"""Real public runtime CLI smoke, frozen campaign, and offline calibration handoff."""
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from actio.common import canonical,digest,file_hash,clean_env
from actio.eval_contract import seal,make_spec
from actio.evaluation import source_bundle,prepare
from actio.campaign import GROUP_RULE,source_group
from actio.preflight import template

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c1'


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-p1c1-cli')/stamp;root.mkdir(parents=True)
    (root/'owner.json').write_text(canonical({'owner':'phase1c1-public-cli'}),encoding='utf8')
    dest=DOC/'artifacts'/stamp;dest.mkdir(parents=True);env=clean_env(root)
    log={'status':'FAIL','command':' '.join(sys.argv),'root':str(root),'destination':str(dest.relative_to(ROOT)),
         'commands':[],'model_requests':0}
    def command(args,expected=0):
        cmd=[sys.executable,'-X','utf8','-I','-B',*map(str,args)]
        p=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
        log['commands'].append({'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==expected,p.stderr+p.stdout
        return json.loads(p.stdout)
    cli=['-m','actio','--db',str(root/'ledger.sqlite'),'--short-root',str(root)]
    try:
        command([*cli,'init'])
        for a in ('C1_CLI_A','C1_CLI_B'):command([*cli,'agent',a,'--create'])
        sources={};(dest/'samples').mkdir()
        for variant in ('compatible','conflict'):
            card=command([*cli,'task-card','--variant',variant,'--a','C1_CLI_A','--b','C1_CLI_B','--output',dest/'tasks'])
            args=[*cli,'schedule','--key',variant,'--task',card['task']]
            run=command(args);assert run['task']==('success' if variant=='compatible' else 'task_failure')
            assert command(args)['id']==run['id']
            bundle=dest/'samples'/variant;command([*cli,'export',run['id'],'--output',bundle]);command(['-m','actio.verify',bundle])
            sources[variant]=source_bundle(bundle)[0]
            if variant=='compatible':
                dup=dest/'samples/export-duplicate';command([*cli,'export',run['id'],'--output',dup]);sources['export-duplicate']=source_bundle(dup)[0]
        tests=[]
        for p in sorted((DOC/'evidence').glob('20*.json')):
            d=json.loads(p.read_bytes())
            if d.get('suite')=='task' and d['exit_code']==0:tests.append((p,d))
        assert tests,'final successful task suite required'
        path,test=tests[-1];testroot=Path(test['tests'][0]['evidence']['root'])
        log['task_suite']={'file':str(path.relative_to(ROOT)),'sha256':file_hash(path)}
        for name in ('decline','illegal','illegal-second','partial','replay','swap'):
            bundle=dest/'samples'/name;shutil.copytree(testroot/'bundles'/name,bundle);sources[name]=source_bundle(bundle)[0]
        sources['old-social-missing-context']=source_bundle(ROOT/'docs/validation/phase1b1/samples/social')[0]
        # Rehashed current-format counterexample, keeping native raw unchanged.
        bad=json.loads(canonical(sources['compatible']));d=json.loads(bad['files']['evidence.json']);d['world'][1]['resolved']='[event] altered result'
        bad['files']['evidence.json']=canonical(d);bad['files'].pop('verification.json')
        inventory=json.loads(bad['files']['manifest.json']);inventory['files']=[e for e in inventory['files'] if e['path']!='verification.json']
        raw=bad['files']['evidence.json'].encode();import hashlib
        next(e for e in inventory['files'] if e['path']=='evidence.json').update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        bad['files']['manifest.json']=canonical(inventory);sources['rehashed-world-contradiction']=bad
        raw=canonical({'scores':{'agent_2':{'goal':{'reasoning':'Preset structure fixture only.','score':8},'relationship':{'reasoning':'Preset structure fixture only.','score':-2}},
                                  'agent_1':{'goal':{'reasoning':'Preset structure fixture only.','score':3},'relationship':{'reasoning':'Preset structure fixture only.','score':1}}}})
        entries=[];indexed={}
        for name,source in sources.items():
            key=digest(source);indexed[key]=source
            for mode in ('deterministic','controlled_response'):
                identity,*_=prepare(make_spec(mode,'0'*64),source)
                entries.append({'id':name+'-'+mode,'source':key,'mode':mode,'raw_response':raw if mode=='controlled_response' else None,
                                'aliases':identity.get('aliases',{}),'grouping':source_group(source)})
        entries.append({**entries[0],'id':'repeated-evaluation-request'})
        entries.append({**entries[1],'id':'invalid-envelope','raw_response':'{}'})
        alt=json.loads(raw);alt['scores']['agent_1']['goal']['score']=4
        entries.append({**entries[1],'id':'different-controlled-response','raw_response':canonical(alt)})
        dataset=seal({'schema':'task-campaign.v1','group_rule':GROUP_RULE,'sources':indexed,'entries':entries})
        datafile=dest/'dataset-input.json';datafile.write_text(canonical(dataset),encoding='utf8')
        # Windows remains short-path-only. Publish in the owned short root, then
        # verify the unchanged portable copy at the bounded documentation path.
        campaign=command(['-m','actio.campaign','run',datafile,'--output',root/'campaign'])
        shutil.copytree(root/'campaign',DOC/'campaign')
        log['campaign_verification']=command(['-m','actio.campaign','verify-campaign',DOC/'campaign'])
        index=json.loads((DOC/'campaign/campaign.json').read_bytes())['body'];report=json.loads((DOC/'campaign'/index['report']).read_bytes())['body']
        records=[DOC/'campaign/records'/(r['record']+'.json') for r in report['registrations'] if r['id'] in ('compatible-deterministic','conflict-deterministic','decline-deterministic')]
        log['annotations']=command(['-m','actio.calibration','export',*records,'--output',DOC/'annotations'])
        log['empty_import']=command(['-m','actio.calibration','import-labels',DOC/'annotations/internal.json',DOC/'annotations/blank-labels.jsonl','--raters','pending_rater_1','pending_rater_2'],2)
        config=dest/'pilot-config.json';config.write_text(canonical(template()),encoding='utf8');log['preflight']=command(['-m','actio.preflight',config],2)
        log.update(status='PASS',campaign_counts=campaign['counts'],independent_research_units=0)
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)};raise
    finally:
        with (DOC/'evidence'/('artifacts-'+stamp+'.json')).open('x',encoding='utf8') as f:f.write(canonical(log))
    print(canonical({'status':'PASS','artifacts':str(dest),'counts':campaign['counts']}))


if __name__=='__main__':main()
