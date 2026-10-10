"""A data-only ordering proposal; no claim, clock trigger or execution capability."""
import random
from collections import Counter
from .common import digest
from .eval_contract import seal
from .transport_contract import require
from .robustness_campaign import preregistration

VERSION='future-block-schedule.v1'
SEED=20261014


def coverage(units):
    curves=[]
    for n in range(len(units)+1):
        prefix=units[:n];row={'episodes':n}
        for name,fields in [('candidate',('card',)),('hidden_world',('structural_group','presentation','arm')),
                            ('presentation',('structural_group','world','arm'))]:
            counts=Counter(tuple(u[f] for f in fields) for u in prefix)
            require(all(c<=2 for c in counts.values()),'comparison cardinality')
            row[name]=sum(v==2 for v in counts.values())
        curves.append(row)
    return curves


def plan():
    old=preregistration()['body'];units=old['units'];rng=random.Random(SEED)
    groups={f:sorted({u['structural_group'] for u in units if u['family']==f}) for f in ('scheduling','bargaining')}
    for group in groups.values():rng.shuffle(group)
    ordered=[];blocks=[]
    for index in range(4):
        pairs={}
        for family,group in groups.items():
            subset=[u for u in units if u['structural_group']==group[index]]
            worlds=sorted({u['world'] for u in subset});pairs[family]=[]
            for w in worlds:
                for p in ('normal','reversed'):
                    arms=('baseline','candidate') if len(pairs[family])%2==0 else ('candidate','baseline')
                    pairs[family].append([next(u for u in subset if u['world']==w and u['presentation']==p and u['arm']==a) for a in arms])
        start=len(ordered)
        for pairindex in range(4):
            for family in groups:ordered.extend(pairs[family][pairindex])
        blocks.append({'index':index,'start':start,'end':len(ordered),'groups':{f:groups[f][index] for f in groups}})
    require(len(ordered)==64 and {digest(u) for u in ordered}=={digest(u) for u in units},'schedule membership')
    curves={'old':coverage(units),'proposed':coverage(ordered)}
    for n in (16,32,48,64):require(all(curves['proposed'][n][k]==n//2 for k in ('candidate','hidden_world','presentation')),'block coverage')
    return seal({'schema':VERSION,'seed':SEED,'source_units_hash':digest(units),'source_cards_hash':old['cards_hash'],
        'versions':old['versions'],'parameters':old['parameters'],'route':'gpt-5.6','metrics':old['metrics'],
        'groups':groups,'blocks':blocks,'units':[{'order':i,'source_unit':u} for i,u in enumerate(ordered)],
        'seat_slots':[{'order':2*i+j,'source_unit':u['id'],'seat':s} for i,u in enumerate(ordered) for j,s in enumerate(('A','B'))],
        'curves':curves,'planned':{'episodes':64,'slots':128,'candidate':32,'hidden_world':32,'presentation':32},
        'assumption':'each listed prefix completed successfully; hypothetical coverage only',
        'decision_basis':'prefix contrast coverage, not observed outcomes','independent_research_units':0,
        'executable':False,'evaluation_created':False,'activation':False})
