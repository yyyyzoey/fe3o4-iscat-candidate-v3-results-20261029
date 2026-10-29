# GitHub Release 发布审计

- 状态：**PASS**
- 审计时间（UTC）：`2026-10-29T15:19:15.997603+00:00`
- 仓库：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029
- Release：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/releases/tag/v1.0.0
- Release ID：`427999383`
- 资产总数：`83`
- 数据分片：`76` 个，全部为 `state=uploaded`
- 意外/探测资产：`0`
- 重组后大小：`1273486344` bytes
- 重组后 SHA256：`fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7`

## 核对方法

通过 GitHub REST API 重新读取 Release `v1.0.0` 的全部资产，不经本地上传脚本缓存。对 76 个 `results_bundle.zip.partNNN` 逐一比较：

1. 资产名与清单一致；
2. `state == "uploaded"`；
3. 服务端 `size` 与本地分片 byte 数一致；
4. 服务端 `digest` 等于 `sha256:<本地分片SHA256>`。

同时核对 6 个辅助资产的本地 SHA256 与服务端 digest，并确认 Release 中没有 `probe*.bin`、`parprobe*` 等测试残留。结果见 [github_release_audit.json](github_release_audit.json)。

## 结论

83 个正式资产全部通过服务端 size/digest 核对，0 个问题。该审计证明 Release 资产完整；最终 ZIP 的可重组性还由本地分片顺序重组后的总 SHA256 独立验证。
