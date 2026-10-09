"""Publish actual finite pilot coverage, limitations and sealed artifact inventory."""
import argparse
import json
from pathlib import Path
from actio.common import canonical,file_hash
from actio.suite_contract import implementation
from actio.suite_measurement import verify
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c0'

def write(name,v):
    with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(v))

def main():
    p=argparse.ArgumentParser();p.add_argument('--census',type=Path,required=True);a=p.parse_args()
    value=json.loads((DOC/'samples/pilot.json').read_bytes());v=verify(value);assert v['valid'],v
    r=v['report'];counts=r['counts'];freeze=value['body']['freeze'];pre=value['body']['preregistration'];census=json.loads(a.census.read_bytes());assert census['status']=='PASS'
    acceptance=json.loads((DOC/'local-acceptance.json').read_bytes());assert acceptance['implementation']==implementation()
    failures=[{'unit':x['unit'],'reason':x['reason'],'seats':[{'seat':s['seat'],'failure':s['failure'],'admitted':s['admitted'],'format':s['format']} for s in x['seats']]} for x in r['rows'] if x['status']=='observed' and any(s['protocol_error'] for s in x['seats'])]
    write('failure-review.json',{'failures':failures,'automatic_retry':False,'extra_diagnostic_model_calls':0,'supplier_received':None,'billed_cost':None})
    state=value['body']['phase_state'];gates={'task_suite_admission':'PASS','measurement_admission':'PASS','transport_readiness':'PASS_LOCAL_CONTRACT_ONLY',
      'pilot_execution':'COMPLETED' if state=='completed' else 'STOPPED_WITH_COMPLETE_DENOMINATOR','billing_reconciliation':'UNVERIFIED','upstream_identity':'UNVERIFIED',
      'human_calibration':'NOT_CALIBRATED','judge':'NOT_RUN','research_validity':'NOT_ESTABLISHED','evolution_promotion':'BLOCKED','binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
    (DOC/'GATES.md').write_text('# C2C0 Gate\n\n| Gate | 结论 |\n|---|---|\n'+''.join('| '+k+' | '+v+' |\n' for k,v in gates.items())+'\n本机期限合同通过不证明供应商可靠性；任务/指标工程准入不代表真人效度、研究独立性或演化准入。human_labels=0。\n',encoding='utf8',newline='\n')
    lines=['# C2C0 结果','',f'冻结提交 `{freeze["commit"]}`；preregistration SHA256 `{pre["sha256"]}`。',
      f'发布核验 {freeze["verified_utc"]} → intent {freeze["first_intent_utc"]}；本机时间记录，非独立签名时间证明。',
      '',f'正式 pilot 状态 **{state}**。计划 24 episodes / 48 seats，实际启动 {counts["observed_episodes"]}，可评估完整 pair {counts["complete_episodes"]}，未启动 {counts["not_run_episodes"]}。',
      '', '| 执行维度 | 数量 |','|---|---|']
    lines += ['| '+k+' | '+str(counts[k])+' |' for k in ('assigned','attempted','sent','response','terminal','admitted','not_run','protocol_error','usage_responses','unknown')]
    lines += ['',f'reported input/output tokens={r["usage"]["input_tokens"]}/{r["usage"]["output_tokens"]}；raw cost 字段 {r["usage"]["cost_fields"]} 条，币种/单位未核实；estimated_cost=null，billed_cost=null。unknown 不等于免费或未接收。',
      f'历史 76 次生成尝试及 1 次目录 GET 排除于本轮；累计真实生成尝试 {r["cumulative_real_generation_attempts"]}。loopback 在 census 中独立统计，不混作 provider 调用。',
      '', '| family | route | format true/defined/missing | A hard true/defined | B local true/defined | joint true/defined/missing |', '|---|---|---|---|---|---|']
    for s in r['strata']:
        def f(k,missing=False):
            v=s[k];return '/'.join(map(str,[v['true'],v['defined']]+([v['missing']] if missing else [])))
        lines.append('| '+s['family']+' | '+s['route']+' | '+f('format',True)+' | '+f('a_own')+' | '+f('b_local')+' | '+f('joint',True)+' |')
    lines += ['', '逐 seat/episode/pair 的 assigned/eligible/defined/missing/not_applicable、分层 feasibility、真实行动、效用/全知 regret/Pareto、时延与删失标记见 [完整报告](samples/report.json)。可信格式错误也计入 format；不完整、非法与不可信的效用为 null。合法拒绝和不可行任务不冒称 actor 能力错误。',
      '',f'本机准入：当前产品下 {len(acceptance["tests"])} 项选定测试通过；24 episodes/48 sends 两 family × 两 route 标签真实 DSH/Concordia 矩阵通过。穷举真值、手算边界和 4 个离线控制策略证明指标区分度；human_labels=0。实际完整 wire 反事实、严格 raw/adapter/native、计划删改拒绝、unknown/一次 claim、零副作用与离线 reader 通过。',
      '新 headers/idle/total=60/60/90 秒；固定 runtime 的 31 秒延迟 headers 通过，缩短期限的 headers 前/首文本后/心跳 total/终态附近取消均按有限合同结束。不能据此保证 TokenKey 成功。',
      f'开发验收失败记录保留 {len(acceptance["failed_attempts_retained"])} 次；首次 wire 反事实断言曾用紧凑 JSON 替代 host 的标准 JSON 空白，已按实际序列化修正，产品输入语义未改变。',
      '', 'C2B2 原 reader 精确重现旧报告；新 [纠正表](c2b2-correction.json) 从完整计划分层，两 route 均为 feasible assigned/defined/missing=8/7/1，infeasible=8/6/2。原 unknown、not_run、claim、manifest 未改。',
      '',f'清理：{len(census["jobs"])} 个具名 Job inactive/reaped，{len(census["services"])} 个服务 join，监听端口={census["remaining_listeners"]}，活动 authorized/reserved/sending={census["unresolved"]}。原始运行归档与逐文件清单在 evidence_manifest 指向的 census。']
    if failures:
        lines+=['','本次停止为预注册基础设施停止，未重试、补样或追加真实诊断。具体原生根因、HTTP/body 观察及 unknown 状态见 [failure-review](failure-review.json)。']
    else:lines+=['','所有预定 episodes 已执行；没有追加真实诊断、重试或扩样。']
    lines += ['', '两 family、12 张自编卡及配对 route 不等于独立研究样本；independent_research_units=0。固定呈现不识别位置因果效应，TokenKey 标签不证明上游权重；不作综合排名、显著性、推广 CI 或 cost-normalized ranking。',
       '', '[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [来源/二开](provenance.json) · [任务卡](task-cards.json) · [预注册](preregistration.json) · [manifest](evidence_manifest.json)',
       '', '停止于 C2C0。C2C1 仅建议单 seat 候选/基线/谱系的离线准入演练；本轮没有候选生成、真人校准、judge、训练、正式研究、晋升或部署。']
    (DOC/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    readme=ROOT/'README.md';old=readme.read_text(encoding='utf8');marker='## Phase 1C2B1 历史交付';history=old[old.index(marker):]
    readme.write_text('# Actio-RSI · Phase 1C2C0\n\n任务集与独立评估准入已交付：2 families / 12 张卡，完整分层分母、新有限期限及只读评估器。正式 pilot '+state+'，计划 24 episodes / 48 seats，sent='+str(counts['sent'])+'，usage='+str(counts['usage_responses'])+'，not_run='+str(counts['not_run'])+'，unknown='+str(counts['unknown'])+'。\n\n入口：[结果](docs/validation/phase1c2c0/RESULTS.md) · [Gate](docs/validation/phase1c2c0/GATES.md) · [CLI](docs/validation/phase1c2c0/CLI.md) · [manifest](docs/validation/phase1c2c0/evidence_manifest.json)。费用/上游身份 UNVERIFIED，human_labels=0，无研究排名或晋升。\n\nC2B2 历史：[结果](docs/validation/phase1c2b2/RESULTS.md) · [追加分母纠正](docs/validation/phase1c2c0/c2b2-correction.json)。\n\n'+history,encoding='utf8',newline='\n')
    manifest={'schema':'phase1c2c0-evidence-manifest.v1','start':'4686959df2261d4bbe8c73489ca3e5ca23c2efde','review_baseline':'e89d8b370c6cc53de21f651b49e7b2626eb1a559',
        'freeze':freeze,'preregistration_hash':pre['sha256'],'gates':gates,'counts':counts,'usage':r['usage'],'cumulative_real_generation_attempts':r['cumulative_real_generation_attempts'],
        'historical_generation_attempts_excluded':76,'historical_catalog_get_excluded':1,'source_hashes':implementation(),'local_acceptance':acceptance,
        'census':a.census.relative_to(DOC).as_posix(),'census_sha256':file_hash(a.census),
        'entry_hashes':{n:file_hash(ROOT/n) for n in ('README.md','AGENTS.md','.gitattributes','pyproject.toml')},
        'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for folder in ('scripts','tests') for p in sorted((ROOT/folder).rglob('*')) if p.suffix in ('.py','.mjs')},
        'artifacts':{p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file()}}
    write('evidence_manifest.json',manifest)
    print(canonical({'status':'delivered','counts':counts,'gates':gates}))

if __name__=='__main__':main()
