// EXPERIMENTAL: replaces only model output and adds a frozen-policy guard.
// DSH owns the actual loop, tool dispatch and native journal.
import { appendFileSync, readFileSync, openSync, fsyncSync, closeSync } from 'node:fs'
import { createHash } from 'node:crypto'

export const name = 'actio-phase1a-fixture'
export const inject = ['llm', 'tools', 'sessionPersistence']
function canonical(v) {
  if (Array.isArray(v)) return '[' + v.map(canonical).join(',') + ']'
  if (v && typeof v === 'object') return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonical(v[k])).join(',') + '}'
  return JSON.stringify(v)
}
const hash = v => createHash('sha256').update(canonical(v)).digest('hex')
function freeze(v) { if (v && typeof v === 'object') { Object.values(v).forEach(freeze); Object.freeze(v) }; return v }

export async function apply(ctx, config) {
  const log = row => { appendFileSync(config.trace, JSON.stringify(row) + '\n'); const fd = openSync(config.trace, 'r+'); fsyncSync(fd); closeSync(fd) }
  const policy = freeze(JSON.parse(readFileSync(config.policy, 'utf8')))
  const policyHash = hash(policy)
  const toolVersion = createHash('sha256').update(readFileSync(config.mcpServer)).digest('hex')
  const used = new Set()
  const seqs = new Map()
  const modelCalls = new Map()
  log({ kind: 'startup', pid: process.pid, node: process.version, policyHash, guardAvailable: typeof ctx.tools.guard === 'function' })
  if (config.initHang) await new Promise(() => {})
  ctx.on('session/event', (session, event) => {
    seqs.set(String(session.id), event.seq)
    log({ kind: 'native-observed', session: String(session.id), event })
  })
  ctx.on('agent/status', async ({ agent, status }) => {
    if (status !== 'idle') return
    const session = String(agent.session.id)
    const through = seqs.get(session)
    try {
      await ctx.sessionPersistence.flush()
      log({ kind: 'native-barrier', session, through, seam: 'sessionPersistence.flush' })
    } catch (e) { log({ kind: 'barrier-error', error: String(e) }) }
  })
  ctx.on('tools/pre-execute', async (exec, next) => {
    const grant = policy.grants[exec.callId]
    log({ kind: 'pre-execute', callId: exec.callId, session: String(exec.agent?.session.id), argsHash: hash(exec.arguments) })
    // Deliberate test-only rewrite AFTER the initial frozen decision.
    if (grant?.fault === 'rewrite') {
      try { exec.arguments = { ...exec.arguments, key: 'changed' }; log({ kind: 'rewritten', callId: exec.callId }) }
      catch (e) { log({ kind: 'rewrite-rejected', callId: exec.callId, error: String(e) }); return { kind: 'deny', reason: 'mutation rejected' } }
    }
    // The tested wheel does not support the newer source's semantic cancel
    // decision. Fail closed using its verified deny branch instead.
    if (grant?.fault === 'cancel') return { kind: 'deny', reason: 'cancel requested before dispatch; semantic cancel unsupported' }
    if (grant?.fault === 'dynamic') return { kind: 'deny', reason: 'dynamic approval unsupported' }
    if (grant?.fault === 'approval-timeout') return { kind: 'deny', reason: 'fixture approval deadline expired' }
    if (grant?.fault === 'approval-disconnect') return { kind: 'deny', reason: 'fixture approval channel unavailable' }
    return next()
  })
  ctx.tools.guard(exec => {
    const grant = policy.grants[exec.callId]
    const args = exec.arguments
    const final = { name: exec.name, arguments: args }
    const schema = ctx.tools.schemas(exec.agent).find(s => s.name === exec.name)
    let reason
    if (!grant) reason = 'missing approval'
    else if (grant.requestHash !== hash(final)) reason = 'final request hash mismatch'
    else if (grant.policyHash !== hash(policy.binding)) reason = 'policy hash mismatch'
    else if (grant.run !== policy.binding.run || grant.scope !== String(exec.agent?.session.id)) reason = 'run/scope mismatch'
    else if (grant.lease !== policy.binding.lease || grant.expires <= Date.now()) reason = 'lease/expiry invalid'
    else if (grant.toolVersion !== policy.binding.toolVersion || policy.binding.toolVersion !== toolVersion || !schema || exec.name !== policy.binding.tool) reason = 'tool/version mismatch'
    else if (!args || typeof args !== 'object' || typeof args.key !== 'string' || typeof args.op !== 'string' || Object.keys(args).sort().join(',') !== 'key,op') reason = 'final schema invalid'
    else if (!policy.binding.keys.includes(args.key)) reason = 'final scope invalid'
    else if (used.has(exec.callId) || used.size >= policy.binding.maxCalls) reason = 'budget exhausted'
    else if (grant.deny) reason = 'policy denies'
    log({ kind: 'final-guard', callId: exec.callId, session: String(exec.agent?.session.id), finalHash: hash(final), policyHash, schemaHash: schema ? hash(schema) : null, allowed: !reason, reason: reason ?? null })
    if (!reason) used.add(exec.callId)
    return reason
  })
  ctx.on('tools/result', (exec, result) => log({ kind: 'tool-result', callId: exec.callId, result }))
  // Implement the public adapter interface structurally: external .mjs cannot
  // import arbitrary packages from inside the single-file executable.
  class Fixture {
    providerInfo(provider) { return { id: provider, name: provider } }
    providerRetryPolicy() { return undefined }
    imageRequestPricing() { return undefined }
    async listModels() { return [] }
    async prepareCall(provider, model) { return { model: await this.resolveModel(provider, model), stream: options => this.stream(options) } }
    async resolveModel(provider, model) { return { provider, id: model, name: model, context: { contextWindow: 32000 } } }
    async *stream(options) {
      const prompt = options.messages.findLast(m => m.role === 'user' && m.source?.kind === 'user')
      const task = JSON.parse(prompt.content.filter(b => b.type === 'text').map(b => b.text).join(''))
      const count = (modelCalls.get(task.op) ?? 0) + 1
      modelCalls.set(task.op, count)
      if (count > 6) throw new Error('fixture model request budget exhausted')
      log({ kind: 'provider-input', op: task.op, messages: options.messages, schemas: ctx.tools.schemas(), tools: options.tools ?? [] })
      if (task.kind === 'hang') await new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('fixture aborted')), { once: true }))
      if (task.kind === 'exit') process.exit(71)
      const already = options.messages.some(m => m.source?.kind === 'tool' && m.source?.callId === task.op + ':call')
      if (task.kind === 'tool' && !already) {
        yield { type: 'block-start', index: 0, blockType: 'tool-call' }
        yield { type: 'block-end', index: 0, block: { type: 'tool-call', id: task.op + ':call', name: task.tool ?? 'mcp__fixture__read_fixture', arguments: JSON.stringify(task.args) } }
        yield { type: 'finish', reason: { kind: 'tool-calls' } }
      } else {
        yield { type: 'block-start', index: 0, blockType: 'text' }
        yield { type: 'block-end', index: 0, block: { type: 'text', text: task.answer ?? 'fixture done' } }
        yield { type: 'finish', reason: { kind: 'stop' } }
      }
    }
  }
  ctx.llm.registerAdapter(['phase1a-fixture'], new Fixture())
}
