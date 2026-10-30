# 来源和本次核对范围

## 论文

Žambochová et al., DOI 10.1364/OE.480337。
作者公开预印本及补充：https://arxiv.org/pdf/2209.14508
本次实际读取了PDF解析内容，并截看第5页图3、第11–13页补充S1–S13。
重点事实：理论PSF用NA1.35；图3做[0,1]归一化显示；补充S6之后包含收集因子eta公式；M170；OPD模型随轴向扫描改变油厚。

用户指定补充：article22047950/file52761698。仓库source_audit.md记录本轮Codex已经下载并哈希校验。本次对此附件直链访问失败，故不声称本次再次独立取得该文件；执行时优先复用已校验的本地文件。

## 被审仓库

https://github.com/yyyyzoey/fe3o4-iscat-candidate-v3-results-20261029
固定提交f0f9959db144b01b6e0c6cf82f4a030df6515127。
本次通过GitHub连接实际重读：
- release/review.md
- release/source_audit.md
- release/code/tools/render_figures.py

完整HDF5未在本次重新下载。出图脚本测试输入是此前交接ZIP中的candidate_pilot，非Release的完整数据。

## 三维显示工具

https://plotly.com/python/3d-mesh/
https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.marching_cubes

Marching cubes输出坐标顺序对应输入数组；工具显式从(zeta,y,x)转换为图中的(x,y,zeta)。显示的网格步长记录在audit，原数据不变。
