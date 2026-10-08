"""Single SQLite authority. All multi-row mutations have an immediate transaction."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import time

from .common import ContractError, canonical, digest, uid


class Store:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(Path(__file__).with_name('schema.sql').read_text())
        with self.tx():
            self.db.execute("INSERT OR IGNORE INTO meta VALUES('store',?)", (uid(),))

    def close(self):
        self.db.close()

    @contextmanager
    def tx(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def row(self, sql, args=()):
        r = self.db.execute(sql, args).fetchone()
        return dict(r) if r else None

    def rows(self, sql, args=()):
        return [dict(r) for r in self.db.execute(sql, args)]

    def agent(self, agent_id, spec=None):
        old = self.row('SELECT * FROM agent WHERE id=?', (agent_id,))
        if spec is None:
            if not old:
                raise ContractError('unknown agent')
            return {**old, 'spec': json.loads(old['spec'])}
        if old:
            if old['spec_hash'] != digest(spec):
                raise ContractError('immutable spec conflict')
            return old
        with self.tx():
            self.db.execute('INSERT INTO agent VALUES(?,?,?)', (agent_id, digest(spec), canonical(spec)))
        return self.agent(agent_id)

    def begin(self, request_key, inputs):
        from .supervisor import process_birth
        h = digest(inputs)
        with self.tx():
            old = self.row('SELECT * FROM run WHERE request_key=?', (request_key,))
            if old:
                if old['input_hash'] != h:
                    raise ContractError('request key conflict')
                return old, False
            if self.row('SELECT * FROM lease'):
                raise ContractError('active lease; TTL cannot authorize takeover')
            epoch = int(self.row("SELECT value FROM meta WHERE key='epoch'")['value']) + 1
            rid = uid()
            self.db.execute("UPDATE meta SET value=? WHERE key='epoch'", (str(epoch),))
            self.db.execute('INSERT INTO run(id,request_key,input_hash,input,epoch,state,task,trajectory,owner_pid,owner_birth,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                            (rid, request_key, h, canonical(inputs), epoch, 'allocated', 'unknown', 'incomplete', os.getpid(), process_birth(os.getpid()), int(time.time())))
            self.db.execute('INSERT INTO lease VALUES(1,?,?)', (rid, epoch))
        return self.run(rid), True

    def fence(self, run, epoch):
        if not self.row('SELECT * FROM lease WHERE run=? AND epoch=?', (run, epoch)):
            raise ContractError('stale epoch')

    def dispatch_fence(self, run, epoch):
        self.fence(run, epoch)
        if time.time()-self.run(run)['created']>=180:
            raise ContractError('run dispatch deadline exceeded; lease still requires cleanup')

    def run(self, run):
        r = self.row('SELECT * FROM run WHERE id=? OR request_key=?', (run, run))
        if not r:
            raise ContractError('unknown run')
        return r

    def audit(self, run, op, kind, body):
        self.db.execute('INSERT INTO audit(run,op,kind,body) VALUES(?,?,?,?)', (run, op, kind, json.dumps(body,ensure_ascii=False,allow_nan=False)))

    def allocate_worker(self, run, epoch, root, job, agent):
        wid, sid, creation = uid(), uid(), uid()
        with self.tx():
            self.dispatch_fence(run, epoch)
            if self.row("SELECT id FROM worker WHERE run=? AND state!='reaped'", (run,)):
                raise ContractError('one managed worker at a time in a run')
            if self.row('SELECT COUNT(*) n FROM worker WHERE run=?',(run,))['n']>=2:
                raise ContractError('run worker budget exhausted')
            self.db.execute('INSERT INTO worker VALUES(?,?,?,?,?,?,?,?)', (wid, run, epoch, str(root), job, None, 'waiting', None))
            self.db.execute('INSERT INTO stream(id,run,worker,agent,native_id,creation,native_store) VALUES(?,?,?,?,?,?,?)',
                            (sid, run, wid, agent, 's'+creation, creation, wid))
        return self.row('SELECT * FROM stream WHERE id=?', (sid,))

    def intent(self, run, epoch, stream, task):
        op = uid()
        with self.tx():
            self.dispatch_fence(run, epoch)
            if self.row('SELECT COUNT(*) n FROM operation WHERE run=?',(run,))['n']>=2:
                raise ContractError('run turn budget exhausted')
            if self.row("SELECT id FROM operation WHERE run=? AND state!='execution_complete'", (run,)):
                raise ContractError('only one active turn')
            self.db.execute('INSERT INTO operation(id,run,stream,epoch,input_hash,state) VALUES(?,?,?,?,?,?)',
                            (op, run, stream, epoch, digest(task), 'dispatch_intent'))
            self.db.execute("UPDATE run SET state='running' WHERE id=?", (run,))
            self.audit(run, op, 'dispatch_intent', task)
        return op

    def op_update(self, op, epoch, **fields):
        allowed = {'state', 'receipt', 'terminal', 'barrier', 'answer', 'reason'}
        if not fields or not fields.keys() <= allowed:
            raise ContractError('invalid operation fields')
        with self.tx():
            row = self.row('SELECT * FROM operation WHERE id=?', (op,))
            self.fence(row['run'], epoch)
            if row['epoch'] != epoch:
                raise ContractError('stale operation epoch')
            self.db.execute('UPDATE operation SET ' + ','.join(k+'=?' for k in fields) + ' WHERE id=?', (*fields.values(), op))

    def finish(self, run, epoch, *, task, reason=None):
        with self.tx():
            self.fence(run, epoch)
            ops = self.rows('SELECT * FROM operation WHERE run=?', (run,))
            live = self.row("SELECT id FROM worker WHERE run=? AND state!='reaped'", (run,))
            if live:
                raise ContractError('cannot release lease before job reaped')
            complete = bool(ops) and all(o['state'] == 'execution_complete' for o in ops)
            state = 'execution_complete' if complete else ('needs_reconcile' if ops else 'infrastructure_failure')
            self.db.execute('UPDATE run SET state=?,task=?,trajectory=?,reason=? WHERE id=?',
                            (state, task if complete else 'unknown', 'complete' if complete else 'incomplete', reason, run))
            self.db.execute('DELETE FROM lease WHERE run=? AND epoch=?', (run, epoch))
        return self.run(run)

    def recover(self):
        from .supervisor import process_birth, reap_named_job
        lease = self.row('SELECT * FROM lease')
        if not lease:
            return []
        old = self.run(lease['run'])
        if process_birth(old['owner_pid']) == old['owner_birth']:
            raise ContractError('owner still alive; no takeover even after TTL')
        reports = []
        for worker in self.rows('SELECT * FROM worker WHERE run=?', (old['id'],)):
            reports.append((worker['id'], reap_named_job(worker['job'])))
        with self.tx():
            self.fence(old['id'], old['epoch'])
            for wid, report in reports:
                self.db.execute("UPDATE worker SET state='reaped',report=? WHERE id=?", (canonical(report), wid))
            self.db.execute("UPDATE operation SET state='needs_reconcile',reason='owner died; never retry unknown dispatch' WHERE run=? AND state!='execution_complete'", (old['id'],))
            self.db.execute("UPDATE run SET state='needs_reconcile',trajectory='incomplete',task='unknown',reason='owner death verified; managed jobs quiesced' WHERE id=?", (old['id'],))
            self.db.execute('DELETE FROM lease WHERE run=?', (old['id'],))
        return reports
