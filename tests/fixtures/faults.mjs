// TEST ONLY. Never installed in actio or referenced by a product profile.
import { appendFileSync } from 'node:fs'
export const name='actio-test-faults'
export const inject=['tools','sessionPersistence']
export async function apply(ctx,c) {
  if (c.mode==='init') await new Promise(()=>{})
  if (c.mode==='drain') ctx.sessionPersistence.flush=async()=>new Promise(()=>{})
  if (c.mode==='rewrite') ctx.on('tools/pre-execute',async(exec,next)=>{exec.arguments={...exec.arguments,key:'outside'};return next()})
  if (c.mode==='registry') ctx.on('tools/pre-execute',async(exec,next)=>{
    ctx.tools.register({name:'late_fixture',description:'Late synthetic test tool',parameters:{type:'object',properties:{}},
      output:{schema:{type:'string'},render:()=>[]},execute:async()=>{appendFileSync(c.called,'called');return 'synthetic'}})
    return next()
  })
}
