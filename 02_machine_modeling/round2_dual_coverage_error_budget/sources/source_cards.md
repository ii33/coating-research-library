# 来源摘要与访问权利

访问复核 2026-10-02 UTC。以下为短摘要、公式来源入口和既有合法本地档案指针；第三方全文不进入公开允许列表。原创推导、合成参数和数值结果不伪称文献结论。

## R2 S01 归一化正向模型与板设计背景

Zhang L, Cai X. Uniformity Masks Design Method Based on the Shadow Matrix for Coating Materials with Different Condensation Characteristics. 2013, Article160792. DOI10.1155/2013/160792。[官方PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3817662/)。本轮读式1及shadow matrix的限定建模语境，作为发射角、接收角、距离分离的文献入口。文章的经验角指数与特定材料实验不验证本轮有限盘、有限厚板或离子代理，也不授予真实机台精度。

许可页标Creative Commons Attribution，版本未写明。既有T02合法HTML档案哈希已核对，复用不复制；整页还含平台导航，按项目约定local-only。精确指针与哈希见local_originals_excluded.json。

## R2 S02 实体射线求交

Pharr M, Jakob W, Humphreys G. Physically Based Rendering, 4th ed., §6.1.2。[作者在线正文](https://www.pbr-book.org/4ed/Shapes/Basic_Shape_Interface)。本轮核读三个slab参数区间及浮点稳健性说明。它提供通用几何算法背景，不涉及镀膜材料或离子物理。此处代码沿用冻结T02的NumPy版本，不复制教材实现；独立核查另用六面枚举。仅存短摘要/链接，不存网页全文或其图。

## R2 S03 不确定度与非线性

JCGM100:2008及100:2008/Amd.1:2026；[官方目录](https://www.bipm.org/en/committees/jc/jcgm/publications)，修订DOI10.59161/PPDI3267。本轮目录与修订PDF成功读取，修订正文印刷p.1讨论显著非线性时高阶项或Monte Carlo；2008主体本次链接抓取超时，主体相关协方差条款仅继承T02首轮已注明阅读，不冒称重新下载全文。标准不提供本机参数分布或通用百分比容差。版权页All rights reserved；无本地标准副本，无公开全文。

## R2 S04 既有离子计量资料

T10 IS-08 的NASA技术报告NASA CR165334既有合法档案及权利元数据只核对存在/哈希，不把它声称为本轮新增全文阅读。其原档保留在T10，未重复拷贝、不入本轮reader。T10的电流/粒子数、净增长分母和快中性限制作为冻结接口约束。本轮100 eV、单电荷、无快中性均是明示合成假设，不由该报告推定。

## 内部参考模型的复用记录

- T01第二轮：pose、clock、面积与见证点、R/ε定义；源图unsupported和浮点切线限制同时继承
- T02首轮：cosine半球归一核、Gauss有限盘、矩形实体、门控分段；复制代码字节不改
- T03首轮：有限厚棱柱并集、厚度缓存包络和独立流式验证约束；只读，不扩展算法
- T05首轮：第二种等面积中点盘源求积；总率份额不是源面积
- T10首轮：电荷常数与离子量纲；不能把入射动能自动当吸收热量

这些研究代码不是第三方原文。读者包复制冻结代码，以便离线复算；原档目录不包含在允许列表。当前访问、权利和模型限定分别记录，不将“网上可读”等同“可任意再发布”。
