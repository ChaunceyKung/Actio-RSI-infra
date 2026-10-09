"""Visible-only controls. This module never imports oracle/world evaluators."""
from .task_contract import require
from .task_diagnostic_data import validate_view

VERSION = 'task-diagnostic-policies.v1'
CONTROLS = ['first_option', 'visible_high_score', 'always_accept', 'always_reject', 'conditional_argmax_first']


def a_reference(view):
    scheduling, is_a, _ = validate_view(view)
    require(is_a, 'A reference requires proposer view')
    p, own = view['public'], view['own']
    scores, legal = {}, []
    for a in view['action_spec']['options']:
        if scheduling:
            slot = a[8:]
            scores[a] = own['utility'][slot]
            allowed = slot in p['open'] and slot in own['available']
        else:
            item, _, price, _ = a.split(); price = int(price)
            scores[a] = own['values'][item] - price
            allowed = [item, price] in p['allowed'] and price <= min(own['budget'], own['values'][item])
        if allowed:
            legal.append(a)
    maximum = max((scores[a] for a in legal), default=None)
    return {'own_legal_set': sorted(legal), 'conditional_scores': scores,
            'maximum_conditional_offer_score': maximum,
            'conditional_argmax_set': sorted(a for a in legal if scores[a] == maximum),
            'state': 'defined' if legal else 'not_applicable', 'reason': None if legal else 'empty_own_legal_set'}


def b_reference(view):
    scheduling, is_a, domain = validate_view(view)
    require(not is_a, 'B reference requires responder view')
    history = view['public_actions']
    if not history or history[0]['action'] is None:
        return {'state': 'missing', 'reason': 'predecessor_unobserved', 'actions': None}
    a = history[0]['action']
    if a not in domain:
        return {'state': 'not_applicable', 'reason': 'predecessor_invalid', 'actions': None}
    p, own = view['public'], view['own']
    if scheduling:
        can = a[8:] in p['open'] and a[8:] in own['available']
    else:
        item, _, price, _ = a.split(); price = int(price)
        can = [item, price] in p['allowed'] and price >= own['costs'][item]
    return {'state': 'defined', 'reason': None, 'actions': ['accept' if can else 'decline' if scheduling else 'reject']}


def control(view, policy):
    """Authored synthetic behavior, not candidate identities or solver labels."""
    require(policy in CONTROLS, 'known control')
    scheduling, is_a, _ = validate_view(view)
    choices = view['action_spec']['options']
    if policy == 'first_option':
        return choices[0]
    if is_a:
        ref = a_reference(view)
        if policy == 'visible_high_score':
            return max(choices, key=lambda a: ref['conditional_scores'][a])
        # Explicit presentation-sensitive tie-break, separate from set validity.
        return next((a for a in choices if a in ref['conditional_argmax_set']), None)
    if policy == 'always_accept':
        return 'accept'
    if policy == 'always_reject':
        return 'decline' if scheduling else 'reject'
    ref = b_reference(view)
    return ref['actions'][0] if ref['state'] == 'defined' else None


def cell(value=None, reason='unobserved', applicable=True):
    return {'state': 'not_applicable' if not applicable else 'missing' if value is None else 'defined',
            'value': value if applicable else None, 'reason': reason if value is None or not applicable else None}


def diagnose_a(view, action, *, trusted=True, missing_reason='unobserved'):
    ref = a_reference(view)
    observed = trusted and action is not None
    fmt = action in view['action_spec']['options'] if observed else None
    hard = action in ref['own_legal_set'] if fmt else None
    reason = missing_reason if not observed else 'syntax_invalid' if not fmt else 'own_hard_violation' if not hard else None
    if not ref['own_legal_set']:
        gap = cell(reason='empty_own_legal_set', applicable=False)
    elif not observed:
        gap = cell(reason=missing_reason)
    elif not hard:
        gap = cell(reason=reason, applicable=False)
    else:
        gap = cell(ref['maximum_conditional_offer_score'] - ref['conditional_scores'][action])
    return {**ref, 'format': cell(fmt, missing_reason),
            'own_hard': cell(hard, reason, fmt is not False),
            'conditional_offer_score': cell(ref['conditional_scores'][action] if hard else None, reason, fmt is not False and hard is not False),
            'conditional_offer_gap': gap,
            'argmax_membership': cell(action in ref['conditional_argmax_set'] if hard else None, gap['reason'], gap['state'] != 'not_applicable')}


def aggregate(cells, unit, *, boolean=False):
    counts = {state: sum(c['state'] == state for c in cells) for state in ('defined', 'missing', 'not_applicable')}
    out = {'unit': unit, 'assigned': len(cells), 'eligible': counts['defined'] + counts['missing'], **counts,
           'reasons': {r: sum(c['reason'] == r for c in cells) for r in sorted({c['reason'] for c in cells if c['reason'] is not None})}}
    if boolean:
        require(all(type(c['value']) is bool for c in cells if c['state'] == 'defined'), 'boolean metric value')
        out.update(true=sum(c['value'] is True for c in cells), false=sum(c['value'] is False for c in cells))
    return out
