# 10 Cu 镀膜材料

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/metal_ge_material_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 光学角色与参考参数

Cu用于导电/反射/等离激元层时，需要同时关心反射率、吸收、氧化和附着。高热导块铜可以散热，不意味着几十纳米Cu膜具备同样面内/界面热性能。

| 参数 | 参考数值 | 对象/条件 | 来源与不确定度 |
|---|---|---|---|
| 理论密度 | 8.92 g/cm³ | 块料，测试温度未给 | M02；非膜有效密度 |
| 熔点 | 1083°C | 块料 | M02；目录近似值 |
| 热导率 | 400 W/(m·K) | 块料，温度未给 | M02；薄膜未知 |
| 线膨胀系数 | 16.5×10⁻⁶ K⁻¹ | 温区未给 | M02；非热应力许可值 |
| QCM Z ratio | 0.437 | 仪器材料起始参数 | M02；须与密度/tooling分别校准 |
| 10⁻⁴ Torr蒸气压温度 | 1017°C | 平衡源料参考值 | M02；不等于熔融工作点 |
| 弹性模量/膜应力/硬度 | 未核实统一值 | 沉积状态强依赖 | 不使用块料值代替薄膜 |

### 两组n,k为什么都可以有用

Johnson/Christy1972对象为室温真空蒸镀膜，厚18.5–50 nm；大部分谱域n,k估计误差小于0.02。数字化库实际覆盖0.1879–1.937 μm，不能把论文能量摘要范围自动扩充成文件有效域。[M05](https://doi.org/10.1103/PhysRevB.6.4370) McPeak数据是35 Å/s、基压3×10⁻⁸ Torr热蒸镀后从Si模板剥离的测面，文件范围0.3–1.7 μm。[M08](https://pmc.ncbi.nlm.nih.gov/articles/PMC4416469/)

| λ/μm | J&C n | J&C k | McPeak n | McPeak k | 处理方式 |
|---|---:|---:|---:|---:|---|
| 0.5500 | 1.00663 | 2.58231 | 0.797460 | 2.56420 | 各自数据内线性插值 |
| 0.6328 | 0.270023 | 3.40809 | 0.109265 | 3.58023 | 不交叉拼n和k |
| 1.5500 | 0.715760 | 10.6552 | 0.194332 | 10.9210 | 非统计置信区间 |

本表使用CC0数据；来源文件SHA256及取样方法与精度在数据文件中保留。现代薄膜可能有更低损耗，但“n更小”或“k更大”本身不是所有用途更优。应把n,k转换成对应器件指标。氧化Cu超薄膜研究也说明质量厚度与物理厚度可能明显不同；它不能被普通块铜模型解释。[M23](https://cpb.iphy.ac.cn/en/article/doi/10.1088/1674-1056/23/8/087802)

### 源和工艺选择

KJLC支持W/Mo舟或W篮热蒸发，也支持屏蔽Ta加热器内Al2O3坩埚；电子束用石墨或Mo衬里。选择需同时检查舟电阻/热负荷、填充与剩余料的几何、污染风险和换料重复性，不能按“能蒸出来”直接判定光学合格。[M02](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=cu1)

工程推论：Cu反射层若需Cr附着层，必须把Cr也放入光学模型，不能只用Cu的裸面R。空气老化和封装后的数据应分版本；见证片若被保护层封住而产品没有，两者不属于同一状态。12/25/35 nm、两种速率的原研究用AFM/XRD/XPS配合椭偏展示了厚度/微结构依赖，支持用组合计量而不是一个数据库常数。[M22](https://pmc.ncbi.nlm.nih.gov/articles/PMC8658243/)

### 工程算例

对空气入射、平整均匀、半无限Cu，R=[(n−1)²+k²]/[(n+1)²+k²]。632.8 nm得到J&C91.8348%、McPeak96.8889%。差5.05个百分点；不代表本机调整速率必然提高5.05个百分点，因为膜厚、测面、形貌和污染均不相同。1.55 μm时结果97.5420%与99.3560%，说明数据选择对预计损耗可比对R更敏感。两组都要进入候选设计的敏感性分析，实际选型由同批测得R/吸收与环境稳定性决定。

### 安全与缺口

KJLC Cu块料SDS2026-02-25列出长期水生生态危害并要求通风与合适防护；镀层残渣、抛光泥及清洗废液要收集，不能排入下水。[M17](https://www.lesker.com/msds/pdfs/BDFDDB1713FDE20B7EFD818AFABA1A11B9567B938D613A5122119BAAB801A6E2.pdf) 缺口：本机氧化层厚度、连续成膜阈值、附着层最小量、湿热后的R损失、IR实测k；本轮数据不覆盖10.6 μm Cu，不外推J&C或McPeak。

## 本卡证据入口

- [M02 KJLC Copper evaporation notes](https://www.lesker.com/newweb/deposition_materials/deposition-materials-notes.cfm?pgid=cu1)
- [M05 Johnson and Christy 1972 Optical constants of the noble metals](https://doi.org/10.1103/PhysRevB.6.4370)
- [M08 McPeak et al 2015 Plasmonic Films Can Easily Be Better](https://pmc.ncbi.nlm.nih.gov/articles/PMC4416469/)
- [M17 KJLC Copper pieces SDS 04570 revision20 2026-02-25](https://www.lesker.com/msds/pdfs/BDFDDB1713FDE20B7EFD818AFABA1A11B9567B938D613A5122119BAAB801A6E2.pdf)
- [M22 Copper nanolayer microstructure and optical constants 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8658243/)
- [M23 Oxidized Cu film constants by ellipsometry and transmission 2014](https://cpb.iphy.ac.cn/en/article/doi/10.1088/1674-1056/23/8/087802)
