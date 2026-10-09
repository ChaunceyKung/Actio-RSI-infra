// Observability-only official llm/stream middleware. No replacement adapter.
import { appendFileSync } from 'node:fs'
export const name = 'actio-official-probe'
export const inject = ['llm','loader']
export async function apply(ctx,config) {
  const log = row => appendFileSync(config.capture,JSON.stringify(row)+'\n')
  const originalFetch=globalThis.fetch
  let sends=0
  globalThis.fetch=(url,options)=>{
    if (![config.endpoint+'/v1/chat/completions'].includes(String(url)) || ++sends>1) {
      log({kind:'egress-denied',url:String(url)});throw new Error('probe only permits one exact loopback request')
    }
    return originalFetch(url,{...options,redirect:'error'})
  }
  log({kind:'loader-provider',entries:[...ctx.loader.entries()].filter(e=>e.options.id?.includes('deepseek')).map(e=>({id:e.options.id,name:e.options.name,disabled:e.disabled}))})
  ctx.on('llm/stream',async function* (request,next) {
    log({kind:'llm-request',provider:request.provider,model:request.model,purpose:request.purpose??null,messages:request.messages,tools:request.tools??[]})
    for await (const chunk of next()) { log({kind:'chunk',chunk});yield chunk }
  })
  log({kind:'probe-loaded',runtime:process.version})
}
