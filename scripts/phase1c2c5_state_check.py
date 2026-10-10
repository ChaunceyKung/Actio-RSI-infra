"""Read-only final domain/ledger census for the nine exact C5 fixture directories."""
import json
from pathlib import Path
import sqlite3
import sys
from actio.common import canonical,file_hash
from actio.failure_fixtures import CASES
from actio.diagnostic_runtime import MARKER

ROOT=Path(__file__).resolve().parents[1];RUN=Path('D:/actio-c2c5-formal-v1')


def main():
    rows=[]
    for case in CASES:
        p=RUN/case['id']/'episode/domain.sqlite';before=file_hash(p)
        c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
        try:
            counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('memory','world','domain_receipt','scenario_terminal')}
            state,task,trajectory=c.execute('select state,task,trajectory from run').fetchone()
            assert counts['memory']==0 and counts['world']==counts['domain_receipt']==case['admitted']
            assert counts['scenario_terminal']==(0 if case['fault'] else 1)
            assert trajectory==('incomplete' if case['fault'] else 'complete')
            memory=[r[0] for r in c.execute('select content from memory')]
            intents=[r[0] for r in c.execute('select intent from world')]
            assert MARKER not in canonical(memory+intents)
            authority=c.execute("select count(*) from lease where state='active'").fetchone()[0] if 'state' in [r[1] for r in c.execute('pragma table_info(lease)')] else None
        finally:c.close()
        assert before==file_hash(p)
        rows.append({'case':case['id'],'database_sha256':before,'counts':counts,'state':state,'task':task,'trajectory':trajectory,
            'raw_reasoning_in_domain':False,'memory_mode':'empty initial snapshot; no memory rows authored by these social fixtures','lease_active_query':authority})
    result={'status':'PASS','rows':rows,'tool_sha256':file_hash(Path(__file__)),'argv':sys.orig_argv,'read_only_databases_unchanged':True,'additional_sends':0}
    with (ROOT/'docs/validation/phase1c2c5/domain-census.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical(result))
    print(canonical({'status':'PASS','cases':len(rows),'domain_receipts':sum(r['counts']['domain_receipt'] for r in rows),'memory_rows':0}))


if __name__=='__main__':main()
