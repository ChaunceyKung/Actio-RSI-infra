# C2C4 发布前 Gate

| Gate | 结果 |
|---|---|
| dataset_task_admission | PASS |
| history_preservation | PASS |
| runtime_wire_integrity | PASS_LOCAL_REHEARSAL |
| channel_measurement | PASS_LOCAL_REHEARSAL |
| denominators | PASS_LOCAL_FULL_ASSIGNED |
| cleanup | PASS_OS_INACTIVE_PRIOR_JOIN_GAP_RETAINED |
| publication | PENDING_FREEZE_COMMIT_AND_REMOTE_CHECK |
| real_campaign | NOT_RUN |
| candidate_development_constraints | NOT_MEASURED_LIVE |
| evaluation_decision | NOT_CREATED |
| research_validity | UNESTABLISHED |
| activation | False |
| billing_upstream_identity | UNVERIFIED |
| binary_source_mapping | unproven |
| full_controller_recovery | unsupported |

本机准入通过，真实结果尚未测量。执行入口必须独立核验本提交已发布到 main 和任务分支，再记录发布收据与首次 intent 的顺序。
