// TEST ONLY fault/script provider. Real DSH agent loop remains in use.
import {appendFileSync} from 'node:fs'
export const name='actio-test-provider'
export const inject=['llm']
export function apply(ctx,c) {
  const calls=new Map()
  class Fixture {
    providerInfo(p){return {id:p,name:p}}
    providerRetryPolicy(){return undefined}
    imageRequestPricing(){return undefined}
    async listModels(){return []}
    async resolveModel(p,m){return {provider:p,id:m,name:m,context:{contextWindow:32000}}}
    async prepareCall(p,m){return {model:await this.resolveModel(p,m),stream:o=>this.stream(o)}}
    async *stream(options){
      const m=options.messages.findLast(m=>m.source?.kind==='user')
      const task=JSON.parse(m.content.filter(b=>b.type==='text').map(b=>b.text).join(''))
      const n=calls.get(task.op)??0;calls.set(task.op,n+1)
      appendFileSync(c.log,JSON.stringify({kind:'provider-entered',op:task.op,n})+'\n')
      if(c.mode==='run') await new Promise(()=>{})
      if(c.mode==='exit') process.exit(71)
      const step=c.script?.[n]
      if(step){
        yield {type:'block-start',index:0,blockType:'tool-call'}
        yield {type:'block-end',index:0,block:{type:'tool-call',id:step.id,name:step.tool??'mcp__fixture__read_fixture',arguments:JSON.stringify({key:step.key??'ok',op:task.op})}}
        yield {type:'finish',reason:{kind:'tool-calls'}}
      }else{
        yield {type:'block-start',index:0,blockType:'text'}
        yield {type:'block-end',index:0,block:{type:'text',text:c.mode==='oversize'?'x'.repeat(70000):'fixture done'}}
        yield {type:'finish',reason:{kind:'stop'}}
      }
    }
  }
  ctx.llm.registerAdapter(['actio-fixture'],new Fixture())
}
