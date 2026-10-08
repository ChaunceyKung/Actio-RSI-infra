"""Versioned, deterministic scenario receipt checks shared by store and offline reader."""
import json

from .common import ContractError, digest, canonical

VERSION = 1


def require(ok, reason):
    if not ok:
        raise ContractError(reason)


def terminal_body(run, streams, operations, receipts, world, audit, outcome):
    manifest = json.loads(run['input'])
    scenario = manifest.get('scenario')
    require(scenario in ('assistant', 'social'), 'unknown scenario contract')
    require(outcome in ('success', 'task_failure'), 'no scenario terminal for infrastructure/unknown outcome')
    by_stream = {s['id']: s for s in streams}
    by_op = {o['id']: o for o in operations}
    by_receipt = {r['op']: r for r in receipts}
    intents = [a for a in audit if a['kind'] == 'dispatch_intent']
    order = [a['op'] for a in sorted(intents, key=lambda a: a['id'])]
    require(len(order) == len(set(order)) and set(order) == set(by_op), 'operation intent order incomplete')
    require(set(by_receipt) == set(by_op), 'domain receipt missing or unexpected')
    for op in operations:
        require(op['state'] == 'execution_complete', 'operation is not execution complete')
        require(op['run'] == run['id'] and op['epoch'] == run['epoch'], 'operation run/epoch mismatch')
        stream = by_stream.get(op['stream'])
        require(stream and stream['run'] == run['id'], 'operation stream scope mismatch')
        receipt = by_receipt[op['id']]
        require(receipt['stream'] == stream['id'], 'domain receipt stream mismatch')
        require(type(receipt['seq']) is int and receipt['seq'] >= 0, 'invalid domain receipt source')
        marker = json.loads(op['barrier'] or '{}')
        require(receipt['seq'] <= marker.get('through', -1), 'domain receipt outside barrier')
    ordered = [by_op[k] for k in order]
    if scenario == 'assistant':
        require(len(ordered) == 1 and not world, 'assistant single-step contract incomplete')
        op = ordered[0]
        require(by_stream[op['stream']]['agent'] == manifest['request']['agent'], 'assistant identity mismatch')
        receipt = by_receipt[op['id']]
        body = json.loads(receipt['body'])
        require(receipt['outcome'] == outcome and body.get('tool_success') is (outcome == 'success'), 'assistant domain outcome mismatch')
        require(bool(body.get('memory')) == (outcome == 'success'), 'assistant memory effect receipt missing')
        reason, owner = 'single_step_finished', 'assistant.owner.v1'
    else:
        require(manifest.get('order') == ['B', 'A'] and manifest.get('max_steps') == 2 and manifest.get('world') == [], 'unsupported frozen social contract')
        entities = manifest['entities']
        require(set(entities) == {'A','B'} and entities['A'] != entities['B'], 'social entity mismatch')
        expected = ['B','A'] if outcome == 'success' else ['B']
        require(len(ordered) == len(expected), 'social steps incomplete')
        require([by_stream[o['stream']]['agent'] for o in ordered] == [entities[e] for e in expected], 'social entity order mismatch')
        if outcome == 'task_failure':
            op = ordered[0]
            receipt = by_receipt[op['id']]
            require(manifest.get('illegal') is True and not world and receipt['outcome'] == 'task_failure', 'illegal action termination mismatch')
            require(op['answer'] not in manifest['action_spec']['options'], 'rejected action was legal')
            require(json.loads(receipt['body']) == {'rejected':'illegal_action','world_unchanged':True}, 'missing explicit action rejection')
            require(not any(a['kind'] == 'gm_resolve' for a in audit), 'rejected action reached GM resolution')
            reason = 'illegal_action_rejected_before_world'
        else:
            require(len(world) == 2, 'social world incomplete')
            for index, (op, w) in enumerate(zip(ordered, sorted(world,key=lambda w:w['step']))):
                receipt = by_receipt[op['id']]
                body = json.loads(receipt['body'])
                require(w['run'] == run['id'] and w['step'] == index and w['agent'] == entities[expected[index]], 'world scope/order mismatch')
                require((w['stream'],w['seq']) == (receipt['stream'],receipt['seq']), 'world/domain source mismatch')
                require(w['intent'] == op['answer'] and op['answer'] in manifest['action_spec']['options'], 'world illegal or mismatched intent')
                require(receipt['outcome'] == 'success' and body.get('resolved') == w['resolved'] and body.get('producer') == 'GM.observe(EVENT)', 'GM domain receipt mismatch')
                resolutions = [json.loads(a['body']) for a in audit if a['kind']=='gm_resolve' and a['op']==op['id']]
                putative = f"[putative_event] {expected[index]}: {op['answer']}"
                resolved = f'resolved[{index}]: {putative}'
                require(body.get('putative') == putative and resolutions == [{'intent':putative,'resolved':resolved,'source':'GM.act(RESOLVE)'}]
                        and w['resolved'] == '[event] '+resolved, 'GM resolved evidence mismatch')
            reason = 'two_entities_resolved'
        owner = 'concordia.scenario.owner.v1'
    return {'version':VERSION, 'run':run['id'], 'scenario':scenario, 'owner':owner,
            'manifest_hash':run['input_hash'], 'outcome':outcome, 'reason':reason,
            'operations':order, 'domain_hash':digest(sorted(receipts,key=lambda r:r['op'])),
            'world_hash':digest(sorted(world,key=lambda w:w['step']))}


def records(store, run):
    return [store.run(run), store.rows('SELECT * FROM stream WHERE run=?',(run,)),
            store.rows('SELECT * FROM operation WHERE run=?',(run,)),
            store.rows('SELECT d.* FROM domain_receipt d JOIN operation o ON o.id=d.op WHERE o.run=?',(run,)),
            store.rows('SELECT * FROM world WHERE run=?',(run,)),
            store.rows('SELECT * FROM audit WHERE run=? ORDER BY id',(run,))]


def validate_sources(store, run):
    from .facts import Facts
    for op in store.rows('SELECT * FROM operation WHERE run=?',(run,)):
        events = Facts(store).certify(op['id'], json.loads(op['barrier'] or '{}'))
        receipt = store.row('SELECT * FROM domain_receipt WHERE op=?',(op['id'],))
        require(receipt is not None, 'domain receipt missing')
        start = max(e['seq'] for e in events if e['type']=='agent/inbox/spliced' and any(m.get('id')==op['receipt'] for m in e['data'].get('inserted',[])))
        end = json.loads(op['barrier'])['terminal']['seq']
        finals = [e for e in events if e['type']=='assistant/message' and start<e['seq']<end]
        require(finals and receipt['seq'] == finals[-1]['seq'] and receipt['stream']==op['stream'], 'domain source is not final assistant occurrence')
        if json.loads(store.run(run)['input'])['scenario']=='assistant':
            blocks=[b for e in events if start<e['seq']<end and e['type']=='tool/result'
                    for b in e['data'].get('message',{}).get('content',[]) if b.get('type')=='tool-result']
            success=len(blocks)==1 and blocks[0].get('isError') is False and 'SYNTHETIC_SHARED_REFERENCE_17' in json.dumps(blocks[0])
            body=json.loads(receipt['body'])
            require(body.get('tool_success') is success, 'domain tool result mismatch')
            if success:
                ack=body.get('memory',{})
                effect=store.row('SELECT * FROM effect WHERE stream=? AND seq=? AND slot=?',(receipt['stream'],receipt['seq'],'assistant.final'))
                require(effect and ack.get('memory_id')==effect['memory_id'] and ack.get('revision')==effect['revision'], 'domain memory effect mismatch')


def seal_terminal(store, run, epoch, outcome):
    with store.tx():
        store.fence(run,epoch)
        validate_sources(store,run)
        body = terminal_body(*records(store,run),outcome)
        store.db.execute('INSERT INTO scenario_terminal VALUES(?,?,?)',(run,VERSION,canonical(body)))


def check_terminal(store, run, outcome):
    receipt = store.row('SELECT * FROM scenario_terminal WHERE run=?',(run,))
    require(receipt and receipt['version']==VERSION, 'scenario terminal absent or unsupported')
    validate_sources(store,run)
    require(json.loads(receipt['body']) == terminal_body(*records(store,run),outcome), 'scenario terminal does not match current evidence')
