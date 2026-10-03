# PO-S02 · Al/McPeak 公共 n,k 数据镜像与本地继承

- 数据条目：[refractiveindex.info Al / McPeak](https://refractiveindex.info/?shelf=main&book=Al&page=McPeak)
- 原始研究：[McPeak et al. (2015)](https://doi.org/10.1021/ph5004237)
- 本次核验：2026-10-02，重读数据条目、光谱范围和CC0声明，并核对T04本地数据哈希。

数据库将该条目标为Al的McPeak et al. 2015 n,k数据，页面范围0.15–1.7 µm，注记“150 Å/s热蒸发、从Si片模板剥离”，并声明数据库为CC0 1.0。相同数值文件已在T04保存，本次不重新导入、不声称它是本机测量：

- 继承源文件：`04_coating_and_substrate_materials/sources/originals/Al_McPeak.yml`
- 继承源文件SHA-256：`4cc03719aeee3f9c9ea2ecd78affeb3212fbd19a60988d228b59d4f78245a7ec`
- Round2现有派生文件SHA-256：`6de78c8ca9bdf0522f0c72ab2a4182fec0f345442bcca7089db593d548a6b558`
- 当前Round2派生子集为0.4–1.0 µm；在此区间分段线性内插、不外推。

## 适用限制

T04镜像文件应继续视为特定快沉积/模板剥离Al膜的光学数据，不是抽象本征Al、任意厚度、任意基片、任意氧化状态或任意工艺的常数。页面总范围不是“每个波长点都连续可用”的保证；上游表在1.355至1.430 µm之间有数据间断。已知数据没有提供逐点协方差/不确定度，因此不确定度必须记为null或未知，不能填0。需做更宽波段建模时应显式处理缺口，不外推。

## 权利

本地T04 YAML标注refractiveindex.info数据库内容CC0 1.0；该许可覆盖数据库的公开数据镜像范围，不自动改变McPeak论文、插图或补充材料的权利状态。
