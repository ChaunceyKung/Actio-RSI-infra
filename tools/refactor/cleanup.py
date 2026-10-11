"""Read-only cleanup audit scoped to recorded roots from this refactor run."""
import argparse
import ctypes as C
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
from urllib.parse import urlsplit

from actio.adapters.runtime.supervisor import Job
from actio.adapters.runtime.supervisor import kernel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_bytes())
    roots = {Path(p).resolve() for p in summary['recorded_test_roots']}
    jobs, services, errors, databases = {}, {}, [], set()
    for root in sorted(roots):
        for path in root.rglob('*.sqlite'):
            path = path.resolve()
            if path in databases:
                continue
            databases.add(path)
            try:
                db = sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)
                try:
                    columns = {row[1] for row in db.execute('PRAGMA table_info(worker)')}
                    if {'job', 'root', 'state'} <= columns:
                        for name, folder, state in db.execute('SELECT job,root,state FROM worker'):
                            if not name or not name.startswith('Local\\Actio-'):
                                continue
                            jobs.setdefault(name, {'job': name, 'root': folder, 'recorded_states': []})['recorded_states'].append(state)
                finally:
                    db.close()
            except sqlite3.Error as error:
                errors.append({'path': str(path), 'error_type': type(error).__name__})
        for path in root.rglob('service.json'):
            path = path.resolve()
            if path in services:
                continue
            value = json.loads(path.read_bytes())
            endpoint = value.get('endpoint')
            if not endpoint:
                continue
            url = urlsplit(endpoint)
            if url.hostname != '127.0.0.1' or url.scheme != 'http' or url.port is None:
                errors.append({'path': str(path), 'error_type': 'non_fixture_endpoint'})
                continue
            # Bind an exclusive local socket instead of sending even a probe connection.
            try:
                with socket.socket() as probe:
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    probe.bind(('127.0.0.1', url.port))
                available = True
            except OSError:
                available = False
            states = []
            if not available:
                # An old fixture port may now be an unrelated outbound client's port.
                # Inspect only this numeric local port; never kill its new owner.
                command = ('Get-NetTCPConnection -LocalPort '+str(url.port)+
                           ' -ErrorAction SilentlyContinue | ForEach-Object { [string]$_.State } | ConvertTo-Json -Compress')
                probe = subprocess.run(['powershell', '-NoProfile', '-Command', command],
                                       capture_output=True, text=True, timeout=30,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                if probe.returncode:
                    errors.append({'path': str(path), 'error_type': 'listener_query_failed'})
                    states = ['Unknown']
                elif probe.stdout.strip():
                    states = json.loads(probe.stdout)
                    if isinstance(states, str):
                        states = [states]
            services[path] = {'path': str(path), 'port': url.port, 'joined': value.get('joined'),
                              'exclusive_bind_succeeded': available, 'tcp_states_if_reused': states,
                              'listening': 'Listen' in states or 'Unknown' in states}
    k = kernel()
    for name, row in jobs.items():
        handle = k.OpenJobObjectW(4, False, name)
        if not handle:
            error = C.get_last_error()
            row.update(absent=error == 2, active=0 if error == 2 else None)
            if error != 2:
                errors.append({'job': name, 'winerror': error})
        else:
            job = object.__new__(Job)
            job.k, job.handle = k, handle
            try:
                row.update(job.snapshot(), absent=False)
            finally:
                k.CloseHandle(handle)
        row['recorded_states'] = sorted(set(row['recorded_states']))
    ok = not errors and all(v['active'] == 0 for v in jobs.values()) and all(
        v['joined'] and not v['listening'] for v in services.values())
    result = {'status': 'PASS' if ok else 'INCOMPLETE', 'scope': 'recorded development roots only; formal09/10 have separate cleanup receipts',
              'database_count': len(databases), 'jobs': list(jobs.values()), 'services': list(services.values()),
              'errors': errors, 'processes_terminated_by_audit': 0, 'network_sends_by_audit': 0}
    args.output.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': result['status'], 'jobs': len(jobs), 'services': len(services), 'errors': len(errors),
                      'active': sum(v.get('active') or 0 for v in jobs.values())}))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
