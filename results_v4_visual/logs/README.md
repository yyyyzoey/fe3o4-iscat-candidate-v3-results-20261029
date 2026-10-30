# `logs/` — 原始执行日志（append-only）

```
result_class                     = CANDIDATE_PAPER_INSPIRED_NOT_PHYSICALLY_CERTIFIED
through_focus                    = true   (NOT sample-space near field)
full_jones_chain                 = UNVERIFIED
high_na_model_validation         = UNVERIFIED
paper_convention_checks          = UNVERIFIED
absolute_calibration             = false
sample_space_near_field          = false
publisher_typeset_pdf            = NOT_OBTAINED
linear_midpoint_reconstruction   = FAILED_KEPT
```

每行一个 JSON 对象，字段固定：

| 字段 | 含义 |
|---|---|
| `step` | 步骤名（`step1_layers` … `step7_package`） |
| `event` | `start` / `done` / 具体产物事件（如 `png`、`html_stack`） |
| `t_rel_s` | 相对本次运行开始的秒数 |
| `utc` | UTC 时间戳 |
| 其余键 | 该事件的载荷（文件路径、字节数、形状、断言结果…） |

日志是**追加**写入的，因此同一个步骤可能有多次运行的记录（包括失败、空跑、重跑）。
这些记录**保留不删**，用于说明真实执行过程；`report/02_generation_log.md` 是对它们的整理。

| 文件 | 体积 | 记录数 |
|---|---|---|
| `step1_layers.jsonl` | 1 KB | 6 |
| `step2_2d.jsonl` | 7 KB | 44 |
| `step3_3d.jsonl` | 8 KB | 53 |
| `step4_axis.jsonl` | 1 KB | 6 |
| `step5_html.jsonl` | 2 KB | 8 |
| `step6_accept.jsonl` | 10 KB | 54 |
| `step7_package.jsonl` | 2 KB | 3 |

## 说明

- 日志里出现的路径是本机绝对路径（`C:\Users\PC\...`），换机器后需要改 `code/vis_common.py` 的 `DATA`。
- 日志不包含任何凭据。
