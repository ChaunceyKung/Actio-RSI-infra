"""Experimental REAL_RUNTIME_FIXTURE_PROVIDER cases; runs only under supervisor."""
import json
import os
import sys
import threading
import time
from pathlib import Path
from common import jsonl, write_json, file_hash
from runtime_adapter import Adapter, make_policy, TOOL
from event_probe import Collector

def lifecycle(root):
    tests=[]
    a=Adapter(root/'中文 home A',persona='PRIVATE_A')
    b=Adapter(root/'中文 home B',persona='PRIVATE_B')
    try:
        r=a.run({'op':'a1','answer':'first','private':'A_SECRET'},'same')
        assert r.final_response=='first' and r.events
        barrier=a.barrier('same')
        r=a.run({'op':'a2','answer':'second'},'same'); a.barrier('same')
        a.run({'op':'a-other','answer':'other'},'other'); a.barrier('other')
        b.run({'op':'b1','answer':'B','private':'B_SECRET'},'same'); b.barrier('same')
        inputs_a=[r for r in jsonl(a.trace) if r['kind']=='provider-input']
        inputs_b=[r for r in jsonl(b.trace) if r['kind']=='provider-input']
        assert 'A_SECRET' in json.dumps(inputs_a[1])
        assert 'A_SECRET' not in json.dumps(inputs_a[2])
        assert 'B_SECRET' not in json.dumps(inputs_a)
        assert 'A_SECRET' not in json.dumps(inputs_b) and 'PRIVATE_A' not in json.dumps(inputs_b)
        assert 'PRIVATE_B' not in json.dumps(inputs_a)
        assert all([s['name'] for s in r['schemas']]==[TOOL] for r in inputs_a+inputs_b)
        tests += [{'test_id':'P1-lifecycle','status':'PASS','assertions':['cold handshake, native events, same-session multi-turn, distinct sessions, two concurrent homes, Chinese/space paths','provider inputs prove cross-home and cross-session marker isolation','only read-only fixture tool enumerated'],'barrier':barrier}]
        tests += [{'test_id':'P1-shared-context','status':'PASS','assertions':['same session retains A_SECRET; other session excludes it']}]
    finally: a.close(); b.close()
    before={str(p.relative_to(a.root)):file_hash(p) for p in (a.root/'home/sessions').rglob('*.jsonl')}
    restarted=Adapter(a.root,persona='PRIVATE_A')
    try:
        try:
            result=restarted.run({'op':'restart','answer':'restart'},'same',deadline=5)
            behavior={'outcome':'returned','answer':result.final_response}
        except Exception as e: behavior={'outcome':'rejected','error':str(e)}
    finally: restarted.close()
    after={str(p.relative_to(a.root)):file_hash(p) for p in (a.root/'home/sessions').rglob('*.jsonl')}
    tests.append({'test_id':'P1-restart','status':'PASS' if behavior['outcome']=='rejected' and before==after else 'FAIL',
        'behavior':behavior,'unchanged_journals':before==after,'assertions':['reusing persisted session ID is characterized, not assumed to resume']})
    return tests

def tools_case(root):
    variants={
      'allow':{},'deny':{'deny':True},'rewrite':{'fault':'rewrite'},'expired':{'expires':0},
      'policy':{'policyHash':'wrong'},'lease':{'lease':'wrong'},'scope':{'scope':'wrong'},'run':{'run':'wrong'},
      'version':{'toolVersion':'wrong'},'dynamic':{'fault':'dynamic'},
      'approval-timeout':{'fault':'approval-timeout'},'approval-disconnect':{'fault':'approval-disconnect'},
      'cancel':{'fault':'cancel'}}
    grants=[{'op':op,'override':override} for op,override in variants.items()]
    tests=[]
    with Adapter(root,policy=make_policy(grants)) as adapter:
        for op in [*variants,'missing','shell']:
            task={'op':op,'kind':'tool','args':{'key':'ok','op':op}}
            if op=='shell': task['tool']='pwsh'
            r=adapter.run(task); adapter.barrier('assistant')
            assert r.final_response=='fixture done'
            calls=[e for e in jsonl(root/'mcp.jsonl') if e['kind']=='received' and e['arguments']['op']==op]
            expected=1 if op=='allow' else 0
            assert len(calls)==expected,(op,calls)
            tests.append({'test_id':'P2-'+op,'status':'PASS','calls':len(calls),
                'assertions':['actual worker MCP dispatch count matches expected; Python does not execute tool'],
                'limits':['static-policy fixture denial; no dynamic approval RPC exercised'] if op in ['dynamic','approval-timeout','approval-disconnect'] else []})
        trace=jsonl(adapter.trace)
        assert any(r['kind']=='rewritten' and r['callId']=='rewrite:call' for r in trace)
        assert any(r['kind']=='final-guard' and r['callId']=='rewrite:call' and not r['allowed'] for r in trace)
        assert all([s['name'] for s in r['schemas']]==[TOOL] for r in trace if r['kind']=='provider-input')
    return tests

def tool_result(root,key):
    op='result-'+key
    policy=make_policy([{'op':op,'args':{'key':key,'op':op}}])
    with Adapter(root,policy=policy) as adapter:
        adapter.run({'op':op,'kind':'tool','args':{'key':key,'op':op}})
        adapter.barrier('assistant')
        results=[r for r in jsonl(adapter.trace) if r['kind']=='tool-result']
        calls=[r for r in jsonl(root/'mcp.jsonl') if r['kind']=='received']
        assert len(calls)==1 and len(results)==1,(calls,results)
        assert results[0]['result']['isError'] is True,results
    return [{'test_id':'P2-result-'+key,'status':'PASS','calls':1,'tool_result':results[0],
             'mcp_tail':jsonl(root/'mcp.jsonl')[-2:],'limits':['DSH result may normalize transport/timeout into isError; classification retains scenario cause']}]

def failure(root,kind):
    init=kind=='init-timeout'
    adapter=Adapter(root,mcp=not init,init_hang=init,initialize_timeout=.7 if init else 20)
    start=time.monotonic()
    try:
        try:
            if init: adapter.start()
            elif kind=='eof':
                adapter.start()
                adapter.harness.client._proc.stdin.close() # Real pipe EOF fault injection.
                adapter.run({'op':'eof','answer':'never'},deadline=3)
            elif kind=='tool-interruption':
                # Separate setup is required to freeze a grant before dispatch.
                raise AssertionError('use tool_interruption')
            else: adapter.run({'op':kind,'kind':'exit' if kind=='exit' else 'hang'},deadline=1)
        except Exception as e:
            error={'type':type(e).__name__,'message':str(e)}
        else: raise AssertionError('failure was incorrectly reported success')
    finally: adapter.close()
    elapsed=time.monotonic()-start
    assert elapsed<12,(kind,elapsed)
    return [{'test_id':'P1-'+kind,'status':'PASS','elapsed_seconds':elapsed,'error':error,
        'operation_state':'unknown/needs_reconcile','automatic_retries':0,
        'limits':['forced termination is not semantic cancellation or recovery']}]

def tool_interruption(root):
    op='interrupted'
    adapter=Adapter(root,policy=make_policy([{'op':op,'args':{'key':'hold','op':op}}]))
    triggered=threading.Event()
    def kill_on_received():
        until=time.monotonic()+15
        while time.monotonic()<until:
            if any(e['kind']=='received' for e in jsonl(root/'mcp.jsonl')):
                adapter.harness.client._proc.kill()
                triggered.set(); return
            time.sleep(.01)
    watcher=threading.Thread(target=kill_on_received,daemon=True)
    try:
        adapter.start(); watcher.start()
        try: adapter.run({'op':op,'kind':'tool','args':{'key':'hold','op':op}})
        except Exception as e: error=str(e)
        else: raise AssertionError('interrupted request reported success')
    finally: adapter.close(); watcher.join(1)
    assert triggered.is_set()
    trace=jsonl(adapter.trace)
    assert not any(r['kind']=='tool-result' for r in trace)
    calls=[e for e in jsonl(root/'mcp.jsonl') if e['kind']=='received']
    assert len(calls)==1
    return [{'test_id':'P3-tool-interruption','status':'PASS','trigger':'fsynced MCP received record, before native tool-result/collector confirmation',
        'calls':len(calls),'error':error,'operation_state':'unknown/needs_reconcile','automatic_retries':0}]

def isolation(root):
    grant={'op':'same-op'}
    a=Adapter(root/'A',policy=make_policy([grant]))
    b=Adapter(root/'B',policy=make_policy([{**grant,'override':{'deny':True}}]))
    try:
        a.start();b.start()
        for adapter in [a,b]:
            adapter.run({'op':'same-op','kind':'tool','args':{'key':'ok','op':'same-op'}})
            adapter.barrier('assistant')
        counts=[sum(r['kind']=='received' for r in jsonl(x.root/'mcp.jsonl')) for x in [a,b]]
        assert counts==[1,0],counts
        assert a.pid!=b.pid
    finally:a.close();b.close()
    with Adapter(root/'no-mcp',mcp=False) as c:
        c.run({'op':'no-mcp','answer':'none'})
        assert all(r['schemas']==[] for r in jsonl(c.trace) if r['kind']=='provider-input')
    return [{'test_id':'P2-policy-isolation','status':'PASS','counts':counts,
        'assertions':['same session/op in two concurrent homes obey separate policies','profile without MCP enumerates zero tools']}]

def constraints(root):
    tests=[]
    for label,args,limit in [('schema',{'key':3,'op':'schema'},2),('key-scope',{'key':'outside','op':'key-scope'},2),('budget',{'key':'ok','op':'budget'},0)]:
        with Adapter(root/label,policy=make_policy([{'op':label,'args':args}],max_calls=limit)) as adapter:
            adapter.run({'op':label,'kind':'tool','args':args});adapter.barrier('assistant')
            assert not any(r['kind']=='received' for r in jsonl(adapter.root/'mcp.jsonl'))
            guard=next(r for r in jsonl(adapter.trace) if r['kind']=='final-guard')
            assert not guard['allowed']
            tests.append({'test_id':'P2-final-'+label,'status':'PASS','guard':guard,'calls':0})
    return tests

def event_integration(root):
    """Actual native journal → small SQLite collector; exact failure boundaries."""
    adapter=Adapter(root/'native')
    try:
        result=adapter.run({'op':'native-to-canonical','answer':'observed'})
        barrier=adapter.barrier('assistant')
        files=list((adapter.root/'home/sessions').rglob('*.jsonl'))
        assert len(files)==1,files
        log=jsonl(files[0]);header=log[0];events=log[1:]
        assert header['type']=='session'
        assert [e['seq'] for e in events]==list(range(len(events)))
        assert barrier['through']<=events[-1]['seq']
        by_seq={e['seq']:e for e in events}
        assert all(e==by_seq[e['seq']] for e in result.events)
    finally:adapter.close()
    # In a product, allocation ledger UUID supplies stable store/creation IDs.
    stream='dsh:fixture-store:native-session-creation-1:assistant'
    c=Collector(root/'collector.sqlite')
    try:c.ingest(stream,events[0]['seq'],events[0],crash_before_commit=True)
    except RuntimeError:pass
    c.db.close();c=Collector(root/'collector.sqlite')
    assert c.cursor(stream)==-1
    for e in reversed(events):c.ingest(stream,e['seq'],e)
    assert c.cursor(stream)==events[-1]['seq']
    n=c.consume('effect-ledger','v1')
    c.db.close();c=Collector(root/'collector.sqlite')
    for e in events:c.ingest(stream,e['seq'],e,'v2')
    assert c.consume('effect-ledger','v2')==n
    c.db.close()
    return [{'test_id':'P3-native-collector','status':'PASS','header':header,'physical_generation':files[0].name,
      'event_count':len(events),'barrier':barrier,'cursor':events[-1]['seq'],'business_effect_slots':n,
      'assertions':['SDK observed records equal persisted journal by seq after explicit flush','real native seq0 transaction rolled back before commit','reopen after commit with ack lost preserves count','same journal projected v2 creates no new business occurrence'],
      'limits':['process-local flush marker, not SDK durable watermark RPC','SQLite effects only; not remote exactly-once or power-loss test']}]

def receipt_loss(root):
    """Accepted response lost before application receipt commit, not wire loss."""
    import sqlite3
    dbpath=root/'receipt.sqlite'
    db=sqlite3.connect(dbpath)
    db.execute('CREATE TABLE operation(id TEXT PRIMARY KEY,state TEXT)')
    db.execute("INSERT INTO operation VALUES('accepted-lost','constructed')");db.commit()
    adapter=Adapter(root/'native')
    try:
        adapter.start()
        message_id=adapter.harness.client.session_prompt('assistant',[{'type':'text','text':json.dumps({'op':'accepted-lost','kind':'hang'})}])
        until=time.monotonic()+3
        while time.monotonic()<until and not any(r['kind']=='provider-input' for r in jsonl(adapter.trace)):time.sleep(.01)
        assert any(r['kind']=='provider-input' for r in jsonl(adapter.trace))
        # Drop the app receipt transaction, terminate the worker, reopen the ledger.
        adapter.harness.client._proc.kill()
    finally:adapter.close();db.close()
    db=sqlite3.connect(dbpath)
    assert db.execute('SELECT state FROM operation').fetchone()[0]=='constructed'
    db.execute("UPDATE operation SET state='unknown/needs_reconcile'");db.commit();db.close()
    observed=[r for r in jsonl(adapter.trace) if r['kind']=='native-observed']
    assert any(message_id in json.dumps(r) for r in observed)
    return [{'test_id':'P3-accepted-receipt-loss','status':'PASS','messageId':message_id,
        'trigger':'SDK returned accepted ID and provider-input observed; application receipt deliberately not committed before real worker kill',
        'operation_state':'unknown/needs_reconcile','automatic_retries':0,
        'limits':['application persistence fault; loss of bytes before SDK response decoding NOT_RUN','no turn completion claimed']}]

CASES={'lifecycle':lifecycle,'tools':tools_case,'iserror':lambda p:tool_result(p,'error'),
       'transport':lambda p:tool_result(p,'transport'),'timeout':lambda p:tool_result(p,'timeout'),
       **{k:(lambda p,k=k:failure(p,k)) for k in ['init-timeout','run-timeout','eof','exit']},
       'tool-interruption':tool_interruption,'policy-isolation':isolation,'constraints':constraints,
       'event-integration':event_integration,'receipt-loss':receipt_loss}

if __name__=='__main__':
    # Supervisor attaches the Windows Job before permitting any descendants.
    assert sys.stdin.readline().strip()=='go'
    name,root=sys.argv[1],Path(sys.argv[2]).resolve()
    root.mkdir(parents=True,exist_ok=True)
    try:
        rows=CASES[name](root)
        write_json(root/'result.json',{'case':name,'tests':rows})
        assert all(r['status']=='PASS' for r in rows),rows
    except BaseException as e:
        write_json(root/'failure.json',{'type':type(e).__name__,'error':str(e)})
        raise
