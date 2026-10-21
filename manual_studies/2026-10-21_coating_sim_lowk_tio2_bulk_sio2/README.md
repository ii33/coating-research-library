# TiO₂/MgF₂ 薄膜与块材 SiO₂ 研究（2026-10-21）

独立研究包；不属于 `coating-sim` 软件发布，也不改写原 ZnS/98% 基准。32、30、28 层在离散的 400–700 nm、0°/30°、s/p 条件下通过 98% 最低反射率目标；26 层本次失败。补充的无答案种子桥接验证也从来源对比推导子堆栈中心，在同一 32 层案例独立通过约 98.7355%，但尚不代表通用软件能力或已完成软件集成。28 层只是预设比较中最少通过者，裕量窄，不是全局最少层数证明。制造误差、散射、应力及粗糙度不在资格验证内。

材料：Franta TiO₂ 与 MgF₂ 薄膜的来源拟合 n,k 原样保留；仅 Malitson 块材熔融 SiO₂ 基底因来源仅给 n，明确采用 k=0 的半无限出射介质假设。拟合膜 k 不等于直接测得的超低损耗。处方按入射侧至基底排列。

- [完整中文总结](RESEARCH-SUMMARY.md)
- [来源、出处与数据许可](sources/lowk_tio2_source_provenance.json)
- [逐层处方 CSV](prescriptions/)
- [独立候选与稠密光谱审计](candidates/)
- [28/30/32 层冻结请求、材料快照、候选与生产审计](production/)
- [无答案种子通用先验桥接验证（单一案例）](generic-prior-bridge/README.md)
- [面向软件维护者的实现建议与限制](SOFTWARE-HANDOFF.md)

脚本复现需 `numpy`、`scipy` 及 `coating-sim` 源码。将 `COATING_SIM_ROOT` 指向干净的 `coating-sim` checkout，提交必须为 `0a631b7428486ab08fe0f27aa8938c50783f5280`；设置可写的 `COATING_RESEARCH_OUT` 目录，然后依次运行：

```sh
COATING_SIM_ROOT=/path/to/coating-sim COATING_RESEARCH_OUT="$PWD/runs/tio2-study" python scripts/tio2_research.py
COATING_SIM_ROOT=/path/to/coating-sim COATING_RESEARCH_OUT="$PWD/runs/tio2-study" python scripts/reduce_layer_count.py
```

输出写入独立研究目录，不会更改软件仓库。运行时间依硬件和负载而变；7.15 秒只对应本次明确的 440/625 nm、8+8 对先验与局部优化实现，不是通用自动合成能力或时间承诺。通用锚点调度仍为待验证建议。
