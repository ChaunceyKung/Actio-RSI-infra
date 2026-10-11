import json
from actio.contracts.json import require

def cleanup(workers,endpoints):
    import ctypes as C
    import socket
    from actio.adapters.runtime.supervisor import kernel
    from actio.adapters.runtime.supervisor import Job
    rows=[]
    for w in workers:
        k=kernel();h=k.OpenJobObjectW(4,False,w['job'])
        if not h:require(C.get_last_error()==2,'Job query failed');active=0
        else:
            j=object.__new__(Job);j.k=k;j.handle=h
            try:active=j.snapshot()['active']
            finally:k.CloseHandle(h)
        require(active==0 and w['state']=='reaped','C5 Worker still active')
        rows.append({'job':w['job'],'root':w['root'],'active':active,'state':w['state'],'report':json.loads(w['report'])})
    ports=[]
    for endpoint in endpoints:
        port=int(endpoint.split(':')[-1].split('/')[0])
        with socket.socket() as s:
            s.settimeout(.5);require(s.connect_ex(('127.0.0.1',port))!=0,'C5 listener remains')
        ports.append({'port':port,'listening':False,'probe':'literal loopback connect_ex'})
    return {'status':'PASS','jobs':rows,'ports':ports,'new_named_jobs_only':True}
