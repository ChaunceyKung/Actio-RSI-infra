from actio.evidence.bundles.terminal import terminal_body
from actio.contracts.json import require
import json
from actio.contracts.json import canonical
VERSION = 1
INPUT_CONTRACT = 'fixture-input.v2'

def records(store, run):
    return [store.run(run), store.rows('SELECT * FROM stream WHERE run=?',(run,)),
            store.rows('SELECT * FROM operation WHERE run=?',(run,)),
            store.rows('SELECT d.* FROM domain_receipt d JOIN operation o ON o.id=d.op WHERE o.run=?',(run,)),
            store.rows('SELECT * FROM world WHERE run=?',(run,)),
            store.rows('SELECT * FROM audit WHERE run=? ORDER BY id',(run,))]

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


def validate_sources(store, run):
    for op in store.rows('SELECT * FROM operation WHERE run=?',(run,)):
        events = store.ports.facts(store).certify(op['id'], json.loads(op['barrier'] or '{}'))
        receipt = store.row('SELECT * FROM domain_receipt WHERE op=?',(op['id'],))
        require(receipt is not None, 'domain receipt missing')
        start = max(e['seq'] for e in events if e['type']=='agent/inbox/spliced' and any(m.get('id')==op['receipt'] for m in e['data'].get('inserted',[])))
        accepted=next(e for e in events if e['seq']==start)
        message=next(m for m in accepted['data']['inserted'] if m.get('id')==op['receipt'])
        task=json.loads(''.join(c.get('text','') for c in message['content'] if c.get('type')=='text'))
        intent=store.rows("SELECT body FROM audit WHERE op=? AND kind='dispatch_intent'",(op['id'],))
        pilot=json.loads(store.run(run)['input']).get('input_contract') in ('scheduling-tokenkey.v2','finite-suite-tokenkey.v1','finite-candidate-loopback.v1','finite-candidate-tokenkey.v1','visible-robustness-tokenkey.v1')
        require(len(intent)==1 and (('op' not in task) if pilot else task.get('op')==op['id']), 'native dispatch binding missing')
        normalized={k:v for k,v in task.items() if k not in ('op','callId')}
        if normalized.get('tool'): normalized['args']={k:v for k,v in normalized['args'].items() if k!='op'}
        require(normalized==json.loads(intent[0]['body']), 'native input differs from dispatch')
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
