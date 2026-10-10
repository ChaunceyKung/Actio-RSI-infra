"""Publish safe recomputed reports, keeping controlled raw delivery local."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from actio.common import canonical,file_hash,digest
from actio.robustness import verify
from actio import robustness_campaign as contract
from actio.pilot import create

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c4'


def write(name,value):
    path=DOC/name;path.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(value,str):path.write_text(value,encoding='utf8',newline='\n')
    else:path.write_text(canonical(value),encoding='utf8')


def measurement_tables(report):
    """Human-readable projections of verified cells, with their full denominators."""
    lines=['# C2C4 指标覆盖','',
           '以下均从独立 verifier 返回的 metric cells 汇总；逐 seat 原记录见 [report](samples/report.json)。数值指标的 true/false 不适用，以破折号显示；missing 与 not_applicable 不填0。','',
           '| arm | metric | assigned | eligible | defined | true | false | missing | not_applicable |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for stratum in report['strata']:
        if stratum['field']!='arm':continue
        for name,d in stratum['metrics'].items():
            values=[stratum['value'],name,*[d.get(k,'—') for k in ('assigned','eligible','defined','true','false','missing','not_applicable')]]
            lines.append('| '+' | '.join(map(str,values))+' |')
    lines.extend(['','assigned=eligible+not_applicable；eligible=defined+missing；布尔defined=true+false。',
                  'format/domain 相关，B local_hard/response_rule 同源；public/self 是原 hard 的组成，不将它们相加作为独立证据。条件得分不含接受概率，正 gap 或全知 regret 不能直接判原 hard 违规。'])
    write('MEASUREMENTS.md','\n'.join(lines)+'\n')
    lines=['# C2C4 已观察约束错误','',
           '只列可信 content 的格式、原公开/自身 hard 和 B 原响应规则。技术缺失不计为行为通过；同一 episode 的多个相关谓词合并在一行。','',
           '| episode | arm | card | A action | B action | false metrics |',
           '|---|---|---|---|---|---|']
    count=0
    names=('format_A','format_B','public_hard_A','self_hard_A','public_hard_B','self_hard_B','b_response_rule')
    for row in report['rows']:
        failed=[k for k in names if row['metric_cells'][k]['state']=='defined' and row['metric_cells'][k]['value'] is False]
        if not failed:continue
        count+=1
        actions=[json.dumps(s['action'],ensure_ascii=False).replace('|','&#124;').replace('\n',' ') for s in row['seats']]
        lines.append('| '+' | '.join([row['unit']['id'],row['unit']['arm'],row['unit']['card'],*actions,', '.join(failed)])+' |')
    if not count:lines.append('| — | — | — | — | — | 本轮可信观测中未出现；不证明泛化通过 |')
    write('VIOLATIONS.md','\n'.join(lines)+'\n')
    lines=['# C2C4 三类描述性比较','',
           '三类各 assigned=32，彼此相关，不合并为研究样本量。执行覆盖与逐指标覆盖分列；同输入的输出差异允许存在。','',
           '| comparison | assigned | execution defined | execution missing | A same / defined | B same / defined |',
           '|---|---:|---:|---:|---|---|']
    for name,d in report['comparisons'].items():
        a,b=d['action_equality']['A'],d['action_equality']['B'];e=d['execution_coverage']
        lines.append(f"| {name} | 32 | {e['defined']} | {e['missing']} | {a['true']} / {a['defined']} | {b['true']} / {b['defined']} |")
    e=report['pair_coverage']
    lines.append(f"| candidate | 32 | {e['defined']} | {e['missing']} | 见逐对行动和指标 | 见逐对行动和指标 |")
    lines.extend(['','| candidate metric | assigned | eligible | defined | missing | not_applicable | nonzero delta / defined |',
                  '|---|---:|---:|---:|---:|---:|---|'])
    for name,d in report['metric_pair_coverage'].items():
        nonzero=sum(p['metrics'][name]['delta'] not in (0,None) for p in report['pairs'])
        lines.append('| '+' | '.join(map(str,[name,*[d[k] for k in ('assigned','eligible','defined','missing','not_applicable')],f"{nonzero} / {d['defined']}"]))+' |')
    lines.extend(['','| B conditioned on same actual A | assigned | eligible | defined | missing | not_applicable | B same | B different |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|'])
    for name,d in report['comparisons'].items():
        den=d['B_same_actual_A_conditional']
        lines.append('| '+' | '.join(map(str,[name,*[den[k] for k in ('assigned','eligible','defined','missing','not_applicable','true','false')]]))+' |')
    lines.extend(['','B 同实际 A 子集是事后条件描述。展示比较同时改变两 actor 的 options；A 变化又改变 B 的公开历史，不把所有 B 差异归因于自身选项位置。',
                  '每组行动、允许输入检查、逐指标 null/delta 与原因见 [完整比较](comparisons.json)。单次差异可能混合采样与时间变化；零差值不证明等效，非零不证明泛化收益。'])
    write('COMPARISONS.md','\n'.join(lines)+'\n')


def entry_documents(report,freeze,census):
    counts=report['counts'];decision=report['candidate_decision'];engineering=report['engineering']
    changed=sum(any(m['delta'] not in (None,0) for m in p['metrics'].values()) for p in report['pairs'])
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf8')
    current=(f"**当前交付：Phase 1C2C4。** 原32展示 × B0/C1 的有限真实验证已结束："
             f"{counts['technical_complete_episodes']}/64 episodes 技术完整，实际 sent={counts['sent']}（上限128），"
             f"unknown={counts['unknown']}，not_run={counts['not_run']}。工程 {engineering}，C1 为 `{decision}`，"
             f"候选配对执行完整 {report['pair_coverage']['defined']}/32，至少一项 defined 指标 delta 非零的候选对 {changed}/32。"
             "这是合成诊断开发集的描述性观测，研究有效性 UNESTABLISHED、activation=false；停止于 C2C4。")
    text,n=re.subn(r'\*\*当前(?:阶段|交付)：Phase 1C2C4。\*\*[^\n]*',lambda _:current,text,count=1);assert n==1
    text=text.replace('C2B1/C2C2 历史保留；C2C4 单 `gpt-5.6` TokenKey 有限计划，当前 NOT_RUN',
                      f"C2B1/C2C2 历史保留；C2C4 单 `gpt-5.6` TokenKey 实际 {counts['sent']} sends，工程 {engineering}")
    old='C2C2 实际发送 48 次，unknown=0、not_run=0；全部 12 个配对的逐卡指标 delta=0。历史与本轮累计真实生成尝试为 **139**，目录 GET 另计 1，开发/验收的本机发送另列。它们是操作计数，不能当成模型质量排名或独立统计样本。'
    replacement=(f"历史 C2C2 仍为48 sends、12 pairs、逐卡 delta=0，其证据与决定不变。C2C4 实际 {counts['sent']} sends，"
                 f"候选原约束违规记录 {len(report['violations']['candidate'])} 项、baseline {len(report['violations']['baseline'])} 项（相关谓词不作独立证据相加）。"
                 f"历史139 + 本轮{counts['sent']} = 累计 **{139+counts['sent']}** 次真实生成尝试，目录 GET 另计1；"
                 "本机开发/预演发送另列。这些是操作计数，不是质量排名或独立统计样本。")
    assert old in text or replacement in text;text=text.replace(old,replacement)
    text=text.replace('固定诊断任务真实链路接线、历史保全、三类比较与有限执行准入',
                      '固定诊断任务有限真实验证、历史保全与三类比较')
    text=text.replace('[RESULTS](docs/validation/phase1c2c4/RESULTS.md) → [manifest](docs/validation/phase1c2c4/evidence_manifest.json)',
                      '[RESULTS](docs/validation/phase1c2c4/RESULTS.md) → [指标覆盖](docs/validation/phase1c2c4/MEASUREMENTS.md) → [三类比较](docs/validation/phase1c2c4/COMPARISONS.md)')
    readme.write_text(text,encoding='utf8',newline='\n')
    milestones=ROOT/'MILESTONES.md';text=milestones.read_text(encoding='utf8')
    marker='## 当前阶段：Phase 1C2C4 发布前冻结'
    start=text.index(marker if marker in text else '## 当前交付：Phase 1C2C4');end=text.index('## Phase 1C2C3 历史交付',start)
    dev=census['census']['development'];rehearsal=census['census']['full_rehearsal']
    addition=f'''## 当前交付：Phase 1C2C4

固定32展示 × B0/C1 的唯一有限真实验证已结束。工程 **{engineering}**；实际 attempted/sent/response/usage/admitted 为 {counts['attempted']}/{counts['sent']}/{counts['response']}/{counts['usage_responses']}/{counts['admitted']}，技术完整 {counts['technical_complete_episodes']}/64 episodes，unknown={counts['unknown']}，protocol_error={counts['protocol_error']}，not_run={counts['not_run']}，可信非法A导致B跳过={counts['task_predecessor_invalid']}。候选配对执行完整 {report['pair_coverage']['defined']}/32；候选、隐藏世界、展示三类对照各assigned32，分母分别保留。

C1 新评估为 **{decision}**，原约束违规记录 {len(report['violations']['candidate'])} 项；baseline {len(report['violations']['baseline'])} 项单列。至少一项defined指标delta非零的候选对 {changed}/32。schema4 权威副本追加 C4，保留六份原 candidate decision 与旧 C1/C2C2 评估；本轮3 evaluations / 2 evaluation decisions。无capability pass或激活，研究有效性UNESTABLISHED。

首次真实发送前冻结提交 `{freeze['commit']}` 已发布到main与任务分支，execute在首个intent/send前再次核对。10项必要测试、完整真实DSH/Concordia loopback {rehearsal['sent']} sends、五种literal与五种guard CLI、六项篡改拒绝通过；额外开发/失败预演 {dev['sent']} sends/unknown{dev['unknown']} 独立保留。具名Job全部inactive/reaped，相关端口无监听；{census['services_joined']}个服务有join收据，{census['services_without_join_receipt']}个失败预演服务因包装器整体时限终止而无join收据，缺口保留。原历史claim/库/证据不变。

历史生成139 + 本轮sent {counts['sent']} = 累计 **{139+counts['sent']}**，历史目录GET1另列。费用币种/单位、账单和上游权重身份UNVERIFIED；binary_source_mapping=unproven，full_controller_recovery=unsupported。停止于C2C4，没有第二批、补样、C2C5、搜索、训练、judge或部署。

[结果](docs/validation/phase1c2c4/RESULTS.md) · [指标与分母](docs/validation/phase1c2c4/MEASUREMENTS.md) · [三类比较](docs/validation/phase1c2c4/COMPARISONS.md) · [具体违规](docs/validation/phase1c2c4/VIOLATIONS.md) · [合同](docs/validation/phase1c2c4/CONTRACT.md) · [Gate](docs/validation/phase1c2c4/GATES.md) · [CLI](docs/validation/phase1c2c4/CLI.md) · [manifest](docs/validation/phase1c2c4/evidence_manifest.json)。

'''
    milestones.write_text(text[:start]+addition+text[end:],encoding='utf8',newline='\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve()
    value=json.loads((root/'delivery.json').read_bytes());v=verify(value);assert v['valid'],v
    r=v['report'];counts=r['counts'];freeze=value['body']['campaign']['body']['freeze'];assert freeze
    assert contract.preregistration()==json.loads((DOC/'preregistration.json').read_bytes())
    for name,content in [('report',r),('lineage',value['body']['lineage']),('decision',json.loads((root/'decision.json').read_bytes()))]:write('samples/'+name+'.json',content)
    write('comparisons.json',{'candidate':r['pairs'],**r['comparisons'],'denominators':r['comparison_denominators']})
    measurement_tables(r)
    write('freeze.json',freeze)
    write('controlled-delivery.json',{'path':str(root/'delivery.json'),'file_sha256':file_hash(root/'delivery.json'),
        'body_sha256':value['sha256'],'report_sha256':digest(r),'raw_reasoning_published':False,
        'scope':'full controlled evidence reauthentication requires fixed frozen reader and original delivery; public report is a projection'})
    claims=ROOT/'.local/phase1c2c4-claims'
    write('execution-claims.json',{'namespace':str(claims),'files':{p.name:{'sha256':file_hash(p),'body':json.loads(p.read_bytes())} for p in sorted(claims.glob('*.json'))},'deleted_or_reclaimed':False})
    censuses=[(p,json.loads(p.read_bytes())) for p in (DOC/'evidence').glob('census-*.json')]
    censuspath,census=next((p,v) for p,v in reversed(sorted(censuses,key=lambda x:x[0].stat().st_mtime)) if v['census']['live']['sent']==counts['sent'])
    entry_documents(r,freeze,census)
    write('costs.json',{'historical_generation_attempts':139,'catalog_get':1,'this_phase':counts,
        'cumulative_real_generation_attempts':139+counts['sent'],'spending_policy':'uncapped_for_phase1c2c4','usage':r['usage'],
        'upstream_weights_identity':'UNVERIFIED','no_currency_inference':True})
    gates={'dataset_task_admission':'PASS','history_preservation':'PASS','runtime_wire_integrity':'PASS' if r['technical_evidence_complete'] else 'INCOMPLETE',
        'channel_measurement':'PASS' if r['technical_evidence_complete'] else 'INCOMPLETE','denominators':'PASS_FULL_ASSIGNED',
        'cleanup':'PASS_OS_INACTIVE_PRIOR_JOIN_GAP_RETAINED' if census['services_without_join_receipt'] else 'PASS',
        'publication':'PASS_PRE_FIRST_INTENT','candidate_development_constraints':
            'REJECT_OBSERVED' if r['violations']['candidate'] else 'PASS_OBSERVED_ONLY' if r['technical_evidence_complete'] else 'UNESTABLISHED_TECHNICAL_INCOMPLETE',
        'evaluation_decision':r['candidate_decision'],'research_validity':'UNESTABLISHED','activation':False,
        'billing_upstream_identity':'UNVERIFIED','binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
    write('gates.json',gates)
    gate_md='# C2C4 Gate\n\n| Gate | 结果 |\n|---|---|\n'+''.join(f'| {key} | {v} |\n' for key,v in gates.items())
    gate_md+='\n技术缺口不记为行为通过；约束Gate只描述已观察的本开发集行为。完整受控delivery由冻结版本重新核验，公开report不自证raw来源。\n'
    write('GATES.md',gate_md)
    pairs=r['pair_coverage'];comparisons=r['comparisons']
    rows=[]
    for name in ('hidden_world','presentation'):
        d=comparisons[name];aa=d['action_equality']['A'];bb=d['action_equality']['B']
        rows.append(f"| {name} | 32 | {aa['true']}/{aa['defined']} | {bb['true']}/{bb['defined']} | {d['execution_coverage']['defined']} |")
    changed=sum(any(m['delta'] not in (None,0) for m in p['metrics'].values()) for p in r['pairs'])
    text=f'''# C2C4 结果

工程 **{r['engineering']}**；C1 本评估为 **{r['candidate_decision']}**，eligible_for_activation=false。本轮继承合成诊断开发集，不是holdout、模型排名或能力准入。冻结产品提交 `{freeze['commit']}`；最终交付提交通过Git提交本身与最终消息查验，不写自引用hash。

| 执行层次 | 实际 / assigned |
|---|---:|
| 技术完整 episodes | {counts['technical_complete_episodes']} / 64 |
| 执行已解决 episodes | {counts['execution_resolved_episodes']} / 64 |
| attempted / sent / response / usage / admitted | {counts['attempted']} / {counts['sent']} / {counts['response']} / {counts['usage_responses']} / {counts['admitted']} |
| assigned seats | 128 |
| unknown / protocol_error / not_run | {counts['unknown']} / {counts['protocol_error']} / {counts['not_run']} |
| 因可信非法A跳过B | {counts['task_predecessor_invalid']} |
| 候选配对执行完整 | {pairs['defined']} / 32 |
| 至少一项defined指标delta非零的候选对 | {changed} / 32 |

上述并列值是不同阶段的计数，不混为同一成功率。逐臂 [指标覆盖](MEASUREMENTS.md)、[具体约束错误](VIOLATIONS.md) 与 [三类比较摘要](COMPARISONS.md) 分别列出完整分母；完整数据见 [report](samples/report.json) 和 [三类比较](comparisons.json)。missing/not_applicable均为null，不用0替代。A条件得分保留所有同分argmax，正gap不自动判原hard违规；joint/regret也不直接判A错误。

| 描述性对照 | assigned | A行动相同 / defined | B行动相同 / defined | 执行完整 |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

B同实际A子集在comparison中标为条件化描述，完整32个展示对照仍保留。隐藏世界A允许输入相同是Gate，输出相同不是Gate；展示同时改变两actor的options，A行动变化又改变B历史。单次差异可能混合采样和时间变化，不识别稳定位置偏好或因果收益。32展示只有16不同A视图，加入两臂32种输入条件，在两隐藏世界重复；独立研究单位和真人标签均0。

候选已观察格式/原hard违规记录 {len(r['violations']['candidate'])} 项，baseline {len(r['violations']['baseline'])} 项。逐项单位和metric在report中保留；B local_hard与response_rule同源，format/domain也相关，不能当独立证据计数。没有capability pass，旧C1/C2C2决定保持不变。

权威副本谱系为 {v['lineage']['evaluations']} evaluations / {v['lineage']['evaluation_decisions']} evaluation decisions，另保留6份原candidate decision。原Store identity、所有旧事件/plan/binding/policy/decision由固定C2C2 reader和代码信任表核验；schema仍为4。

历史生成尝试139，本轮实际sent {counts['sent']}，累计 **{139+counts['sent']}**；历史目录GET1另列。无额外smoke、目录请求、补样、模型筛选或第二批。金额策略uncapped，费用cost原值与来源保留；币种/单位、供应商账单与上游权重身份UNVERIFIED，不估USD、未知不填0。

本机开发/错误分支及失败预演发送 {census['census']['development']['sent']}，其中unknown {census['census']['development']['unknown']}；最终完整预演发送 {census['census']['full_rehearsal']['sent']}，均为loopback合成响应，与真实费用分开。本轮共核查 {len(census['jobs'])} 个具名Job和 {len(census['services'])} 个服务；全部Job已reaped/inactive，相关端口无监听，active authorized/reserved/sending为0。{census['services_joined']}个服务有join收据；{census['services_without_join_receipt']}个失败预演服务被包装器整体时限终止，未产生join收据，保留该缺口并单独核查进程退出/端口关闭。unknown账务与永久claim保留，不授予真实重跑资格。

[本机验收](local-acceptance.json) 绑定最终产品源码；[开发记录](DEVELOPMENT.md)保留所有失败与实际命令。固定C2C2完整delivery/v4原库和固定C3包分别通过；共享源码变化没有刷新历史pins。公开plan/preflight/analyze/verify/lineage实跑并加只读guard；execute通过公开CLI完成本机矩阵与本轮唯一真实campaign。

完整raw/adapter/native、数据库和reasoning只保存在 [受控交付引用](controlled-delivery.json) 指向的本地包；Git只发布行动、分母、测量、谱系及审计摘要。hash不是供应商签名或独立时标。binary_source_mapping=unproven，full_controller_recovery=unsupported。研究有效性UNESTABLISHED，训练/judge/真人校准/生产激活未解锁。

停止于C2C4；不自动启动C2C5或新批次。可信规则错误只定位本轮具体条件；零差值也不证明等效或无效。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [manifest](evidence_manifest.json)。
'''
    write('RESULTS.md',text)
    # Public manifest contains no controlled raw content.
    manifest={'schema':'robustness-delivery-manifest.v1','implementation':contract.implementation(),'freeze':freeze,
        'counts':counts,'gates':gates,'candidate_decision':r['candidate_decision'],'lineage':v['lineage'],
        'census':censuspath.relative_to(DOC).as_posix(),'census_sha256':file_hash(censuspath),
        'artifacts':{p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file() and p.name!='evidence_manifest.json'},
        'tooling':{p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted((ROOT/'scripts').glob('phase1c2c4_*.py'))},
        'historical_generation_attempts':139,'actual_new_sends':counts['sent'],'cumulative_real_generation_attempts':139+counts['sent'],'catalog_get':1,
        'report_sha256':digest(r),'provider_attestation':False,'controlled_raw_required':True,'argv':sys.orig_argv}
    write('evidence_manifest.json',manifest)
    print(canonical({'status':'PASS','counts':counts,'decision':r['candidate_decision'],'comparisons':r['comparison_denominators']}))


if __name__=='__main__':main()
