# 来源、获取状态与引用

本文件引用的是公开来源，不代表所有PDF已经下载到包内。

1. Žambochová et al., *Axial profiling of interferometric scattering enables an accurate determination of nanoparticle size*, Optics Express 31, 10101–10113 (2023), DOI 10.1364/OE.480337。
   - https://doi.org/10.1364/OE.480337
   - https://arxiv.org/pdf/2209.14508
   - 本次实际通过网页PDF阅读/截图核对作者预印本正文与补充。容器未成功下载原PDF；包中不伪装有原件。
2. 用户指定补充材料：
   - https://opticapublishing.figshare.com/articles/journal_contribution/Supplementary_document_for_Axial_Profiling_of_Interferometric_Scattering_Enables_an_Accurate_Determination_of_Nanoparticle_Size_-_6288691_pdf/22047950?file=52761698
   - 页面显示Version 3，2025-03-04；下载文件52761698。
   - 直接下载及API尝试失败。不能把页面元数据检查说成PDF公式逐式核查。
3. Querry (1985), *Optical constants*, CRDC-CR-85034；磁铁矿数据由refractiveindex.info公开整理：
   - https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe3O4/nk/Querry.yml
   - https://refractiveindex.info/?shelf=main&book=Fe3O4&page=Querry
   - 已核对530与540nm两点；源数据说明CC0。两点数值写入Fe3O4_Querry_bracket.csv，不声称下载了完整表。
4. 独立Mie定义/归一化核对可用开发者官方文档：
   - https://miepython.readthedocs.io/en/stable/api/miepython.core.S1_S2.html
   - https://miepython.readthedocs.io/en/latest/01_basics.html
   - https://pymiescatt.readthedocs.io/en/latest/forward.html
   - 特别注意miepython的复折射率虚部约定和默认S1/S2归一化；不能直接对未经转换的复振幅作比较。本文包的代码没有依赖miepython，不宣称已用它独立核验。
5. scipy球Bessel函数官方定义：
   - https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.spherical_jn.html
   - 数值测试使用mpmath半整数柱Bessel高精度计算作为独立特殊函数路径，不是对同一Scipy函数自比较。
6. 可选界面基准，不是本任务强制替换主模型：
   - https://smuthi.readthedocs.io/en/latest/_source/01%20about/about_smuthi.html
   - Egel et al., *SMUTHI: A python package for the simulation of light scattering by multiple particles near or between planar interfaces*, JQSRT (2021), DOI 10.1016/j.jqsrt.2021.107846。
   - 若使用，阅读当前版本约束；本轮μr=1的光学Fe₃O₄近似不能被混同于求解磁导率张量；厚盖玻片的传播和球—界面多次散射也需正确区分。

核对日期：2026-10-29。论文图像未重新生成或AI重绘；本包生成的是数值代码，不是文献图像替代品。
