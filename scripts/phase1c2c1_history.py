"""Hard-coded historical sources only. Sidecars do not re-admit old actions."""
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile
from actio.common import canonical,file_hash,clean_env
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c1'


def main():
    import phase1c2b2_legacy as older
    older.DOC=DOC;older.main()
    sys.path.insert(0,str(ROOT/'tests'));from test_suite import GUARD
    root=ROOT/'.local/phase1c2c1-history'/uuid.uuid4().hex;root.mkdir(parents=True);records=[]
    for phase,pin,module in [('phase1c2b2','e89d8b370c6cc53de21f651b49e7b2626eb1a559','pilot_measurement'),
                             ('phase1c2c0','e2e6691ef9bae5f61bccaaa97528e0478bd9a666','suite_measurement')]:
        folder=root/phase;folder.mkdir();raw=subprocess.check_output(['git','-c','core.autocrlf=false','archive','--format=zip',pin,'src'],cwd=ROOT)
        (folder/'source.zip').write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.endswith('/'):continue
                assert name.startswith('src/') and '..' not in Path(name).parts
                path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
        runner=folder/'reader.py';runner.write_text("import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))\n"+GUARD+
            '\nfrom actio.'+module+" import verify\nf=pathlib.Path(sys.argv[1]);r=verify(json.loads((f/'samples/pilot.json').read_bytes()));assert r['valid'],r\nassert r['report']==json.loads((f/'samples/report.json').read_bytes())\nprint(json.dumps(r['report']['counts']))\n",encoding='utf8')
        args=[sys.executable,'-X','utf8','-I','-S','-B',str(runner),str(ROOT/'docs/validation'/phase)]
        result=subprocess.run(args,capture_output=True,text=True,encoding='utf8',env=clean_env(folder),timeout=60)
        assert result.returncode==0,result.stderr
        records.append({'phase':phase,'reader_commit':pin,'archive_sha256':file_hash(folder/'source.zip'),
            'source_hashes':{p.relative_to(folder).as_posix():file_hash(p) for p in (folder/'src').rglob('*') if p.is_file()},
            'old_report_exact':True,'counts':json.loads(result.stdout),'actual_argv':args})
    out={'status':'PASS','readers':records,'network_requests':0,'workers_started':0,'historical_writes':0}
    with (DOC/'history.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical(out))
    print(canonical({'status':'PASS','exact_report_readers':2}))


if __name__=='__main__':main()
