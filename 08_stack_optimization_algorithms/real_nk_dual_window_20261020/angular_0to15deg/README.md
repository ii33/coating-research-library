# 真实材料双窗 0–15° s/p：11 层推荐处方

研究ID：BMARK-REAL-NK-DUAL-20261020-ANGULAR-v1。仅固定来源模型内的独立数值研究。

**唯一推荐入口：[11层 CSV](recommended/final-prescription.csv) / [JSON](recommended/final-prescription.json)**。
总厚3871.098426 nm，从基片向空气排列。历史12层仅在history目录中追溯。

[总报告](REPORT.html)｜[第二独立验收](independent_review/REPORT.html)｜[完整验收摘要](independent_review/summary.json)｜[离线算法说明](algorithms.html)。

3–5/8–12 μm、空气侧0–15°含边界，s/p分别R≤0.99%、T≥90.01%，容差1e-6未用于放宽。
最大R0.756956100%，最低T97.280190605%；T指进入半无限ZnS通量，非成品整片透射。
未宣称连续域数学证明、全局最优或制造验收。

现有依赖为NumPy/SciPy/mpmath；最终光学复核独立于产品核心：
`python -B scripts/verify_angular.py --check-inputs-only`
仅核查包与数据身份，无光学评价。完整复算需显式`--output`指定包外空目录，详见[便携说明](PORTABILITY.md)。
科学函数源文本及AST与已接受的独立验收相同；仅改包内相对路径、CSV加载和输出边界。
发布整理未重新搜索，也未重复完整密网格计算。原完整独立验收结果与出处保留。
完整自动结构搜索依赖未发布v3核心，不在本包声称可独立重跑。
