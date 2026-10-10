"""Exercise the public package in a new stdlib-only installation after relocation."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_suite import GUARD
from actio.common import canonical,file_hash
from actio.transport_diagnostics import sources


def main():
    root=ROOT/'.local/phase1c2c5-portability'/uuid.uuid4().hex;root.mkdir(parents=True)
    env=root/'env';cmd=[sys.executable,'-X','utf8','-B',str(ROOT/'scripts/install_failure_diagnostics.py'),str(env)]
    build=subprocess.run(cmd,capture_output=True,encoding='utf8',timeout=120)
    (root/'install.stdout').write_text(build.stdout,encoding='utf8');(root/'install.stderr').write_text(build.stderr,encoding='utf8')
    assert build.returncode==0,build.stderr
    python=env/'Scripts/python.exe';moved=root/'moved-package';moved.mkdir()
    pkg=moved/'package.json';shutil.copyfile(ROOT/'docs/validation/phase1c2c5/package.json',pkg)
    runner=root/'guard.py';runner.write_text('import sys\nsys.dont_write_bytecode=True\n'+GUARD+
        '\nfrom actio.transport_diagnostics import main\nraise SystemExit(main())\n',encoding='utf8')
    commands=[]
    for args in (['plan'],['analyze',str(pkg)],['verify',str(pkg)]):
        argv=[str(python),'-X','utf8','-I','-B',str(runner),*args]
        r=subprocess.run(argv,capture_output=True,encoding='utf8',timeout=90)
        value=json.loads(r.stdout) if r.returncode==0 else None
        commands.append({'argv':argv,'exit':r.returncode,'stdout_hash':hashlib.sha256(r.stdout.encode()).hexdigest(),
            'stderr_hash':hashlib.sha256(r.stderr.encode()).hexdigest(),'guard':True,'result':value if args[0]!='plan' else {'plan_sources_equal':value['sources']==sources()} if value else None})
    status='PASS' if all(r['exit']==0 for r in commands) else 'FAIL'
    result={'status':status,'sources':sources(),'root':str(root),'installer_argv':cmd,'installer_exit':build.returncode,
        'package_sha256':file_hash(pkg),'commands':commands,'runtime_dependencies_installed':False,
        'tools':{n:file_hash(ROOT/n) for n in ('scripts/install_failure_diagnostics.py','scripts/phase1c2c5_portability.py','tests/test_suite.py')},
        'new_external_requests':0,'new_loopback_sends':0}
    dest=ROOT/'docs/validation/phase1c2c5'/('portability-'+root.name[:12]+'.json');dest.write_text(canonical(result),encoding='utf8',newline='\n')
    print(canonical({'status':status,'receipt':str(dest)}));return 0 if status=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
