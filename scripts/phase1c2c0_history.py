"""Pinned historical reader + append-only corrected strata; no artifact-selected code."""
import datetime
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile
from actio.common import canonical,file_hash,clean_env
from actio.suite_measurement import correct_c2b2
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c0'
PIN='e89d8b370c6cc53de21f651b49e7b2626eb1a559'

def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    dest=ROOT/'.local/phase1c2c0-history'/stamp;dest.mkdir(parents=True)
    raw=subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.eol=lf','archive','--format=zip',PIN,'src'],cwd=ROOT)
    (dest/'fixed-source.zip').write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.endswith('/'):continue
            assert n.startswith('src/') and '..' not in Path(n).parts
            p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    sys.path.insert(0,str(ROOT/'tests'));from test_suite import GUARD
    runner=dest/'reader.py'
    runner.write_text("import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))\n"+GUARD+"\nfrom actio.pilot_measurement import verify\nf=pathlib.Path(sys.argv[1]);r=verify(json.loads((f/'samples/pilot.json').read_bytes()));assert r['valid'],r\nassert r['report']==json.loads((f/'samples/report.json').read_bytes())\nprint(json.dumps(r['report']['counts']))\n",encoding='utf8')
    argv=[sys.executable,'-X','utf8','-I','-S','-B',str(runner),str(ROOT/'docs/validation/phase1c2b2')]
    result=subprocess.run(argv,cwd=dest,env=clean_env(dest),capture_output=True,text=True,encoding='utf8',timeout=60)
    assert result.returncode==0,result.stderr
    old=ROOT/'docs/validation/phase1c2b2';pre=json.loads((old/'preregistration.json').read_bytes());report=json.loads((old/'samples/report.json').read_bytes())
    correction=correct_c2b2(pre,report)
    sidecar={'schema':'c2b2-strata-correction.v1','metric_version':'finite-independent-measurement.v1',
        'fixed_old_reader_commit':PIN,'fixed_old_reader_archive_sha256':file_hash(dest/'fixed-source.zip'),
        'new_reader_sha256':file_hash(ROOT/'src/actio/suite_measurement.py'),
        'source_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (old/'preregistration.json',old/'evidence_manifest.json',old/'samples/pilot.json',old/'samples/report.json')},
        'old_reader_exact_report_recomputed':True,'old_counts':json.loads(result.stdout),'corrected_strata':correction,
        'scope':'episode joint strata only; all planned units grouped by frozen feasibility; no changes to actions, usage, old report or unknown claims',
        'human_labels':0,'historical_writes':0,'model_requests':0,'actual_argv':argv}
    (DOC/'c2b2-correction.json').write_text(canonical(sidecar),encoding='utf8')
    print(canonical({'old_reader_pass':True,'corrected_strata':correction}))

if __name__=='__main__':main()
