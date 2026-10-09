// Narrow send gate around the fixed official pure-text adapter. No serializer/parser replacement.
import { readFileSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { canonical, writer, bytesHash } from './common.mjs'
export const name='actio-chat-budget'
export const inject=['llm','loader']
export async function apply(ctx,config) {
  const log=writer(config.capture,config.limits)
  const original=globalThis.fetch
  let active=null, disposed=false
  const ipc=value=>{
    const p=spawnSync(config.python,['-I','-B','-m','actio.budget',config.ledger],{
      input:JSON.stringify(value),encoding:'utf8',timeout:5000,maxBuffer:65536,windowsHide:true,
      ...(config.helper_env?{env:config.helper_env}:{}),
    })
    if(p.error || p.status!==0) throw new Error('budget IPC failed: '+(p.stdout||p.error||p.stderr))
    const result=JSON.parse(p.stdout)
    if(!result.allowed) throw new Error('budget denied: '+result.reason)
    return result
  }
  globalThis.fetch=async (url,options)=>{
    const a=active
    if(disposed || !a || a.used || String(url)!==config.endpoint+'/chat/completions' || options?.method!=='POST' || typeof options.body!=='string') {
      log({kind:'denied',reason:'out-of-scope fetch'});throw new Error('unbound/duplicate/nonloopback fetch')
    }
    a.used=true
    const request={method:'POST',url:String(url),raw:options.body,prepared:a.prepared}
    const ticket=ipc({command:'reserve',attempt:a.op,request})
    const wireHash=bytesHash(Buffer.from(options.body))
    if(ticket.wire_hash!==wireHash) throw new Error('body changed after reserve')
    ipc({command:'sending',attempt:a.op,wire_hash:wireHash})
    log({kind:'sending',op:a.op,wire_hash:wireHash})
    try {
      const headers=new Headers(options.headers)
      const expected=config.credential_env?process.env[config.credential_env]:'actio-loopback-fake-key'
      if(!expected || headers.get('authorization')!=='Bearer '+expected) throw new Error('unexpected credential')
      headers.set('X-Actio-Attempt',a.op)
      const first=new AbortController()
      const timer=config.first_ms?setTimeout(()=>first.abort('first-response deadline'),config.first_ms):null
      let response
      try {
        response=await original(url,{...options,headers,redirect:'error',
          signal:AbortSignal.any([...(options.signal?[options.signal]:[]),first.signal,AbortSignal.timeout(config.total_ms??3000)])})
      } finally {if(timer) clearTimeout(timer)}
      a.response.status=response.status
      // The official Response is returned unchanged. A bounded tee only retains audit bytes.
      a.capture=(async()=>{
        const reader=response.clone().body.getReader();let size=0;const chunks=[]
        try {
          while(true) {
            const {value,done}=await reader.read();if(done) break
            size+=value.byteLength;if(size>65536) {await reader.cancel();throw new Error('response byte limit')}
            chunks.push(Buffer.from(value))
          }
          a.response.raw=Buffer.concat(chunks).toString('utf8')
        } catch(e) {a.response.raw=Buffer.concat(chunks).toString('utf8');a.response.error=String(e)}
        finally {reader.releaseLock()}
      })()
      return response
    } catch(e) {a.response.error=String(e);throw e}
  }
  ctx.on('llm/stream',async function* (request,next) {
    if(active || disposed) throw new Error('overlapping model hook denied')
    const binding=JSON.parse(readFileSync(config.active,'utf8'))
    const a={op:binding.op,used:false,capture:null,
      prepared:{provider:request.provider,model:request.model,purpose:request.purpose??null,messages:request.messages,tools:request.tools??[]},
      response:{status:0,raw:'',chunks:[],error:null}}
    if(!a.op || a.op==='not-dispatched') throw new Error('no active operation')
    active=a;log({kind:'hook',op:a.op})
    try {
      for await(const chunk of next()) {
        if(a.response.chunks.length>=128) throw new Error('stream event limit')
        // DSH cancels its fetch signal when the consumer receives finish. Drain the
        // bounded audit tee first so that normal consumer disposal is not an audit failure.
        if(chunk.type==='finish' && a.capture) await a.capture
        a.response.chunks.push(chunk);yield chunk
      }
    } catch(e) {a.response.error=String(e);throw e}
    finally {
      if(a.capture) await a.capture
      writeFileSync(config.response,JSON.stringify(a.response))
      log({kind:'observed-terminal',op:a.op,response:a.response})
      active=null
    }
  })
  ctx.on('dispose',()=>{disposed=true;globalThis.fetch=original})
  log({kind:'profile',entries:[...ctx.loader.entries()].map(e=>({id:e.options.id,name:e.options.name,disabled:e.disabled}))})
}
