# 来源摘要与权利范围

访问/核对日期：2026-10-02 UTC。只引用官方方法资料，以下为原创短摘要；没有下载或交付第三方全文、网页缓存、原图。

## SciPy 1.17.0 quad / QUADPACK

官方链接：https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.integrate.quad.html

用途：核对本机SciPy1.17.0实际API的epsabs/epsrel、points、limit、full_output与warning语义。abserr是绝对误差估计；points用于给已知困难位置分段，limit限制自适应区间数。全文档描述QUADPACK相关后端。本研究把warning保留，不将它或base/tight差写成严格上界。

支持范围：软件调用语义与估计量名称；不为本机物理模型、输入几何、遗漏事件或高频rate提供认证。

## NIST DLMF §3.5 Quadrature

官方链接：https://dlmf.nist.gov/3.5

用途：求积规则、光滑性前提与误差项的基础数学背景。这里的光滑中点误差界需要真实二阶导数界；有硬遮挡/不明rate事件时不能把光滑公式直接套到整个未分段函数。

支持范围：经典求积与误差条件。厚板中心投影、源坐标解析消元、支集Lipschitz控制与本合成数值均为本增补推导，不声称NIST认证本工程。

## 既有项目原创冻结输入

v0.1的t01合同、13点留出、dual_finite与四个frozen Python模块；v0.2的robust_mask.py，只按原字节复制必要小模块，哈希在data/provenance.json。它们是本项目原创研究代码/合成数据；不是第三方论文或实机参数。

保留v0.1的partial状态与v0.2“只作小批量求交子oracle”的范围。新的独立数学证据与旧同源代码回归分别记述；没有将同源相等当独立物理真值。
