"""Write descriptive results and a non-self-referential evidence inventory."""
import argparse
import json
from pathlib import Path
from actio.common import canonical,file_hash
from actio.pilot_contract import implementation
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2b2'

def main():
    p=argparse.ArgumentParser();p.add_argument('census',type=Path);a=p.parse_args()
    census=json.loads(a.census.read_bytes());assert census['status']=='PASS'
    report=census['pilot_verification']['report'];count=report['counts'];pre=json.loads((DOC/'preregistration.json').read_bytes())
    freeze=json.loads((DOC/'samples/freeze.json').read_bytes());pilot=json.loads((DOC/'samples/pilot.json').read_bytes())
    tests={};failed=[];history=[];cli=[]
    for f in sorted((DOC/'evidence').glob('*.json')):
        d=json.loads(f.read_bytes())
        if 'suite' in d:
            if d['exit_code']!=0:failed.append({'file':f.relative_to(DOC).as_posix(),'suite':d['suite'],'tests_run':d['tests_run']})
            if all(d['source_hashes'].get('src/actio/'+n)==h for n,h in implementation().items()):
                for test in d['tests']:tests[test['id']]={'status':test['status'],'file':f.relative_to(DOC).as_posix()}
        if f.name.startswith('legacy-') and d['status']=='PASS':history.append(f.relative_to(DOC).as_posix())
        if f.name.startswith('cli-') and d['status']=='PASS':cli.append(f.relative_to(DOC).as_posix())
    assert tests and all(t['status']=='PASS' for t in tests.values()) and history and cli
    assert any('full_matrix' in n for n in tests) and any('multichoice' in n for n in tests)
    gates={'measurement_integrity':'PASS','engineering_pilot_execution':'PASS' if pilot['body']['phase_state']=='completed' else 'STOPPED_WITH_COMPLETE_DENOMINATOR',
           'billing_reconciliation':'UNVERIFIED','route_observation':'OBSERVED_IN_RECORDED_WINDOW','upstream_identity':'UNVERIFIED',
           'human_calibration':'NOT_CALIBRATED','judge':'NOT_RUN','research_validity':'NOT_ESTABLISHED','evolution_promotion':'BLOCKED',
           'binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
    (DOC/'GATES.md').write_text('# Phase 1C2B2 Gate\n\n|Gate|结论|\n|---|---|\n'+''.join(f'|{k}|{v}|\n' for k,v in gates.items())+
        '\nmeasurement_integrity 表示版本化文本/输入边界及离线来源绑定通过。pilot 结论限于既定路由、时段、任务矩阵的工程观察。公开报价不等于账户账单或权重身份证明。未进行 judge、真人校准、训练、候选晋升或部署。\n',encoding='utf8',newline='\n')
    lines=['# Phase 1C2B2 结果','',f'预注册冻结提交：`{freeze["commit"]}`；preregistration SHA256：`{pre["sha256"]}`。',
           f'远端核验 {freeze["verified_utc"]}，首次 intent {freeze["first_intent_utc"]}；顺序由导出中的每个请求 UTC 复核。',
           '',f'完整计划 32 episodes / 64 seats。本次状态 `{pilot["body"]["phase_state"]}`：observed episodes={count["observed_episodes"]}、未启动 episodes={count["not_run_episodes"]}。',
           '', '|执行维度|计数|','|---|---|']
    lines.extend(f'|{k}|{count[k]}|' for k in ('assigned','attempted','sent','response','terminal','admitted','not_run','protocol_error','usage_responses','unknown'))
    lines+=['',f'reported input/output tokens：{report["usage"]["input_tokens"]} / {report["usage"]["output_tokens"]}；raw cost 字段 {report["usage"]["cost_fields"]} 条。estimated_cost=null，billed_cost=null，raw cost 币种/单位仍未核实。没有自动 retry、新 API 目录扫描或直接模型诊断。',
            '', '|TokenKey route|格式 true/N|A own true/N|B local true/N|feasible joint true/N|infeasible joint true/N|','|---|---|---|---|---|---|']
    def fraction(v):return f'{v["true"]}/{v["denominator"]}'
    for model,m in report['metrics_by_route'].items():
        lines.append('|'+model+'|'+'|'.join(fraction(v) for v in (m['format'],m['a_own'],m['b_local'],m['joint_by_feasibility']['True'],m['joint_by_feasibility']['False']))+'|')
    lines+=['','共同结果是协议结果，冲突中合法 decline 不记为 B 能力错误。逐单位/seat action、not_run reason、operation/occurrence/receipt、reported cache/reasoning、请求/响应标签、HTTP ID/date、headers/首 text/请求/episode 时延见 [完整报告](samples/report.json)。时延为本机/供应商报告事实，不代表独立网络计时证明；unknown 不按零费用处理。',
            '', '只有一个任务 family、四个参数实例、两类对称结构；两模型为配对路由 cohort，repeats 与镜像相关。joint presentation 同时反转两 seat 选项，不识别单 seat 位置效应。independent_research_units=0；不作能力排名、显著性检验、推广 CI 或 cost-normalized ranking。',
            '',f'当前产品 hash 下 {len(tests)} 个选定测试通过。完整真实 DSH/Concordia 本地矩阵 16 episodes/32 sends；另有负例、UTF-8 字节分片、并发 claim、旧路径与零副作用回归。开发过程 {len(failed)} 次验证运行未通过，原证据全部保留。早期断言曾未实际改到分片文本、将 SDK 外部消息 ID 纳入跨运行 equality、随机取到 B 导致 proposal 替换为空操作；随后用实际内容变更和固定外部 ID 校正。旧 preflight 回归还发现局部导入遮蔽旧 validator，已用独立别名修复并复跑。未更改历史真实原件。',
            '', '最终固定实现重新完成矩阵；此前本地源版本归档在 baseline evidence。固定旧 reader：C0=1e85d8c2、C1=af0a88cf、C2A.1=b086cba、C2B0=f65045a、C2B1=1e00535。原 8 条 C2B1 live raw/adapter/native 文本追加检查全通过，原有 22 次生成尝试（20 次有 usage、2 次 usage 未核实）和 1 次目录 GET 不进入 pilot 分母；历史未核实 usage/费用不回填为 0。',
            '', f'清理清点：{len(census["jobs"])} 个具名 Job 均 inactive/reaped，{len(census["services"])} 个本地服务已 join，剩余监听端口={census["remaining_listeners"]}，活动 reservation/sending={census["unresolved"]}。生成文件已检查真实/假凭据；失败和 raw 数据在明确目录归档，ZIP/hash/逐文件清单见 manifest 指向的 census。依赖 node_modules/bytecode 不重复扫描，固定 runtime/锁定安装另行核对。',
            '', '[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [预注册](preregistration.json) · [历史追加复核](historical-text-review.json) · [route/cost registry](route-cost-registry.json) · [证据 manifest](evidence_manifest.json)',
            '', '停止于 C2B2。C2C 应增加有区分度且有来源的任务、独立校准和评估准入，再考虑单 seat 候选与谱系；本轮不自动执行后续阶段。']
    if pilot['body']['phase_state']=='stopped':
        failure=json.loads((DOC/'failure-review.json').read_bytes())
        lines+=['', '本次停止详情：`'+failure['unit']+'` / '+failure['model']+' / '+failure['seat']+'，官方 pi-ai 原生事件报告 `stream idle timeout after 30000ms`。未取得 HTTP headers/body，不能据此推断供应商是否接收或收费。26 个 episode 完整结束，第 27 个保留 A 的已完成前缀与 B 的 unknown；余下 5 个 episode 未启动。受影响 Worker 已 reaped，未重试、补样或追加模型诊断。详见 [只读故障复核](failure-review.json)。']
    (DOC/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf8')
    start=text.index('当前阶段为测量完整性');end=text.index('## Phase 1C2B1 历史交付',start)
    intro=f'Phase 1C2B2 已完成测量完整性修复与预注册工程 pilot：计划 32 episodes / 64 seats，实际发送 {count["sent"]}，admitted {count["admitted"]}，not_run {count["not_run"]}，unknown {count["unknown"]}。raw→adapter→native 文本绑定和 actor own/public 输入边界已验证；独立集合谓词测量与完整分母可离线复核。\n\n入口：[结果](docs/validation/phase1c2b2/RESULTS.md) · [Gate](docs/validation/phase1c2b2/GATES.md) · [合同](docs/validation/phase1c2b2/CONTRACT.md) · [CLI](docs/validation/phase1c2b2/CLI.md) · [预注册](docs/validation/phase1c2b2/preregistration.json) · [manifest](docs/validation/phase1c2b2/evidence_manifest.json)。费用/账单与上游权重身份仍 UNVERIFIED；本轮不构成研究能力排名、judge 校准或演化晋升。\n\n'
    readme.write_text(text[:start]+intro+text[end:],encoding='utf8',newline='\n')
    manifest={'schema':'phase1c2b2-evidence-manifest.v1','start':'6436fc7bc4d25570ee93fb44ab2428635bf6b218',
        'freeze':freeze,'preregistration_hash':pre['sha256'],'gates':gates,'counts':count,'usage':report['usage'],'test_results':tests,
        'cumulative_real_generation_attempts':22+count['sent'],'historical_generation_attempts_excluded':22,'historical_usage_responses':20,'historical_usage_unverified_attempts':2,'historical_catalog_get_excluded':1,
        'failed_validation_attempts_retained':failed,'fixed_historical_readers':history,'public_cli':cli,
        'census':a.census.relative_to(DOC).as_posix(),'census_sha256':file_hash(a.census),'source_hashes':implementation(),
        'entry_hashes':{n:file_hash(ROOT/n) for n in ('README.md','.gitattributes','AGENTS.md','pyproject.toml')},
        'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for d in ('tests','scripts') for p in (ROOT/d).glob('*') if p.suffix in ('.py','.mjs')},
        'artifact_hashes':{p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file() and p.name!='evidence_manifest.json'},
        'publication':'normal task branch and main push; final commit SHA independently verified after commit; no self-referential commit hash'}
    with (DOC/'evidence_manifest.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical(manifest))
    print(canonical({'tests_passed':len(tests),'gates':gates,'counts':count,'failed_validation_runs_retained':len(failed)}))

if __name__=='__main__':main()
