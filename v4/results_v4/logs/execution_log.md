# 执行日志（机器生成）

本文件由 `build/make_execution_log.py` 从真实产物生成；没有任何一行成功结论是手写的。
测试日志是命令 stdout/stderr 原文，失败不会被删除。

## A. 测试套件实际运行

- 运行窗口：`2026-10-30T07:14:31Z` → `2026-10-30T07:14:35Z`（UTC）
- 合计：98 次运行 / 86 个唯一用例；failures=0，errors=0，skipped=0，全部退出码为 0：True
- 解释器：`CPython 3.11 (isolated venv, path redacted)`
- 测试未被修改以使其通过（`tests_were_not_modified_to_pass`）：`True`

| 套件 | 目标 | 用例 | 退出码 | 耗时(s) | 结论 | 日志 | 字节 | 日志SHA256(前16) |
|---|---|---:|---:|---:|---|---|---:|---|
| `solver_and_v41_35` | `code/solver/tests` | 35/35 | 0 | 1.804 | PASS | `logs/tests/solver_and_v41_35.log` | 4772 | `1b4a03ee1f0bd136` |
| `exporter_9` | `code/package_v4/tests` | 9/9 | 0 | 0.39 | PASS | `logs/tests/exporter_9.log` | 807 | `48c49f26798d11b2` |
| `legacy_7` | `inputs/source_snapshot/legacy/tests` | 7/7 | 0 | 0.517 | PASS | `logs/tests/legacy_7.log` | 922 | `12009566d66a954d` |
| `handoff_audit_21` | `handoff package tests/` | 21/21 | 0 | 0.414 | PASS | `logs/tests/handoff_audit_21.log` | 2296 | `e954e31f2ca141c6` |
| `strict_auditor_12` | `handoff package tests/test_strict_cube_audit.py` | 12/12 | 0 | 0.411 | PASS | `logs/tests/strict_auditor_12.log` | 1520 | `2bc845fdffaca2ed` |
| `verifier_14` | `code/package_v4/tools/test_verify_results_bundle.py` | 14/14 | 0 | 0.425 | PASS | `logs/tests/verifier_14.log` | 1680 | `3ac9e2a42a60b3d4` |

> 计数口径：六组共 98 次测试运行全部通过。strict_auditor_12 的 12 个用例是 handoff_audit_21 的子集，去重后唯一用例为 86 个；runs 与 unique_cases 同时列出，未隐藏重叠。

## B. 冻结证据（封装期间不再改写，故可安全列出 SHA256）

| 文件 | generated_utc | 结论 | 字节 | SHA256(前16) |
|---|---|---|---:|---|
| `validation/preflight_final.json` | 2026-10-30T07:14:14+00:00 | PASS | 689 | `61701114d67c66e9` |
| `validation/parts_verification.json` | 2026-10-30T07:08:50+00:00 | PASS | 42089 | `e3cc733430b7e78f` |
| `validation/execution_package_sha_check.json` | — | PASS | 3685 | `daacbe96410490f4` |
| `validation/baseline_new_verifier.json` | — | PASS | 1804 | `fe2460bcf3a75674` |
| `validation/baseline_strict_audit.json` | — | PASS | 1611 | `66b0d1af50eabb5f` |
| `validation/tests.json` | 2026-10-30T07:14:37+00:00 | PASS | 24118 | `2245108ead23287e` |
| `validation/jones_chain_numbers.json` | 2026-10-30T03:27:37+00:00 | — | 7764 | `db78dc9c1ddb6fd4` |
| `validation/numerical_audit.json` | — | — | 46513 | `a2cc9c3459a8b109` |
| `validation/numerical_spot_recompute.json` | — | CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED | 6077 | `b090faedd0ddee8a` |

## C. 本次封装最终审计（由 `audit_final_tree.py` 在封包前最后重写）

这些报告在生成本文件之后还会被写入一次，因此这里只列用途；它们的最终哈希请以 `SHA256SUMS.txt` 为准。

| 文件 | 用途 |
|---|---|
| `validation/data_hdf5_check_final.json` | HDF5 抽样复读 |
| `validation/figure_checks_final.json` | 图件/CSV/必需产物/最终清单 |
| `validation/html_audit_final.json` | HTML 离线自包含 |
| `validation/html_render_audit_final.json` | headless Edge 实际渲染 |
| `validation/xdmf_audit_final.json` | XDMF 包装器 |
| `validation/privacy_scan_final.json` | 隐私扫描 |
| `validation/acceptance_gates.json` | G00–G15 验收门 |

## D. 本次封装步骤（`run_step.py` 逐条追加，未手写）

| # | 步骤 | 开始(UTC) | 耗时(s) | 退出码 | 日志 | 备注 |
|---:|---|---|---:|---:|---|---|
| 1 | `step01_sanitize` | 2026-10-30T07:24:20+00:00 | 0.08 | 0 | `logs/step01_sanitize.log` | redact third-party emails + rewrite absolute paths in xdmf audit |
| 2 | `step02_xdmf` | 2026-10-30T07:24:24+00:00 | 0.3 | 0 | `logs/step02_xdmf.log` | re-read XDMF wrappers against the saved cubes |
| 3 | `step03_sanitize2` | 2026-10-30T07:24:27+00:00 | 0.08 | 0 | `logs/step03_sanitize2.log` | rewrite absolute paths written by verify_xdmf |
| 4 | `step04_exec_log` | 2026-10-30T07:24:32+00:00 | 0.09 | 0 | `logs/step04_exec_log.log` | regenerate execution_log.md, report 04 and test_run_summary.json from real artifacts |
| 5 | `step05_html_render` | 2026-10-30T07:24:35+00:00 | 8.74 | 0 | `logs/step05_html_render.log` | headless Edge render with DNS blocked, incl. previews/index.html |
| 6 | `step06_audit_final` | 2026-10-30T07:24:48+00:00 | 12.58 | 0 | `logs/step06_audit_final.log` | independent re-read: inventory, PNG decode, CSV, HTML, privacy, HDF5 sampled layers |
| 7 | `step07_html_render_all` | 2026-10-30T07:26:11+00:00 | 7.69 | 0 | `logs/step07_html_render_all.log` | supersedes step05: renders all 9 delivered HTML pages, incl. F3/F5/F6 indices |
| 8 | `step08_previews` | 2026-10-30T07:39:04+00:00 | 9.69 | 0 | `logs/step08_previews.log` | regenerate 2D and orthoslice 3D previews from saved HDF5; no physics recomputation |
| 9 | `step09_preview_docs` | 2026-10-30T07:39:17+00:00 | 0.09 | 0 | `logs/step09_preview_docs.log` | align preview prose/status with the actual orthoslice renderer and add renderer source snapshot |
| 10 | `step10_html_render_final` | 2026-10-30T07:39:25+00:00 | 8.8 | 0 | `logs/step10_html_render_final.log` | render all delivered HTML pages offline in headless Edge after preview/doc updates |
| 11 | `step11_audit_final_tree` | 2026-10-30T07:39:37+00:00 | 13.16 | 0 | `logs/step11_audit_final_tree.log` | post-update inventory, figure/CSV/HTML/privacy checks and sampled HDF5 reread |
| 12 | `step12_execution_log` | 2026-10-30T07:39:58+00:00 | 0.09 | 0 | `logs/step12_execution_log.log` | rebuild execution log and report index from all recorded steps and test artifacts |
| 13 | `step13_html_rerender` | 2026-10-30T07:40:19+00:00 | 7.82 | 0 | `logs/step13_html_rerender.log` | rerender after final START_HERE wording correction |
| 14 | `step14_audit_final_tree` | 2026-10-30T07:40:31+00:00 | 13.13 | 0 | `logs/step14_audit_final_tree.log` | final pre-seal tree audit after renderer, prose and HTML updates |
| 15 | `step15_g15_finalize` | 2026-10-30T07:44:11+00:00 | 0.1 | 0 | `logs/step15_g15_finalize.log` | flip G15 to PASS only after both temporary ZIPs passed external verification |
| 16 | `step16_audit_final_tree_all_pass` | 2026-10-30T07:44:16+00:00 | 16.02 | 1 | `logs/step16_audit_final_tree_all_pass.log` | post-G15 inventory; failed privacy because this step log embedded a local absolute path; log path redacted without changing exit code 1, corrected rerun follows |
| 17 | `step17_audit_final_tree_corrected` | 2026-10-30T07:45:25+00:00 | 15.59 | 0 | `logs/step17_audit_final_tree_corrected.log` | corrected rerun with relative command paths after redacting the absolute-path log incident; exit 1 of step16 is retained |
| 18 | `step18_execution_log` | 2026-10-30T07:45:57+00:00 | 0.09 | 0 | `logs/step18_execution_log.log` | rebuild execution log and report index from all recorded steps and test artifacts |
| 19 | `step19_audit_final_tree_after_log` | 2026-10-30T07:46:01+00:00 | 15.54 | 0 | `logs/step19_audit_final_tree_after_log.log` | final post-log inventory, figure/CSV/HTML/privacy and sampled HDF5 re-read with relative paths |
| 20 | `step20_final_tree_audit` | 2026-10-30T07:46:26+00:00 | 15.54 | 0 | `logs/step20_final_tree_audit.log` | final audit after log regeneration, relative paths only |

- 记录 20 条，其中非零退出码 1 条：`step16_audit_final_tree_all_pass`

## E. 范围声明

- 日志只证明“这些命令实际执行过、退出码如上”，不构成物理正确性认证。
- 结果分类保持 `CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED`。
