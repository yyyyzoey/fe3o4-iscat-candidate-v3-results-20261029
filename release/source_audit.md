# 来源与版本审计

审计日期：2026-10-29。结论：用户指定的 Figshare 补充文件已真实下载并按页核对；出版社最终排版 PDF 仍未取得，不能把“指定附件核对”扩大成“所有来源版本均已逐式确认”。

## 1. 论文与附件标识

- 论文：Žambochová et al., *Axial profiling of interferometric scattering enables an accurate determination of nanoparticle size*, Optics Express 31, 10101–10113 (2023), DOI `10.1364/OE.480337`。
- 作者预印本（含补充材料）：`https://arxiv.org/pdf/2209.14508`。
- Figshare 条目：article id `22047950`，DOI `10.6084/m9.figshare.22047950.v3`，version `3`，published `2025-03-04T03:35:23Z`，license CC BY 4.0。
- 用户指定文件：file id `52761698`，名称 `6288691.pdf`。

## 2. 指定 Figshare 文件的实际获取记录

成功 URL：

`https://ndownloader.figshare.com/files/52761698`

本次实际返回：

| 字段 | 实测值 |
|---|---|
| HTTP | 200 |
| Content-Type | `application/pdf` |
| 最终响应 | S3 预签名下载地址，`application/pdf` |
| 字节数 | 2,821,576 |
| PDF 页数 | 12 |
| SHA256 | `62a60e7194230c7ad5ed7635c951dfdab81e6f82e2e0f4772b6b71ef70ffbbfe` |
| Figshare 提供的 MD5 | `1d2a86bb3e910a7ede3d7cef2a70c01b` |
| 本地计算 MD5 | `1d2a86bb3e910a7ede3d7cef2a70c01b` |
| 本地文件 | `results/execution_20261029/review/diagnostics/sources_retrieval/figshare_supplement_file52761698.pdf` |

`retrieval_report.json` 明确记录 `exact_supplement_obtained=true`、`exact_supplement_downloaded_this_run=true`、`cache_used=false`。这不是只看网页元数据；文件本体已落盘并进行了哈希、页数和内容核对。

Figshare 元数据文件 `figshare_article_metadata.json` 也由 API `https://api.figshare.com/v2/articles/22047950` 于本轮重新获取，返回 HTTP 200、3,814 bytes、SHA256 `620787c5c04ead62919aee78b2c64005f4d12f386ca083206cacc7abdec65de1`。其中 file id、大小和 MD5 与下载文件一致。

## 3. 第一次下载失败的真实记录

交接环境第一次执行 `tools/fetch_sources.py` 时，指定文件没有成功下载。原始日志保留在 `results/execution_20261029/logs/fetch_sources.stdout.txt`，其中记录了：

- `https://opticapublishing.figshare.com/ndownloader/files/52761698`：返回内容不是 PDF，疑似 HTML 阻断；
- `https://api.figshare.com/v2/file/download/52761698`：SSL `UNEXPECTED_EOF_WHILE_READING`。

因此第一次运行的状态是 `exact_supplement_downloaded=false`。之后修复下载工具并改用 `ndownloader.figshare.com` 直链，第二次才得到上述 HTTP 200 的 PDF。第二次日志为 `logs/fetch_sources_2.stdout.txt`。这两次记录均保留，不把第一次失败改写成成功。

## 4. 页面与公式核对范围

已把指定 Figshare PDF 的相关页渲染为 PNG，放在 `diagnostics/sources_retrieval/pages/`，并做目视核对：

- 补充第 5 页（PDF 页面编号，印刷页脚 Page 4 | 11）：S1–S3，包括参考场、散射场和 QWP/PBS/Fresnel Jones 描述；
- 补充第 6 页（PDF 页面编号，印刷页脚 Page 5 | 11）：S4–S6，包括 Mie `S1/S2`、`t_p/t_s` 和散射光瞳表达式；
- 补充第 7 页（PDF 页面编号，印刷页脚 Page 6 | 11）：S12/S13，包括 `Ex` 中正的 `J₂ sin(2φ_d)` 方位项；
- 作者预印本第 4 页：主文式 (6)–(11)，包括散射场、OPD 和 iSCAT 对比度定义。

核对结果显示指定补充版本的 S6 印刷项是 `i(S2 t_p + S1 t_s)`，而 S2/S4/S5 的线性链条在返回光 p 基下推得候选项为 `S1 t_s - S2 t_p`。这是本包保持 `CANDIDATE` 的正式原因之一，详见 `formula_audit.md`。

## 5. 作者预印本

- URL：`https://arxiv.org/pdf/2209.14508`
- HTTP 200，`application/pdf`
- 4,776,448 bytes，20 页
- SHA256：`1e40105aa5f1fe5ad399185f0ec84c400178c94fbdb1c1ea199496b452114358`
- 本地文件：`diagnostics/sources_retrieval/author_preprint_including_supplement.pdf`

预印本用于补充指定 Figshare 附件的页码/式号定位；它不能替代出版社最终排版版，也不能证明最终出版版与预印本完全同式。

## 6. 出版社最终 PDF 的访问限制

对出版社 DOI 的最近一次访问只得到 HTTP 202，并重定向到 `opg.optica.org/.../viewmedia.cfm`，没有返回可保存的最终出版社 PDF。因此：

- 已确认真实获取并核对的，是 Figshare version 3 的指定附件；
- 未声称取得出版社最终排版 PDF；
- 未把预印本页面当作最终出版版；
- `source_version_audit=VERIFIED` 的范围仅限用户指定的 Figshare 文件及其作者预印本定位。

## 7. 材料数据来源

Fe₃O₄ 光学常数来自 Querry 1985 的块体磁铁矿数据，经 refractiveindex.info 整理。本轮重新获取：

- URL：`https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe3O4/nk/Querry.yml`
- HTTP 200，16,992 bytes
- SHA256：`c42e5a5007827fb3548df61daf222b164a7799206790fb2116c8488aefe9e802`
- `n=2.3456`、`k=0.0926` 是 530–540 nm 区间线性插值得到的模型值，不是用户颗粒的实测值。

## 8. 历史交接文字与本轮结论

`docs/SOURCES.md`、`docs/FORMULA_AUDIT.md` 和 `full/config_used.json` 中关于 Figshare 下载失败的描述属于交接时的旧状态，已由本轮 `retrieval_report.json` 和本报告覆盖；没有回写历史文件或运行配置，以免伪造当时的运行环境。最终 release 中以本文件及真实检索 JSON 为准。
