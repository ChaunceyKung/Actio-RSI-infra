"""Experimental SQLite contract experiment, NOT the Actio event store/outbox."""
import json
import sqlite3
import tempfile
from pathlib import Path
from common import digest, write_json, EVIDENCE

class Collector:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.executescript('''
          PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
          CREATE TABLE IF NOT EXISTS occurrence(stream TEXT, seq INTEGER, raw_hash TEXT, raw TEXT, PRIMARY KEY(stream,seq));
          CREATE TABLE IF NOT EXISTS projection(stream TEXT, seq INTEGER, slot TEXT, mapper TEXT, value TEXT, PRIMARY KEY(stream,seq,slot,mapper));
          CREATE TABLE IF NOT EXISTS cursor(stream TEXT PRIMARY KEY, through INTEGER);
          CREATE TABLE IF NOT EXISTS pin(consumer TEXT PRIMARY KEY, mapper TEXT);
          CREATE TABLE IF NOT EXISTS effect(consumer TEXT, stream TEXT, seq INTEGER, slot TEXT, PRIMARY KEY(consumer,stream,seq,slot));
        ''')

    def ingest(self,stream,seq,raw,mapper='v1',slots=('fact','audit'),crash_before_commit=False):
        h=digest(raw)
        with self.db:
            previous=self.db.execute('SELECT raw_hash FROM occurrence WHERE stream=? AND seq=?',(stream,seq)).fetchone()
            if previous and previous[0]!=h: raise ValueError('same occurrence, conflicting raw hash')
            self.db.execute('INSERT OR IGNORE INTO occurrence VALUES(?,?,?,?)',(stream,seq,h,json.dumps(raw)))
            for slot in slots:
                self.db.execute('INSERT OR IGNORE INTO projection VALUES(?,?,?,?,?)',(stream,seq,slot,mapper,json.dumps({'raw':raw,'rendering':mapper})))
            self.db.execute('INSERT OR IGNORE INTO cursor VALUES(?,-1)',(stream,))
            through=self.cursor(stream)
            while self.db.execute('SELECT 1 FROM occurrence WHERE stream=? AND seq=?',(stream,through+1)).fetchone(): through+=1
            self.db.execute('UPDATE cursor SET through=? WHERE stream=?',(through,stream))
            if crash_before_commit: raise RuntimeError('injected before canonical transaction commit')

    def cursor(self,stream):
        r=self.db.execute('SELECT through FROM cursor WHERE stream=?',(stream,)).fetchone()
        return r[0] if r else -1

    def consume(self,consumer,mapper):
        with self.db:
            self.db.execute('INSERT INTO pin VALUES(?,?) ON CONFLICT(consumer) DO UPDATE SET mapper=excluded.mapper',(consumer,mapper))
            self.db.execute('''INSERT OR IGNORE INTO effect SELECT ?,p.stream,p.seq,p.slot
                FROM projection p JOIN cursor c ON p.stream=c.stream
                WHERE p.mapper=? AND p.seq<=c.through''',(consumer,mapper))
        return self.db.execute('SELECT count(*) FROM effect WHERE consumer=?',(consumer,)).fetchone()[0]

def exercise(path):
    c=Collector(path)
    rows=[]
    def ok(test_id,assertions): rows.append({'test_id':test_id,'status':'PASS','assertions':assertions})
    raw={'event':'tool/result','op':'one','value':'synthetic'}
    c.ingest('producer:store-A:session-A:creation-1',0,raw)
    c.ingest('producer:store-A:session-A:creation-1',0,raw)
    assert c.consume('business','v1')==2
    ok('P3-F01-duplicate',['two deliveries, one occurrence; two semantic slots'])
    c.ingest('producer:store-A:session-A:creation-1',0,raw,'v2')
    assert c.consume('business','v2')==2
    assert c.db.execute('SELECT count(*) FROM projection').fetchone()[0]==4
    ok('P3-F01-remap',['v1/v2 projections=4; business effects remain 2; consumer atomically pins v2'])
    try: c.ingest('producer:store-A:session-A:creation-1',0,{'changed':True})
    except ValueError: pass
    else: raise AssertionError('raw conflict not rejected')
    ok('P3-F01-conflict',['same occurrence/different hash rejected; original retained'])
    c.ingest('producer:store-A:session-A:creation-2',0,raw)
    assert c.consume('business','v1')==4
    ok('P3-F01-restart',['new logical stream creation may reuse seq; continuing old stream reuses identity'])
    c.ingest('gap',2,{'n':2}); assert c.cursor('gap')==-1
    c.ingest('gap',0,{'n':0}); assert c.cursor('gap')==0
    c.ingest('gap',1,{'n':1}); assert c.cursor('gap')==2
    ok('P3-F01-gap',['cursor -1 → 0 → 2; advances only contiguous committed prefix'])
    try: c.ingest('before-commit',0,raw,crash_before_commit=True)
    except RuntimeError: pass
    assert c.cursor('before-commit')==-1
    c.db.close()
    c=Collector(path)
    assert c.db.execute("SELECT count(*) FROM occurrence WHERE stream='before-commit'").fetchone()[0]==0
    c.ingest('before-commit',0,raw)
    ok('P3-transaction-rollback',['native observed supplied by caller; rollback before commit; safe re-ingest on reopen'])
    n=c.consume('business','v1')
    # Effect commit has happened; emulate dropped acknowledgment and reopen.
    c.db.close(); c=Collector(path)
    assert c.consume('business','v1')==n
    ok('P3-ack-lost',['effect transaction committed before ack loss; replay after reopen does not increment count'])
    c.db.close()
    return rows

if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='phase1a-event-') as temp: rows=exercise(Path(temp)/'probe.sqlite')
    write_json(EVIDENCE/'events.json',{'mode':'SQLITE_CONTRACT_FIXTURE','tests':rows,
      'limits':['exception rollback/reopen, not power-loss durability','business effect is local SQLite ledger, not remote exactly-once','new slots require explicit consumer migration; never silently count remapping as a new occurrence']})
    print(f'{len(rows)} event contract checks passed')
