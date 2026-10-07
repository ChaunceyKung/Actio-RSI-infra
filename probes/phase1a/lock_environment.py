"""Record the resolved, actually downloaded Windows wheel closure; no secrets."""
import email
import json
import platform
import sys
import urllib.request
import zipfile
from common import ROOT, LOCAL, EVIDENCE, file_hash, write_json

def main():
    rows=[]
    for wheel in sorted((LOCAL/'wheels').glob('*.whl')):
        with zipfile.ZipFile(wheel) as z:
            metadata=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
            licenses=[n for n in z.namelist() if any(s in n.lower() for s in ['license','notice','copying'])]
        name, version=metadata['Name'],metadata['Version']
        url=f'https://pypi.org/pypi/{name}/{version}/json'
        d=json.load(urllib.request.urlopen(url,timeout=30))
        entry=next(f for f in d['urls'] if f['filename']==wheel.name)
        sha=file_hash(wheel)
        assert sha==entry['digests']['sha256'],wheel.name
        rows.append({'name':name,'version':version,'filename':wheel.name,'size':wheel.stat().st_size,'sha256':sha,
                     'url':entry['url'],'metadata_url':url,'requires_dist':metadata.get_all('Requires-Dist',[]),
                     'license':metadata['License-Expression'] or metadata['License'],'license_files':licenses})
    (ROOT/'requirements.lock').write_text('# Generated from verified downloaded wheels; Windows x64 / Python 3.12 only.\n'+
        '\n'.join(f"{r['name']}=={r['version']} --hash=sha256:{r['sha256']}" for r in rows)+'\n',encoding='utf-8')
    write_json(EVIDENCE/'artifacts.json',{'platform':platform.platform(),'python':sys.version,'wheels':rows,
         'dsh_source':'5badb15009ae1756c3afe0ae0cef1faafc290ccc','binary_source_mapping':'UNPROVEN',
         'concordia_source':'b71d202750e23444ce1bf28d9f114bcd88aa41db','patch':None})
    print(f'Verified {len(rows)} wheels against PyPI metadata')

if __name__=='__main__': main()
