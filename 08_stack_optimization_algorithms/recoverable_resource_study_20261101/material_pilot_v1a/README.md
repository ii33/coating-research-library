# 不同文献材料组合的可见光条件性测试

2026-11-01。固定 coating-sim 核心 131d3fc989c3dc9ac8d94fee3c39541a61b851df。离线参考设计生成实验，不是在线预测器，不给出预测误差或泛化达标宣称。

## 冻结任务矩阵

六组各六类任务，共 36 项。所有组合使用完全相同的目标、角度、偏振与预算。同一任务族共享随机整数种子，避免仅因组合名称不同改变随机序列；材料本身导致相位厚度、结构提案和优化轨迹不同。无配对重复种子统计，不把一次有限搜索差异归因于唯一因素。

| 组 | 候选低/高折射率材料 | 基片 |
|---|---|---|
| sio2_ta2o5 | SiO2 Rodríguez / Ta2O5 Rodríguez | 熔融石英 Malitson |
| sio2_tio2 | SiO2 Rodríguez / TiO2 Jolivet 非晶 | 同上 |
| sio2_hfo2 | SiO2 Rodríguez / HfO2 Bright | 同上 |
| mgf2_tio2 | MgF2 Rodríguez / TiO2 Jolivet 非晶 | 同上 |
| ybf3_zns | YbF3 Amotchkina 仅 n / ZnS Amotchkina n/k | 同上 |
| ybf3_zns_substrate | 同前组 | ZnS Debenham 块材 |

“低/高”是材料池排列约定，不假定全谱常数，也不使用真实材料名配造常数。完整光学组直接摘录固定核心仓库的光学目录或归档 provenance，原数据、单位、域、来源、工艺说明保留在各输入中；原文件和摘录组均记录 SHA256。不拼接不同工艺来源，不外推。HfO2 源表范围不是全域实测范围。数据库数值许可为 CC0，原论文权利另计。

| 任务族 | 原始指标（波长 nm） |
|---|---|
| ar | 450–700 R ≤ 0.015 |
| hr | 500–650 R ≥ 0.95 |
| mixed | 420–500 R ≥ 0.90；650–780 T ≥ 0.90 |
| bandpass | 420–480 R ≥ 0.85；550–620 T ≥ 0.85；700–780 R ≥ 0.85 |
| dual_ar | 420–500、650–780 R ≤ 0.02 |
| mean_mix | 420–500 平均 R ≥ 0.90；650–780 平均 T ≥ 0.92 |

全部角度为 0°、30°，非偏振，单前面、空气入射、半无限基片。除 mean_mix 外均逐点指标，比较包含等号；原始条件不可为通过而放宽。窗口在所选全部来源的共同计算域内，准备时逐材料逐目标在 513 点验证严格源采样。波段、角度和目标类型覆盖有限，不能声称涵盖红外、任意角度或实际用户四窗口任务。

## 吸收数据与条件性结论

所有输入显式设置 environment.assume_lossless=True，其核心语义仅为“完全缺失的 k 按零假设”，不清零已知 k，也不扩展局部 k 数据的有效域。

- 所有熔融石英基片和 ZnS 块材基片仅有 n，本轮其 k=0 是研究假设。
- YbF3 的这组可见光 n 模型缺少 k，亦是假设零；其红外 n/k 表不移用到可见光。
- SiO2、Ta2O5、TiO2、HfO2、MgF2、ZnS 膜的已知 k 保留。来源模型中的零也不等于已证实的工艺零吸收。
- 因此每组都是基片无吸收假设下的条件性结果；YbF3 两组另有膜材吸收不确定性。不可把组间结果直接说成化学材料性能排名。

已知吸收较大的来源可能在较严指标下找不到达标设计。没有找到仅记 unknown，不证明不可行，也不偷偷用零吸收重算替换。

## 参考算法和预算

复用 pilot_v4a 的有限参考流程，唯一协议改动是共享族随机种子与遵守显式未知 k 假设。0/2/4/8/12/16/24/32 起始层数；非带通为周期、修饰周期与随机三起点。带通由冻结核心纯结构生成器每族前 256 个候选的层数代表中选不超过 8 项，完整未评分起点在 input 内冻结；其生成不是达标证明。

局部拟合每窗 41 点、每起点最多 60 次函数评价；每任务 45 秒协作式修复预算，非硬实时截止。材料加载、起点准备、落盘等不能忽略为零成本。最多两个优化端点达标层数桶后进入两轮减量，每轮两提案。提前达标起点立即保存，即使随后端点失败也保留，但不计为端点成功桶。

单层厚度 1e-7–2 倍参考波长、起点层数上限等只是数值努力边界，不是制造约束或物理下界。32 倍独立原指标审计；通过设计立即持久化，成对选 N/D，评分 log(1+N)+log(1+D/参考波长)，同分按 N、D、物理哈希。有限网格审计不是连续证书，不含工艺容差保证。

## 冻结、发布和复算

在运行第一次搜索前，完整源码、文档、plan、所有 36 个输入、source manifest 必须发布并远端复读。各批结果及完整见证完成后发布、复读，再进入下一批。批次清单位于执行目录外的 material_pilot_v1a_checkpoints，不往冻结根中放多余文件。运行环境、线程、源码和输入摘要准入沿用已验证机制；先运行定向 unittest，再 prepare 和源存档。

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export COATING_CORE_REPOSITORY=/path/to/pinned/coating-sim
python -m unittest -v test_reference_contract test_pilot_admission test_material_contract
python run_pilot.py --repo "$COATING_CORE_REPOSITORY" prepare
# 完成远端源存档复读后，替换三个外部核验值并按组分批。
python run_pilot.py --repo "$COATING_CORE_REPOSITORY" run --workers 2 \
  --case material-sio2_ta2o5-ar \
  --verified-checkpoint <commit> --verified-plan-sha256 <sha256> \
  --verified-source-manifest-sha256 <sha256>
```

程序离线，提交参数不是程序自行证实的远端状态。结果恢复核对所有见证、设计/请求哈希、原审计和成对资源。未发现见证保持 unknown；不伪造最小资源或通过标签。

本目录为 v1a，仅修正未发布 v1 算法页的带通起点和端点停止说明；v1 未进行光学搜索。
