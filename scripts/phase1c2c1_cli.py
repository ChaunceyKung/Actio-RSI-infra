"""Actual public commands and guarded portable delivery verification."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import uuid
from actio.common import canonical,clean_env,file_hash,digest
from actio.pilot_contract import implementation
from actio.candidate import verify
from actio.eval_contract import seal
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c1'


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve()
    value=json.loads((root/'delivery.json').read_bytes());assert verify(value)['valid']
    scratch=ROOT/'.local/phase1c2c1-cli'/uuid.uuid4().hex;scratch.mkdir(parents=True)
    records=[]
    commands=[['-m','pip','--isolated','check'],['-m','actio.candidate','plan'],['-m','actio.candidate','preflight'],
              ['-m','actio.candidate','verify',str(root/'delivery.json')],['-m','actio.candidate','lineage',str(root/'candidates.sqlite')]]
    for args in commands:
        cmd=[sys.executable,'-X','utf8','-I','-B',*args]
        result=subprocess.run(cmd,cwd=scratch,env=clean_env(scratch),capture_output=True,text=True,encoding='utf8',timeout=60)
        assert result.returncode==0,result.stderr
        body=json.loads(result.stdout) if 'actio.candidate' in args else {'pip_check':result.stdout.strip()}
        if 'actio.candidate' in args:assert body['credential_reads']==body['network_requests']==body['workers_started']==0
        records.append({'argv':cmd,'exit_code':result.returncode,'stdout_hash':digest(result.stdout),
            'summary':body.get('lineage',{}).get('sha256') or body.get('report',{}).get('counts') or body.get('preregistration',{}).get('sha256') or body,'stderr':result.stderr})
    exe=Path(sys.executable).with_name('actio-candidate.exe');cmd=[str(exe),'preflight']
    result=subprocess.run(cmd,cwd=scratch,env=clean_env(scratch),capture_output=True,text=True,encoding='utf8',timeout=60)
    assert result.returncode==0 and json.loads(result.stdout)['network_requests']==0
    records.append({'argv':cmd,'exit_code':0,'stdout_hash':digest(result.stdout)})
    sys.path.insert(0,str(ROOT/'tests'));from test_suite import GUARD
    code=GUARD+"\nfrom actio.candidate import verify\nr=verify(json.load(open(sys.argv[1],encoding='utf8')));assert r['valid'],r;print(json.dumps({'counts':r['report']['counts'],'lineage':r['lineage']}))"
    cmd=[sys.executable,'-X','utf8','-I','-B','-c',code,str(root/'delivery.json')]
    result=subprocess.run(cmd,cwd=scratch,env=clean_env(scratch),capture_output=True,text=True,encoding='utf8',timeout=60)
    assert result.returncode==0,result.stderr
    tamper=[]
    for case in ('lineage-decision','lineage-parent','campaign-binding','missing-arm'):
        b=copy.deepcopy(value['body']);lineage=b['lineage']['body']
        if case=='lineage-decision':
            row=lineage['tables']['decision'][0];d=json.loads(row['body']);d['eligible_for_activation']=True;row['body']=canonical(d);row['decision_hash']=digest(d)
        if case=='lineage-parent':lineage['tables']['lineage_edge'][0]['parent']='0'*64
        if case=='campaign-binding':
            row=lineage['tables']['campaign_binding'][0];d=json.loads(row['body']);d['plan']['body']['units'].pop();row['body']=canonical(d);row['plan_hash']=digest(d)
        if case=='missing-arm':b['campaign']['body']['entries'].pop();b['campaign']=seal(b['campaign']['body'])
        b['lineage']=seal(lineage);r=verify(seal(b));assert not r['valid'];tamper.append({'case':case,'result':r})
    import actio
    assert {n:file_hash(Path(actio.__file__).parent/n) for n in implementation()}==implementation()
    log={'status':'PASS','commands':records,'guard_argv':cmd,'guard_result':json.loads(result.stdout),'tamper_rejections':tamper,
         'implementation':implementation(),'source_install_equal':True,'external_provider_requests':0}
    with (DOC/'evidence'/('cli-'+uuid.uuid4().hex[:12]+'.json')).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(log))
    print(canonical({'status':'PASS','actual_commands':len(records),'guarded_delivery':True,'tamper_rejections':len(tamper)}))


if __name__=='__main__':main()
