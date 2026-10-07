"""Bounded official PyPI wheel download with verified ranges and SHA256."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import time
import urllib.request
from common import LOCAL, write_json, EVIDENCE, file_hash

def fetch(package,version,tag):
    u=f'https://pypi.org/pypi/{package}/{version}/json'
    meta=json.load(urllib.request.urlopen(u,timeout=30))
    f=next(f for f in meta['urls'] if f['filename'].endswith('.whl') and tag in f['filename'])
    print(f['filename'],f['size'],'bytes',flush=True)
    wheels=LOCAL/'wheels';wheels.mkdir(parents=True,exist_ok=True)
    target=wheels/f['filename']
    if target.exists() and file_hash(target)==f['digests']['sha256']:return target
    parts=LOCAL/'parts'/f['filename'];parts.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();size=1024*1024
    def chunk(index):
        begin=index*size;end=min(begin+size,f['size'])-1
        part=parts/str(index)
        if part.exists() and part.stat().st_size==end-begin+1:return index
        for attempt in range(2):
            if time.monotonic()-started>300:raise TimeoutError('artifact total download deadline')
            try:
                req=urllib.request.Request(f['url'],headers={'Range':f'bytes={begin}-{end}'})
                with urllib.request.urlopen(req,timeout=30) as response:
                    if response.status!=206:raise RuntimeError('server did not honor bounded Range request')
                    data=response.read(end-begin+2)
                assert len(data)==end-begin+1
                part.write_bytes(data);return index
            except Exception:
                if attempt:raise
    count=(f['size']+size-1)//size
    with ThreadPoolExecutor(max_workers=6) as pool:
        done=0
        for result in as_completed([pool.submit(chunk,i) for i in range(count)]):
            result.result();done+=1
            if done%10==0: print(done,'/',count,'chunks',flush=True)
    with target.open('wb') as out:
        for i in range(count):out.write((parts/str(i)).read_bytes())
    actual=file_hash(target)
    assert actual==f['digests']['sha256'],'download hash mismatch'
    write_json(EVIDENCE/(package+'-download.json'),{'metadata_url':u,'filename':f['filename'],'size':f['size'],
        'url':f['url'],'sha256':actual,'elapsed_seconds':time.monotonic()-started,'status':'PASS'})
    print('verified',actual,flush=True)
    return target

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('package');p.add_argument('version');p.add_argument('tag')
    a=p.parse_args();fetch(a.package,a.version,a.tag)
