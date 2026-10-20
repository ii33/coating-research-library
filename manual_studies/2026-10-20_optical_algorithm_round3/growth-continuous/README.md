# 连续厚度回修小试

2026-10-20。仅云端合成研究。结果见[中文结论](小试结论.md)。

复现：

    python run_continuous.py
    python -m pytest -q test_continuous.py

Python3.12，NumPy2.3.5，SciPy1.17.0，pytest9.1.1。数值主试验约17秒，仅共享云端实现量级。脚本路径均相对包目录，不依赖原产品仓库或网络。原核位于verified_kernel；SHA-256与上一阶段一致。

文件：

- run_continuous.py：原有限结构机制加连续全层SLSQP epigraph minimax回修，真实光谱/有限差分调用计费
- pilot/results.json：全部8轮、所有实际候选、层序膜厚、档案轨迹、局部精修记录、邻域事件和固定密采样审计；每个 run 完成后评估该 run 的检查点，不反馈后续搜索
- pilot/runs.csv、summary.csv：逐种子三个检查点及汇总
- test_continuous.py、test_report.txt：实际测试
- 小试结论.md：明确的“无新增收益，且算子尚未触发”，没有把未测当失败

本轮没有扩大种植谱目录。目标改为原双窗AR严格1%，明确未证明可行；另设4%可行校准，使用旧六层解作外部见证，不给搜索器。相同回修器改善了候选，但两方法在预算内完全同路径，没有触发停滞两编辑。按要求停止扩张。
