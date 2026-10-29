# GitHub Release 发布与公开访问审计

- 状态：**PASS**
- 审计时间（UTC）：`2026-10-29T16:08:46.458141+00:00`
- 仓库：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029
- 仓库可见性：**public**（`private=false`）
- Release：https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029/releases/tag/v1.0.0
- Release ID：`427999383`
- Release target：`f0f9959db144b01b6e0c6cf82f4a030df6515127`
- 审计时 `main`：`e55349a6c06279c6cdba20dd2a1a05b60f58eb0e`
- 资产总数：`83`
- 数据分片：`76` 个，全部为 `state=uploaded`
- 意外/探测资产：`0`
- 重组后大小：`1273486344` bytes
- 重组后 SHA256：`fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7`

## 核对方法

通过 GitHub REST API 重新读取 Release `v1.0.0` 的全部资产，不经本地上传脚本缓存。对 76 个 `results_bundle.zip.partNNN` 逐一比较资产名、`state`、服务端 `size` 和服务端 `digest`；同时比较 7 个辅助资产的本地 SHA256 与服务端 digest，并确认没有 `probe*.bin`、`parprobe*` 等测试残留。

仓库公开后追加匿名访问检查：不携带任何认证头读取仓库元数据与 Release 资产列表，确认 `visibility=public`、`private=false`，且匿名可见资产数与认证读取一致。

## 结论

83 个正式资产全部通过服务端 size/digest 核对，0 个问题。仓库已公开，匿名读取通过。

## 端到端匿名下载与重组测试

- 时间（UTC）：`2026-10-29T16:08:46.457141+00:00`
- 方法：在 `GITHUB_TOKEN` 未设置的情况下直接运行 Release 资产 `download_results.py`，走匿名 `browser_download_url` 路径，8 路并行下载全部 76 个分片。
- 每片 SHA256：全部通过。
- 重组大小：`1273486344` bytes。
- 重组 SHA256：`fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7`。
- ZIP 内部测试：139 个成员，`testzip` 无损坏；成员列表与原始包一致。
- 最终输出：`FINAL ARCHIVE VERIFICATION PASSED`。

详见 [github_public_e2e_download.json](github_public_e2e_download.json) 与 [github_release_audit.json](github_release_audit.json)。
