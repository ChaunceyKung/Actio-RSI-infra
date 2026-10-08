"""Read-only native journal ingestion and conservative completion predicate."""
import hashlib
import json
from pathlib import Path

from .common import ContractError

MAPPERS = {'v1','v2'}
TYPES = {'agent/inbox/spliced','turn/start','turn/end','assistant/message','step/start','step/end',
         'tool/call','tool/result','user/message','system/message','request/header',
         'request/context','session/title','assistant/attempt'}


def wire(v):
    return json.dumps(v,ensure_ascii=False,allow_nan=False,separators=(',',':'))


class Facts:
    def __init__(self, store):
        self.s = store

    def ingest(self, stream, event, raw=None, mapper='v1'):
        if mapper not in MAPPERS:
            raise ContractError('unknown mapper')
        seq = event.get('seq')
        if type(seq) is not int or seq < 0 or not isinstance(event.get('type'),str) or not isinstance(event.get('data'),dict):
            raise ContractError('unknown native event schema')
        raw = raw if raw is not None else wire(event)
        h = hashlib.sha256(raw.encode()).hexdigest()
        conflict = False
        with self.s.tx():
            old = self.s.row('SELECT * FROM occurrence WHERE stream=? AND seq=?',(stream,seq))
            if old and old['raw_hash']!=h:
                self.s.db.execute('INSERT OR IGNORE INTO conflict VALUES(?,?,?,?,?)',(stream,seq,old['raw_hash'],h,raw))
                self.s.db.execute("UPDATE stream SET integrity='conflict' WHERE id=?",(stream,))
                conflict = True
            else:
                self.s.db.execute('INSERT OR IGNORE INTO occurrence VALUES(?,?,?,?)',(stream,seq,h,raw))
                slots = ['audit']
                if event['type']=='assistant/message':
                    slots.append('assistant.final')
                for slot in slots:
                    self.s.db.execute('INSERT OR IGNORE INTO projection VALUES(?,?,?,?,?)',(stream,seq,slot,mapper,wire({'type':event['type'],'source_hash':h})))
                cursor = self.s.row('SELECT cursor FROM stream WHERE id=?',(stream,))['cursor']
                while self.s.row('SELECT seq FROM occurrence WHERE stream=? AND seq=?',(stream,cursor+1)):
                    cursor += 1
                self.s.db.execute('UPDATE stream SET cursor=? WHERE id=?',(cursor,stream))
        if conflict:
            raise ContractError('same source occurrence has conflicting bytes')

    def collect(self, stream, *, item=65536,total=8*1024*1024,count=4096):
        s = self.s.row('SELECT * FROM stream WHERE id=?',(stream,))
        worker = self.s.row('SELECT * FROM worker WHERE id=?',(s['worker'],))
        base = Path(worker['root'])/'home/sessions'
        paths = list(base.rglob('session.v3.jsonl')) if base.exists() else []
        if len(paths)!=1:
            raise ContractError('managed journal missing or ambiguous')
        path = paths[0]
        if not path.resolve().is_relative_to(base.resolve()) or any(p.is_junction() or p.is_symlink() for p in (path,*path.parents) if p.is_relative_to(base)):
            raise ContractError('unmanaged journal path')
        consumed = n = 0
        try:
            if path.stat().st_size<s['consumed_bytes']:
                raise ContractError('native truncation')
            with path.open('rb') as f:
                header_line = f.readline(item+1)
                if len(header_line)>item or not header_line.endswith(b'\n'):
                    raise ContractError('incomplete journal header')
                header = json.loads(header_line)
                if header.get('type')!='session' or header.get('version')!=3 or header.get('id')!=s['native_id']:
                    raise ContractError('unknown native header/generation')
                if s['header'] and json.loads(s['header'])!=header:
                    raise ContractError('native creation header changed')
                self.s.db.execute('UPDATE stream SET path=?,header=? WHERE id=?',(str(path),wire(header),stream))
                consumed = len(header_line)
                partial = False
                while raw := f.readline(item+1):
                    if len(raw)>item or consumed+len(raw)>total or n>=count:
                        raise ContractError('journal data_limit_exceeded')
                    if not raw.endswith(b'\n'):
                        partial = True
                        break
                    event = json.loads(raw)
                    # Native v3 envelope pinned; new type cannot silently become complete.
                    if event.get('type') not in TYPES:
                        raise ContractError('unmapped native event type: '+str(event.get('type')))
                    self.ingest(stream,event,raw.decode().rstrip('\r\n'))
                    consumed += len(raw); n += 1
                self.s.db.execute("UPDATE stream SET consumed_bytes=?,integrity=? WHERE id=? AND integrity!='conflict'",
                                  (consumed,'partial_tail' if partial else 'valid',stream))
        except (ValueError,ContractError) as e:
            self.s.db.execute("UPDATE stream SET integrity=? WHERE id=? AND integrity!='conflict'",(str(e),stream))
            raise
        return self.s.row('SELECT * FROM stream WHERE id=?',(stream,))

    def certify(self, op, marker):
        o = self.s.row('SELECT * FROM operation WHERE id=?',(op,))
        s = self.s.row('SELECT * FROM stream WHERE id=?',(o['stream'],))
        for key,expected in {'run':o['run'],'op':op,'epoch':o['epoch'],'creation':s['creation'],'session':s['native_id']}.items():
            if marker.get(key)!=expected:
                raise ContractError('stale/unbound flush marker: '+key)
        through = marker.get('through')
        if type(through) is not int or through<0 or s['cursor']<through or s['integrity']!='valid':
            raise ContractError('insufficient contiguous native prefix')
        if not o['receipt'] or marker.get('receipt')!=o['receipt'] or o['terminal']!='completed':
            raise ContractError('receipt/terminal evidence missing')
        events = [json.loads(r['raw']) for r in self.s.rows('SELECT raw FROM occurrence WHERE stream=? AND seq<=? ORDER BY seq',(s['id'],through))]
        receipts = [e for e in events if e['type']=='agent/inbox/spliced' and any(m.get('id')==o['receipt'] for m in e['data'].get('inserted',[]))]
        terminal = marker.get('terminal',{})
        terminals = [e for e in events if e['seq']==terminal.get('seq') and e['type']=='turn/end' and e['data'].get('reason',{}).get('kind')=='completed']
        if not receipts or not terminals or receipts[-1]['seq']>=terminals[0]['seq'] or terminal.get('reason')!='completed':
            raise ContractError('receipt does not delimit an acceptable turn')
        if self.s.row('SELECT seq FROM conflict WHERE stream=?',(s['id'],)):
            raise ContractError('unresolved source conflict')
        return events

    def reconcile(self, run):
        result = []
        for stream in self.s.rows('SELECT id FROM stream WHERE run=?',(run,)):
            try:
                s = self.collect(stream['id'])
                result.append({'stream':stream['id'],'cursor':s['cursor'],'integrity':s['integrity']})
            except ContractError as e:
                result.append({'stream':stream['id'],'error':str(e)})
        # Facts can be recovered without accepted/flush/domain receipts. Never infer success or redispatch.
        return result
