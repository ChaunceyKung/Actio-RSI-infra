"""Publish an honest pre-live status only after final local acceptance exists."""
import json
from pathlib import Path
from actio.common import canonical,file_hash
from actio import robustness_campaign as c
from phase1c2c4_manifest import refresh

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c4'


def write(name,value):
    (DOC/name).write_text(value if isinstance(value,str) else canonical(value),encoding='utf8',newline='\n')


def main():
    admission=json.loads((DOC/'local-acceptance.json').read_bytes())
    assert admission['status']=='PASS' and admission['implementation']==c.implementation()
    cli=json.loads((DOC/admission['full_rehearsal']['file']).read_bytes())
    census=json.loads((DOC/admission['cleanup']['file']).read_bytes())
    assert cli['rehearsal_counts']['sent']==128 and census['census']['live']['sent']==0
    assert not (ROOT/'.local/phase1c2c4-claims/live-once.json').exists()
    gates={'dataset_task_admission':'PASS','history_preservation':'PASS',
           'runtime_wire_integrity':'PASS_LOCAL_REHEARSAL','channel_measurement':'PASS_LOCAL_REHEARSAL',
           'denominators':'PASS_LOCAL_FULL_ASSIGNED','cleanup':
               'PASS_OS_INACTIVE_PRIOR_JOIN_GAP_RETAINED' if census['services_without_join_receipt'] else 'PASS_LOCAL',
           'publication':'PENDING_FREEZE_COMMIT_AND_REMOTE_CHECK','real_campaign':'NOT_RUN',
           'candidate_development_constraints':'NOT_MEASURED_LIVE','evaluation_decision':'NOT_CREATED',
           'research_validity':'UNESTABLISHED','activation':False,'billing_upstream_identity':'UNVERIFIED',
           'binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
    write('gates.json',gates)
    write('GATES.md','# C2C4 发布前 Gate\n\n| Gate | 结果 |\n|---|---|\n'+
          ''.join(f'| {k} | {v} |\n' for k,v in gates.items())+
          '\n本机准入通过，真实结果尚未测量。执行入口必须独立核验本提交已发布到 main 和任务分支，再记录发布收据与首次 intent 的顺序。\n')
    dev=census['census']['development']
    write('RESULTS.md',f'''# C2C4 发布前结果

本机工程准入 **PASS**；真实 campaign **NOT_RUN**，本轮真实生成发送 **0**。此提交冻结执行实现、完整预注册与本机准入证据，提交及两个远端 SHA 的核对由专用 execute 在首次 intent/send 之前记录，避免自引用提交 hash。

完整 DSH/Concordia loopback 预演为 **64 episodes / 128 sent / 128 admitted**，unknown=0。仅使用本机合成响应，不能作为真实模型结果。候选、隐藏世界、展示对照分别 assigned=32，研究独立单位和真人标签均为0。

本机开发/错误分支另计 **{dev['sent']} sent / {dev['unknown']} unknown**；unknown 与失败库存永久保留。10 项必需测试通过，公开 plan/preflight/analyze/verify/lineage 各有 literal 和只读 guard 验收，完整 execute 经公开 CLI 执行，六项重新 seal 的篡改被拒绝。所有来源和实际 argv 见 [本机准入](local-acceptance.json) 与 [开发记录](DEVELOPMENT.md)。

旧 C2C2 完整 delivery 和 v4 权威原库经固定 reader 认证，C2C3 原包也由固定 reader 核验。schema4 一致快照追加 rehearsal evaluation，保留原 Store identity、六份 candidate decision、全部旧事件与 C1/C2C2 evaluation。预演副本有3 evaluations / 2 evaluation decisions；真实副本尚未建立，不伪造 live 登记或决定。

本机清理核对 {len(census['jobs'])} 个具名 Job 和 {len(census['services'])} 个服务；Job均inactive/reaped，相关端口无监听，active authorized/reserved/sending=0。{census['services_joined']}个服务有join收据；{census['services_without_join_receipt']}个失败预演服务因包装器整体时限退出而无join收据，缺口保留，单独验证进程退出及端口关闭。原26个 C2C2 claim 与历史数据库 hash 均保全。

下一步仅限本阶段唯一真实计划：原32 presentations × B0/C1 × 1 repeat，最多128 seat发送；技术失败停止全后缀，可信非法A跳B且不补样。历史生成尝试139、目录GET1另列；此时累计生成仍为139。金额策略uncapped_for_phase1c2c4，费用币种/单位、账单、上游权重身份UNVERIFIED。

预演不产生真实候选晋升结论；没有capability pass，activation=false。binary_source_mapping=unproven，full_controller_recovery=unsupported，研究有效性UNESTABLISHED。完成唯一计划及离线核验后更新实际结果，停止于C2C4。

[合同](CONTRACT.md) · [Gate](GATES.md) · [CLI](CLI.md) · [预注册](preregistration.json) · [manifest](evidence_manifest.json)。
''')
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf8')
    text=text.replace('当前本机验收进行中，真实 campaign 为 NOT_RUN；首次真实发送前须完成本机准入、冻结提交和两分支发布核对。',
                      '本机准入已 PASS（完整预演 64/128），真实 campaign 为 NOT_RUN；首次真实发送前须完成冻结提交和两分支发布核对。')
    readme.write_text(text,encoding='utf8',newline='\n')
    milestones=ROOT/'MILESTONES.md';text=milestones.read_text(encoding='utf8')
    marker='## 当前交付：Phase 1C2C3'
    assert marker in text
    addition=f'''## 当前阶段：Phase 1C2C4 发布前冻结

本机准入 PASS：新 v10/v6 显式接线、原32展示与完整64/128计划、三类各32对照、固定历史 reader/v4一致快照已完成。全矩阵真实DSH/Concordia loopback为64 episodes/128 sent/unknown0；开发错误分支另计{dev['sent']} sent/unknown{dev['unknown']}。10项必要测试、公开CLI及只读guard和六项篡改拒绝通过，原历史证据保全。

本轮真实发送0、live NOT_RUN；历史生成139、目录GET1另列。此提交先发布实现/预注册/本机证据，再由专用execute独立核对main与任务分支、干净工作树及安装源码，随后才允许唯一有限真实campaign。无晋升或激活，研究有效性UNESTABLISHED；不自动启动下一阶段或第二批。

[结果](docs/validation/phase1c2c4/RESULTS.md) · [合同](docs/validation/phase1c2c4/CONTRACT.md) · [Gate](docs/validation/phase1c2c4/GATES.md) · [CLI](docs/validation/phase1c2c4/CLI.md) · [manifest](docs/validation/phase1c2c4/evidence_manifest.json)。

## Phase 1C2C3 历史交付'''
    milestones.write_text(text.replace(marker,addition,1),encoding='utf8',newline='\n')
    write('evidence_manifest.json',{'schema':'robustness-delivery-manifest.v1','stage':'pre_live_freeze',
          'implementation':c.implementation(),'preregistration_sha256':c.preregistration()['sha256'],
          'gates':gates,'rehearsal_counts':cli['rehearsal_counts'],'census':admission['cleanup']['file'],
          'census_sha256':file_hash(DOC/admission['cleanup']['file']),
          'historical_generation_attempts':139,'actual_new_sends':0,'cumulative_real_generation_attempts':139,
          'catalog_get':1,'controlled_raw_required':True,'provider_attestation':False})
    refresh()


if __name__=='__main__':main()
