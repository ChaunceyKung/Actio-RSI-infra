"""Publish descriptive C2C2 projections, keeping raw reasoning in controlled storage."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
from actio.common import canonical,file_hash,digest
from actio.candidate_evaluation import verify
from actio import evaluation_campaign as contract
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c2'


def write(name,value):
    with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--census',type=Path,required=True);a=p.parse_args()
    value=json.loads((a.root/'delivery.json').read_bytes());checked=verify(value);assert checked['valid'],checked
    report=checked['report'];counts=report['counts'];campaign=value['body']['campaign'];freeze=campaign['body']['freeze']
    census=json.loads(a.census.read_bytes());assert census['status']=='PASS'
    assert census['census']['live_matrix']=={'sent':counts['sent'],'usage':counts['usage_responses'],'unknown':counts['unknown'],'unresolved':0}
    assert report['evidence_kind']=='live_development_exploratory'
    admission=json.loads((DOC/'local-acceptance.json').read_bytes());assert admission['implementation']==contract.implementation()
    write('freeze.json',freeze)
    write('bindings.json',{'preregistration_hash':campaign['body']['preregistration']['sha256'],'execution_refs':report['execution_refs'],
        'pairs':report['pairs'],'source_rule':'pair key is preregistration_hash + pair_hash; B derives from actual own-arm A'})
    write('costs.json',{'policy':'uncapped_for_phase1c2c2','observations':report['usage'],'currency':None,'estimated_usd':None,
        'supplier_received':None,'billing_reconciled':False,'upstream_identity_verified':False,
        'historical_generation_attempts':91,'new_sent':counts['sent'],'cumulative_real_generation_attempts':report['cumulative_real_generation_attempts'],'catalog_get':1})
    write('controlled-delivery.json',{'schema':'controlled-delivery-reference.v1','path':str((a.root/'delivery.json').resolve()),
        'file_sha256':file_hash(a.root/'delivery.json'),'body_sha256':value['sha256'],'reader_source':freeze['commit'],
        'access':'local controlled archive; raw reasoning is required for independent dual-channel verification and excluded from public reports',
        'guarded_cli':'evidence/cli-*.json','public_projection':'samples/report.json','raw_archives_census':str(a.census.relative_to(DOC))})
    complete=report['technical_evidence_complete']
    gates={'candidate_static_contract':'PASS','evaluation_lineage':'PASS','intervention_integrity':'PASS_OBSERVED_PREFIX',
        'measurement_integrity':'PASS_FULL_PLAN_DENOMINATORS','live_execution':'PASS' if complete else 'STOPPED_TECHNICAL_INCOMPLETE',
        'provider_protocol_observation':'PASS_OBSERVED_CAMPAIGN' if complete else 'INCOMPLETE_OR_REJECTED_OBSERVED_PROTOCOL',
        'candidate_development_constraints':'REJECT_OBSERVED_VIOLATIONS' if report['violations']['candidate'] else 'PASS_OBSERVED_ONLY' if complete else 'INCOMPLETE',
        'capability_admission':report['candidate_decision'],'production_activation':'BLOCKED_FALSE',
        'billing/upstream_identity':'UNVERIFIED','binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
    write('gates.json',gates)
    (DOC/'GATES.md').write_text('# C2C2 Gate\n\n| Gate | 结论 |\n|---|---|\n'+''.join('| '+k+' | '+v+' |\n' for k,v in gates.items())+
        '\n各 Gate 独立；工程或测量 PASS 不覆盖候选约束、能力、账单或身份缺口。B0 仅为参照。所有 activation=false。\n',encoding='utf8',newline='\n')
    lines=['# C2C2 结果','',f'冻结提交 `{freeze["commit"]}`。计划 `{campaign["body"]["preregistration"]["sha256"]}`。',
        f'远端核验 {freeze["verified_utc"]} → intent {freeze["first_intent_utc"]}；这是本机记录，不是独立签名时标。','',
        f'技术工程：**{report["engineering"]}**。C1 本轮决策：**{report["candidate_decision"]}**；B0 为参照，未授予晋升决定。能力没有 pass 路径，activation=false。','',
        '| 计数 | 实际值 |','|---|---|']
    lines += ['| '+k+' | '+str(v)+' |' for k,v in counts.items()]
    lines += ['',f'本轮实际外部生成发送 {counts["sent"]}；历史 91 与目录 GET 1 排除于新分母；累计真实生成尝试 {report["cumulative_real_generation_attempts"]}。未进行 smoke、目录扫描、诊断或第二 live 批次。',
        f'开发/验收本机发送 {census["census"]["development_admission"]["sent"]}、usage {census["census"]["development_admission"]["usage"]}、unknown {census["census"]["development_admission"]["unknown"]}，单列而不拼入 live。','',
        '| 指标配对 | assigned | defined | missing | not_applicable |','|---|---|---|---|---|']
    lines += ['| '+name+' | '+' | '.join(str(v[k]) for k in ('assigned','defined','missing','not_applicable'))+' |' for name,v in report['metric_pair_coverage'].items()]
    lines += ['',f'arm pair 执行完成 {report["pair_coverage"]["defined"]}/12；与每个指标能否比较分开。各卡原值/delta/null/原因、全部 seat、family/arm/feasibility 分层见 [report](samples/report.json) 和 [bindings](bindings.json)。',
        f'C1 已观察约束违反 {len(report["violations"]["candidate"])} 项；B0 参照诊断 {len(report["violations"]["baseline"])} 项。任一方格式错误不删除整对；缺失效用不补 0。','',
        '三个前置边界：schema 4 新 evaluation 追加历史，保留旧 candidate decided/decision；技术完成与行为/指标适用性分离；v9 独立 live/rehearsal 接线，旧 v8 仍 local-only。每份 B 输入按本臂实际 A 正向重算，非历史字段及 hidden 反事实保持允许边界。',
        '同一 B0/C1 仍链接 C2C1 原 local 评估及本轮 live 评估。原六份提案/decision、24/48/12/零差值、C2C0/C2B2 的停止与 claim 保留。源库/hash/备份、迁移、两评估事件、重开等值和固定历史 reader 均有证据。','',
        '这 12 卡均已用于开发，单 route、单次两臂没有消除模型随机性或时间漂移。split=development_exploratory，independent_research_units=0，human_labels=0。无整体排名、显著性、推广 CI、候选能力获益或泛化结论。',
        '费用保留原 Decimal 文本；币种/单位、可信报价、账单和上游权重身份未核实，不估 USD、不声称对账。reasoning 仅用于协议一致性核验，正文在 controlled raw archive，不进入公开报告/actor/memory。','',
        f'清理：{len(census["jobs"])} 个本轮具名 Job 均 inactive/reaped，{len(census["services"])} 个本机服务 join，{len(census["ports"])} 个记录端口无监听，authorized/reserved/sending=0。unknown 可保留，不重领。',
        '完整 controlled delivery 已在禁止 key/env/network/process/runtime import/write 的 guard 下独立重算。公共报告为该完整导出的投影；其本地路径、hash 与固定 reader 见 [controlled delivery](controlled-delivery.json)，不把脱敏投影冒充原始可核验协议证据。','',
        '[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [预注册](preregistration.json) · [谱系](samples/lineage.json) · [决策](samples/decision.json) · [manifest](evidence_manifest.json)','',
        '停止于 C2C2；binary_source_mapping=unproven，full_controller_recovery=unsupported。']
    (DOC/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    rootread=ROOT/'README.md';old=rootread.read_text(encoding='utf8')
    rootread.write_text('# Actio-RSI · Phase 1C2C2\n\n'+f'有限真实 B0/C1 配对已交付。实际 {counts["sent"]} 次发送、{counts["usage_responses"]} 份 usage、unknown={counts["unknown"]}、not_run={counts["not_run"]}；工程 {report["engineering"]}，候选决策 {report["candidate_decision"]}，全部 activation=false。\n\n'+
        '[结果](docs/validation/phase1c2c2/RESULTS.md) · [合同](docs/validation/phase1c2c2/CONTRACT.md) · [Gate](docs/validation/phase1c2c2/GATES.md) · [CLI](docs/validation/phase1c2c2/CLI.md) · [manifest](docs/validation/phase1c2c2/evidence_manifest.json)。\n\n## Phase 1C2C1 历史交付\n\n'+old.split('\n',1)[1],encoding='utf8',newline='\n')
    write('installation.json',{'platform':platform.platform(),'python':sys.version,'venv':'.local/phase1c2c2-runtime-venv',
        'bootstrap_log_sha256':file_hash(ROOT/'.local/phase1c2c2-install.log'),'final_install_log_sha256':file_hash(ROOT/'.local/phase1c2c2-cli-fix-install.log'),
        'preceding_install_log_sha256':file_hash(ROOT/'.local/phase1c2c2-final-install.log'),
        'source_installed_equal':contract.implementation(),'pip_check':'PASS; actual argv/exit in CLI evidence','runtime_check':'PASS; census.verify_runtime'})
    scanned=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/phase1c2c2_publish_check.py'),'--live-root',str(a.root)],cwd=ROOT,capture_output=True,text=True,encoding='utf8',check=True)
    scan=json.loads(scanned.stdout);write('evidence/final-publication-scan.json',scan)
    write('evidence_manifest.json',{'schema':'phase1c2c2-evidence-manifest.v1','freeze':freeze,'preregistration_hash':campaign['body']['preregistration']['sha256'],
        'counts':counts,'metric_pair_coverage':report['metric_pair_coverage'],'gates':gates,'lineage':checked['lineage'],
        'census':a.census.resolve().relative_to(DOC).as_posix(),'census_sha256':file_hash(a.census),'implementation':contract.implementation(),
        'historical_generation_attempts':91,'new_external_sends':counts['sent'],'cumulative_real_generation_attempts':report['cumulative_real_generation_attempts'],
        'activation':False,'publication_scan':scan,'artifacts':{p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file()},
        'entry_hashes':{n:file_hash(ROOT/n) for n in ('README.md','AGENTS.md','.gitattributes','pyproject.toml')},
        'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for folder in ('scripts','tests') for p in sorted((ROOT/folder).rglob('*')) if p.suffix in ('.py','.mjs')}})
    print(canonical({'status':'PASS','counts':counts,'decision':report['candidate_decision'],'cumulative_real_generation_attempts':report['cumulative_real_generation_attempts']}))


if __name__=='__main__':main()
