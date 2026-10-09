"""Render C2C1 observed results and hash-addressed delivery manifest."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
from actio.common import canonical,file_hash,digest
from actio.candidate import verify
from actio.candidate_campaign import implementation
from actio.suite_oracle import fixture_policy
from actio.suite_tasks import get
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c1'


def write(name,value):
    with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def main():
    p=argparse.ArgumentParser();p.add_argument('--census',type=Path,required=True);a=p.parse_args()
    value=json.loads((DOC/'samples/delivery.json').read_bytes());v=verify(value);assert v['valid'],v
    r=v['report'];c=r['counts'];campaign=value['body']['campaign'];freeze=campaign['body']['freeze'];pre=campaign['body']['preregistration']
    census=json.loads(a.census.read_bytes());assert census['status']=='PASS'
    acceptance=json.loads((DOC/'local-acceptance.json').read_bytes());assert acceptance['implementation']==implementation()
    assert all(row['status']=='observed' and {s['seat']:s['action'] for s in row['seats']}==fixture_policy(get(row['unit']['card']),'own_rule') for row in r['rows'])
    assert r['engineering']=='PASS' and c['sent']==48 and r['pair_coverage']['defined']==12
    assert all(pair['delta']=={'a_own':0,'b_local':0,'joint_achieved':0,'format':{'A':0,'B':0},'utilities':{'A':0,'B':0}} for pair in r['pairs'])
    assert census['census']['main_matrix']=={'sent':48,'usage':48,'unknown':0,'unresolved':0}
    lineage=value['body']['lineage'];tables=lineage['body']['tables']
    names={x['id']:json.loads(x['proposal'])['name'] for x in tables['candidate']}
    decisions=[{'candidate_hash':d['candidate'],'name':names[d['candidate']],**json.loads(d['body'])} for d in tables['decision']]
    write('decisions.json',decisions)
    write('failure-latency.json',{'schema':'failure-latency-observation.v2','rows':[{'unit':row['unit']['id'],'arm':row['unit']['arm'],
        'seats':[{'seat':s['seat'],**s['failure']} for s in row['seats']]} for row in r['rows']],
        'historical_compatibility':'c2c0-compatibility.json','rule':'observed total response latency is independent of action admission'})
    write('bindings.json',{'effective_pair_key':'(preregistration_hash, pair_hash); oracle source hash resolved from frozen plan implementation',
        'preregistration_hash':pre['sha256'],'oracle_source_hash':pre['body']['implementation']['suite_oracle.py'],
        'task_source_hash':pre['body']['implementation']['suite_tasks.py'],'execution_refs':r['execution_refs'],
        'unit_diagnostics':r['pairs'],'same_rule_outputs_verified':True,'all_zero_deltas_verified':True})
    gates={'channel_audit':'PASS_LOCAL','candidate_contract':'PASS','paired_execution':'PASS_24_EPISODES_12_ARM_PAIRS',
        'lineage_durability':'PASS_LOCAL_SQLITE','offline_verification':'PASS','provider_compatibility':'NO_NEW_LIVE_EVIDENCE',
        'capability_admission':'insufficient_evidence','production_activation':'BLOCKED_FALSE',
        'billing_reconciliation':'UNVERIFIED','upstream_identity':'UNVERIFIED','human_calibration':'NOT_CALIBRATED',
        'binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
    (DOC/'GATES.md').write_text('# C2C1 Gate\n\n| Gate | 结论 |\n|---|---|\n'+''.join('| '+k+' | '+v+' |\n' for k,v in gates.items())+
        '\n工程 PASS 不等于候选能力准入或 provider 稳定性证据。所有登记候选 activation=false；未创建 active pointer。\n',encoding='utf8',newline='\n')
    lines=['# C2C1 结果','',f'冻结提交 `{freeze["commit"]}`，计划 SHA256 `{pre["sha256"]}`。',
        f'远端核验 {freeze["verified_utc"]} → 首次 intent {freeze["first_intent_utc"]}；本机时间不是独立签名时间戳。','',
        '**工程闭环 PASS**：B0 → 人工通用 checklist C1 → 静态校验 → 真实 DSH/Concordia 本机配对执行 → 独立决策 → SQLite 持久谱系。B0/C1 的能力决策均为 **insufficient_evidence**；四个 synthetic 静态负例均 reject，六个提案全部保留且不可激活。','',
        '| 主矩阵维度 | 数量 |','|---|---|']
    lines += ['| '+k+' | '+str(c[k])+' |' for k in ('planned_episodes','observed_episodes','complete_episodes','assigned','sent','response','terminal','admitted','usage_responses','not_run','unknown','protocol_error')]
    lines += ['','12/12 arm pairs 完整。48 个 HTTP 请求是 seat 级消息，24 是 A/B episodes，12 才是 arm pairs；不是 48 个独立研究样本。两臂采用相同冻结 own_rule fixture，逐卡格式、A hard、B local、joint、两方 toy utility 的差值全部为 0。','',
        '| family | arm | format true/defined | A hard true/defined | B local true/defined | joint true/defined |','|---|---|---|---|---|---|']
    for s in r['strata']:
        lines.append('| '+s['family']+' | '+s['arm']+' | '+' | '.join(str(s[k]['true'])+'/'+str(s[k]['defined']) for k in ('format','a_own','b_local','joint'))+' |')
    lines += ['','逐卡 utility 原值/差值/missing 与真实 wire hashes 见 [bindings](bindings.json)，所有完整分母和逐 seat 诊断见 [report](samples/report.json)。没有跨 family 综合排名、显著性、推广 CI 或无限 z。fixture 不解释清单含义，12 张卡均已用于开发，independent_research_units=0、human_labels=0。','',
        '新 v2 按 index/type 支持同时打开 reasoning/text，核验 raw UTF-8/SSE → 官方 adapter/end → native content/reasoning。只有 content 进入实际 A 行动、B 公开观察、世界与 memory。实际 prepared 仅归一化独立 UUID4 message IDs；full wire 的直接干预仅为 A checklist，固定 A 输出时 B wire 相同。','',
        '旧 C2C0 停止是冻结纯文本 v1 不支持 reasoning_content，不是已观察到的行动文本矛盾。只读新 sidecar 验证 raw/adapter/native 两通道一致；旧 admitted=14、sent/usage=15、not_run=33、unknown=0 及停止点不改。完整 HTTP/终态耗时保持 observed，行动未准入仍缺失；reasoning 正文未复制。','',
        f'本轮主矩阵本机发送 48；开发验收本机发送 {census["census"]["development_admission"]["sent"]}、usage={census["census"]["development_admission"]["usage"]}、unknown={census["census"]["development_admission"]["unknown"]}（包含故意 missing-DONE 和保留的失败验收），单独计数、不拼入主矩阵。新增真实模型/provider/catalog 请求均为 0；历史生成尝试仍 91、目录 GET 1。费用/账单/upstream identity 仍 UNVERIFIED。','',
        f'验收：最终源码 8 项 C2C1 测试通过，另有 20 项受影响旧分派纯回归；历史 C0/C1/C2A.1/C2B0/C2B1 固定 reader 通过，C2B2/C2C0 原报告精确重现。两份失败测试和未发布草案保留，见 [开发记录](DEVELOPMENT.md)。事务内 proposal/event/edge/decision 写失败均回滚，重复登记幂等，evaluating 不重领，重开 DB 等值、坏库拒绝、v2→v3 copy/backup 与旧库不变已检查。','',
        '真实公开 CLI、pip check、源码/安装一致、完整 delivery 在 network/key/env/process/runtime/write 禁止的 audit hook 下核验，以及重新计算 outer hash 的篡改拒绝见 evidence/cli 文件。JSON 是 SQLite 的投影，原始数据库/Worker 日志保存在本地 hash 清单归档；公共 delivery 只承载可迁移的合成运行证据。','',
        f'清理：{len(census["jobs"])} 个具名 Job 均 inactive/reaped；{len(census["services"])} 个服务已 join；{len(census["ports"])} 个记录端口无残留监听；authorized/reserved/sending=0。原始归档、只读 DB hash 与 census 在 [manifest](evidence_manifest.json)。','',
        '[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [计划](preregistration.json) · [提案](proposals.json) · [决策](decisions.json) · [谱系](samples/lineage.json) · [完整导出](samples/delivery.json) · [来源](provenance.json)','',
        '停止于 C2C1。C2C2 仅建议：先独立冻结 live candidate/control 合同、更多独立任务及可审计的能力证据，再讨论 inactive 候选的准入与激活 CAS；本轮不执行、不生成新候选、不自动调用 provider。binary_source_mapping=unproven，full_controller_recovery=unsupported。']
    (DOC/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    path=ROOT/'README.md';old=path.read_text(encoding='utf8');history=old[old.index('## Phase 1C2C0 历史交付'):]
    path.write_text('# Actio-RSI · Phase 1C2C1\n\n双通道审计、单 A scaffold 候选、SQLite 谱系和独立准入闭环已交付。真实 DSH/Concordia loopback 主矩阵 24 episodes / 48 sends / 12 arm pairs 完整，unknown=0、not_run=0、全部 delta=0。工程 PASS，能力 insufficient_evidence，所有候选 activation=false。\n\n入口：[结果](docs/validation/phase1c2c1/RESULTS.md) · [合同](docs/validation/phase1c2c1/CONTRACT.md) · [Gate](docs/validation/phase1c2c1/GATES.md) · [CLI](docs/validation/phase1c2c1/CLI.md) · [manifest](docs/validation/phase1c2c1/evidence_manifest.json)。新增 provider 请求 0；历史生成尝试 91、目录 GET 1 不变。\n\n'+history,encoding='utf8',newline='\n')
    write('installation.json',{'python':sys.version,'platform':platform.platform(),'venv':'.local/phase1c2c1-runtime-venv',
        'bootstrap':'scripts/bootstrap.py --venv .local/phase1c2c1-runtime-venv --offline --concordia-source <pinned local repo>',
        'bootstrap_log_sha256':file_hash(ROOT/'.local/phase1c2c1-bootstrap.log'),'final_install_log_sha256':file_hash(ROOT/'.local/phase1c2c1-install.log'),
        'source_installed_equal':implementation(),'pip_check':'PASS; actual command/exit in evidence/cli record',
        'runtime_pin_check':'PASS; collect.verify_runtime checked installed SDK/runtime versions and executable SHA256',
        'binary_source_mapping':'unproven','provider_requests':0})
    scan=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/phase1c2c1_publish_check.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf8',check=True)
    scan_result=json.loads(scan.stdout);write('evidence/final-publication-scan.json',scan_result)
    write('evidence_manifest.json',{'schema':'phase1c2c1-evidence-manifest.v1','freeze':freeze,'preregistration_hash':pre['sha256'],
        'counts':c,'pair_coverage':r['pair_coverage'],'gates':gates,'lineage':v['lineage'],'census':a.census.resolve().relative_to(DOC).as_posix(),
        'census_sha256':file_hash(a.census),'implementation':implementation(),'local_acceptance':acceptance,
        'external_provider_requests':0,'historical_generation_attempts':91,'catalog_get':1,'activation':False,'publication_secret_scan':scan_result,
        'artifacts':{p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file()},
        'entry_hashes':{n:file_hash(ROOT/n) for n in ('README.md','AGENTS.md','.gitattributes','pyproject.toml')},
        'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for folder in ('scripts','tests') for p in sorted((ROOT/folder).rglob('*')) if p.suffix in ('.py','.mjs')}})
    print(canonical({'status':'PASS','counts':c,'decision':'insufficient_evidence','activation':False}))


if __name__=='__main__':main()
