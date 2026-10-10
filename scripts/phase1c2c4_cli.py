"""Source-bound actual public CLI acceptance; every failure gets a receipt."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import uuid
from actio.common import canonical,clean_env,digest,file_hash
from actio.pilot_contract import implementation
from actio.robustness import verify
from actio.eval_contract import seal

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c4'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--rehearsal',action='store_true');args=parser.parse_args();root=args.root.resolve()
    scratch=ROOT/'.local/phase1c2c4-cli'/uuid.uuid4().hex;scratch.mkdir(parents=True)
    log={'status':'FAIL','implementation':implementation(),'actual_argv':sys.orig_argv,'commands':[],
         'root':str(root),'kind':'full_rehearsal' if args.rehearsal else 'offline_cli','provider_requests':0,
         'harness_source_sha256':file_hash(Path(__file__))}
    def run(arguments,*,timeout=240,guard=False):
        argv=[sys.executable,'-X','utf8','-I','-B',*arguments]
        record={'argv':argv,'exit_code':None,'guard':guard,'harness_timeout_seconds':timeout}
        log['commands'].append(record)
        process=subprocess.run(argv,cwd=scratch,env=clean_env(scratch),capture_output=True,text=True,encoding='utf8',timeout=timeout)
        record.update(exit_code=process.returncode,stdout_hash=digest(process.stdout),stderr=process.stderr)
        assert process.returncode==0,record
        result=json.loads(process.stdout)
        record['summary']=result.get('report',{}).get('counts') or result.get('counts') or result.get('preregistration',{}).get('sha256') or result.get('lineage',{}).get('sha256')
        assert result.get('valid') is not False,result
        return result
    try:
        if args.rehearsal:
            result=run(['-m','actio.robustness','execute','--rehearsal','--project',str(ROOT),'--root',str(root),
                        '--source-database','D:/actio-c2c2-live-v1/candidates.sqlite'],timeout=None)
            assert result['counts']['sent']==result['counts']['admitted']==128
            assert result['counts']['execution_resolved_episodes']==64
            assert result['lineage']['evaluations']==3 and result['lineage']['evaluation_decisions']==2
            log['rehearsal_counts']=result['counts']
        commands=[['plan'],['preflight'],['analyze',str(root/'matrix/pilot.json')],['verify',str(root/'delivery.json')],['lineage',str(root/'candidates.sqlite')]]
        for cmd in commands:run(['-m','actio.robustness',*cmd])
        sys.path.insert(0,str(ROOT/'tests'));from test_suite import GUARD
        guarded=GUARD+"\nfrom actio.robustness import main\nsys.argv=['actio-robustness',*sys.argv[1:]]\nraise SystemExit(main())"
        for cmd in commands:run(['-c',guarded,*cmd],guard=True)
        value=json.loads((root/'delivery.json').read_bytes());rejections=[]
        for case in ('missing_arm','wrong_world','old_decision','new_decision','wrong_candidate','wire_mismatch'):
            b=copy.deepcopy(value['body'])
            if case in ('missing_arm','wrong_world','wire_mismatch'):
                campaign=b['campaign']['body']
                if case=='missing_arm':campaign['entries'].pop()
                elif case=='wrong_world':campaign['entries'][0]['unit']['world']='foreign'
                else:campaign['entries'][0]['evidence']['ledger']['attempts'][0]['request']['raw']='{}'
                b['campaign']=seal(campaign)
            else:
                line=b['lineage']['body'];table=line['tables']
                if case in ('old_decision','new_decision'):
                    row=table['evaluation_decision'][0 if case=='old_decision' else -1];d=json.loads(row['body']);d['state']='reject' if d['state']!='reject' else 'insufficient_evidence';row['body']=canonical(d)
                    event=next(r for r in table['evaluation_event'] if r['evaluation']==row['evaluation'] and r['state']=='decided');event['body']=canonical({'decision_hash':digest(d)})
                else:table['evaluation_binding'][-1]['candidate']='0'*64
                b['lineage']=seal(line)
            result=verify(seal(b));assert not result['valid'],case
            rejections.append({'case':case,'error':result['error']})
        log.update(status='PASS',tamper_rejections=rejections,source_install_equal=
                   all(file_hash(ROOT/'src/actio'/name)==h for name,h in implementation().items()))
        assert log['source_install_equal']
    except BaseException as error:
        log['error']=type(error).__name__+': '+str(error)[:2048]
        raise
    finally:
        dest=DOC/'evidence'/('cli-'+uuid.uuid4().hex[:12]+'.json');dest.parent.mkdir(exist_ok=True)
        with dest.open('x',encoding='utf8') as f:f.write(canonical(log))
        print(canonical({'status':log['status'],'receipt':str(dest),'commands':len(log['commands']),'root':str(root)}))


if __name__=='__main__':main()
