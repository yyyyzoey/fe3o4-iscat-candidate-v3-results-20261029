# logs 目录说明

本目录保存**真实执行日志**，不做美化。

| 文件 | 内容 |
|---|---|
| `tests/solver_and_v41_35.log` | 核心光学 + V4.1 回归（35 例） |
| `tests/exporter_9.log` | 导出器（9 例） |
| `tests/legacy_7.log` | 交接包 legacy（7 例） |
| `tests/handoff_audit_21.log` | 交接包审计（21 例） |
| `tests/strict_auditor_12.log` | 严格独立审计器（12 例） |
| `tests/verifier_14.log` | 打包验证器负向注入（14 例） |
| `execution_log.md` | 本轮封装/审计/验证的实际命令、时间、退出码、耗时 |
| `step_index.jsonl` | 与 `execution_log.md` 对应的机器可读记录 |

约定：

- 日志为命令 stdout/stderr 原文；失败不会被删除。
- 退出码、耗时与日志哈希同时记录在 `validation/tests.json` 与 `logs/step_index.jsonl`。
- 不包含 token、邮箱或本机绝对路径（发布前经 `validation/privacy_scan_final.json` 扫描）。
