"""Experimental measurement envelope; controlled returns, no SOTOPIA evaluator."""
import math
from common import EVIDENCE, write_json

def evaluate(trajectory, judge):
    if trajectory.get('infrastructure_error'): return 'infrastructure_failure'
    if not trajectory.get('complete') or not trajectory.get('barrier'): return 'insufficient_evidence'
    if not trajectory.get('legal') or not trajectory.get('isolated') or trajectory.get('requests',0)>6: return 'task_failure'
    try: result=judge()
    except Exception: return 'invalid_measurement'
    if not isinstance(result,list) or len(result)!=2: return 'invalid_measurement'
    if {r.get('agent') for r in result if isinstance(r,dict)}!={'A','B'}: return 'invalid_measurement'
    for row in result:
        scores=row.get('scores',{})
        if set(scores)!={'goal','relationship'}: return 'invalid_measurement'
        if any(type(v) not in (float,int) or not math.isfinite(v) or not 0<=v<=10 for v in scores.values()): return 'invalid_measurement'
    return 'valid_measurement'

def run():
    base={'complete':True,'barrier':True,'legal':True,'isolated':True,'requests':2}
    good=[{'agent':a,'scores':{'goal':5,'relationship':6}} for a in ['A','B']]
    cases=[('normal',base,good,'valid_measurement'),('empty',base,[],'invalid_measurement'),
        ('identity',base,[{'agent':'C','scores':{}},good[1]],'invalid_measurement'),
        ('missing_dimension',base,[{'agent':'A','scores':{'goal':5}},good[1]],'invalid_measurement'),
        ('nonnumeric',base,[{'agent':'A','scores':{'goal':'5','relationship':6}},good[1]],'invalid_measurement'),
        ('nonfinite',base,[{'agent':'A','scores':{'goal':float('nan'),'relationship':6}},good[1]],'invalid_measurement'),
        ('judge_exception',base,RuntimeError('synthetic judge failure'),'invalid_measurement'),
        ('illegal',{**base,'legal':False},good,'task_failure'),
        ('leak',{**base,'isolated':False},good,'task_failure'),
        ('budget',{**base,'requests':7},good,'task_failure'),
        ('partial',{**base,'complete':False},good,'insufficient_evidence'),
        ('no_barrier',{**base,'barrier':False},good,'insufficient_evidence'),
        ('worker_loss',{**base,'infrastructure_error':True},good,'infrastructure_failure')]
    rows=[]
    for name,trajectory,response,expected in cases:
        def judge():
            if isinstance(response,Exception): raise response
            return response
        actual=evaluate(trajectory,judge)
        assert actual==expected,(name,actual)
        rows.append({'test_id':'P5-'+name,'status':'PASS','outcome':actual})
    write_json(EVIDENCE/'evaluation.json',{'mode':'CONTROLLED_ENVELOPE_FIXTURE','tests':rows,
        'limits':['No upstream SOTOPIA parser/evaluator execution','No validity, statistical power or evolution claim','B09 requires pilot, independent units, dataset splits, metrics and authorized budget']})
    print(f'{len(rows)} measurement checks passed')

if __name__=='__main__': run()
