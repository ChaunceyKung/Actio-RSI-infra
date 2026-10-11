"""C5 read-only diagnostics and explicit local-only validation entry points."""
from pathlib import Path
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.evidence.failure_observation import observe
from actio.evidence.failure_observation import from_entry
from actio.evidence.failure_observation import parse
from actio.evidence.failure_observation import LIMITS
from actio.evidence.failure_fixtures import CASES
from actio.evidence.failure_fixtures import portable_vectors
from actio.evidence.future_schedule import plan as schedule

PACKAGE='transport-diagnostic-package.v2-refactor'
SUITE='transport-diagnostic-suite.v1'


def sources():
    root=Path(__file__).resolve().parents[1]
    return {p.relative_to(root).as_posix():file_hash(p) for p in sorted(root.rglob('*')) if p.suffix in ('.py','.mjs','.sql','.json')}


def plan():
    return {'schema':'transport-diagnostic-plan.v1','cases':CASES,'maximum_loopback_sends':12,
        'new_external_requests':0,'limits':LIMITS,'future':schedule(),'sources':sources(),
        'credential_reads':0,'network_requests':0,'workers_started':0}


def portable(history=None,runtime=None):
    vectors=portable_vectors()
    return seal({'schema':PACKAGE,'scope':'synthetic recomputation and public projections; no historical/raw runtime authentication',
        'sources':[{'path':path,'sha256':sha} for path,sha in sources().items()],'fixtures':vectors,'observations':[observe(v['input']) for v in vectors],
        'future':schedule(),'historical_projection':history,'runtime_projection':runtime,
        'projection_authentication':'hash integrity only; controlled originals require separate verification'})


def analyze(value):
    b=unseal(value)
    if b['schema']=='transport-failure-evidence.v1':return observe(value)
    if b['schema']=='transport-diagnostic-controlled-entry.v1':
        require(set(b)=={'schema','origin','entry'},'controlled entry fields')
        return {'observations':from_entry(b['entry'],b['origin']),'scope':'controlled source authentication'}
    require(b['schema']==PACKAGE,'unknown diagnostic schema')
    expected=portable(b.get('historical_projection'),b.get('runtime_projection'))
    require(value==expected,'portable package/fixture/source/result mismatch')
    return {'valid':True,'scope':b['scope'],'synthetic_vectors':len(b['fixtures']),
        'historical_raw_authenticated':False,'runtime_raw_authenticated':False,'future_hash':b['future']['sha256'],
        'credential_reads':0,'network_requests':0,'workers_started':0}


def read(path):
    p=Path(path);require(p.stat().st_size<=64*1024*1024,'package byte bound')
    return parse(p.read_text(encoding='utf8'),64*1024*1024,source_manifest=sources())
