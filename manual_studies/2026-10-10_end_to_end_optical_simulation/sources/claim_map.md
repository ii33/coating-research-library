# 结论—来源证据链

`reported` 表示原稿作者如此报告；本包没有重开链接目标，不将其提升为独立交叉核验。`derived` 是工程建议，不是原始文献背书。来源索引的 `U/metadata_only` 仅表示本包的登记状态。

| 结论 ID | 结论 | 来源定位 | 状态/限制 |
|---|---|---|---|
| C-01 | 局部平行、各向同性膜堆的复 TMM 可作逐命中响应；不等于任意横向结构全波散射。 | [SRC-000001](index.md#src-000001) §§2–6；[SRC-000002](index.md#src-000002)；[SRC-000006](index.md#src-000006)；[SRC-000014](index.md#src-000014) §§3–5 | reported；实际材料/适用域待验证。 |
| C-02 | Poke 论文与源码展示射线/空间膜厚到 Jones pupil 的开放桥接；不等于完整开源几何入口。 | [SRC-000008](index.md#src-000008) §§2–5；[SRC-000011](index.md#src-000011)；[SRC-000012](index.md#src-000012) | reported；源码未运行。 |
| C-03 | Optiland 顺序薄膜/偏振功能不能外推成 NSQ 偏振薄膜闭环；各稿的版本快照不同。 | [SRC-000019](index.md#src-000019)、[SRC-000022](index.md#src-000022)；[SRC-000065](index.md#src-000065)、[SRC-000076](index.md#src-000076) | reported；提交/日期分别绑定，不合并成单一版本事实。 |
| C-04 | Mueller/Stokes 可表示偏振统计输运，但不能恢复 Jones 公共相位或空间间互相干。 | [SRC-000001](index.md#src-000001) §2；[SRC-000008](index.md#src-000008) §§2–3；[SRC-000024](index.md#src-000024)；[SRC-000053](index.md#src-000053) | reported；V符号和基约定待对照代码测试。 |
| C-05 | HCIPy/Prysm 的波动/偏振/GPU范围各有版本边界；文档不证明本机性能。 | [SRC-000028](index.md#src-000028)、[SRC-000031](index.md#src-000031)、[SRC-000032](index.md#src-000032)、[SRC-000038](index.md#src-000038) | reported；目标调用子集待回归。 |
| C-06 | PSF/OTF与探测器要区分绝对响应、归一化、像素面积、光谱测度和 QE。 | [SRC-000046](index.md#src-000046)、[SRC-000055](index.md#src-000055)、[SRC-000056](index.md#src-000056) | reported/derived；无传感器校准，不宣称 EMVA 符合。 |
| C-07 | Mitsuba `thindielectric`/普通 `dielectric` 不等价任意多层相干膜/色散闭环。 | [SRC-000062](index.md#src-000062)、[SRC-000063](index.md#src-000063)、[SRC-000077](index.md#src-000077) | reported；源码未运行。 |
| C-08 | PBRT-v4光谱 SampledSpectrum 不是 Stokes；PBRT/Raysect作标量参照，不是偏振全链。 | [SRC-000064](index.md#src-000064)、[SRC-000069](index.md#src-000069)、[SRC-000070](index.md#src-000070)、[SRC-000073](index.md#src-000073) | reported；平台/许可证逐版确认。 |
| C-09 | BRDF/BTDF需有光谱、角度、偏振基、镜面峰和校准条件；RMS粗糙度不能唯一规定散射尾部。 | [SRC-000083](index.md#src-000083)、[SRC-000084](index.md#src-000084)、[SRC-000085](index.md#src-000085) | reported；用户实测数据缺失。 |
| C-10 | 弱鬼像采样需概率补偿、独立批次/父样本误差；零命中不表示零贡献。 | [SRC-000079](index.md#src-000079)、[SRC-000080](index.md#src-000080)、[SRC-000081](index.md#src-000081) | reported/derived；概率界仅在其独立抽样条件内。 |
| C-11 | 按用途组合候选：Optiland顺序设计、Prysm/HCIPy波动成像、Mitsuba/Dr.Jit自定义非顺序、PBRT/Raysect标量对照。 | [SRC-000019](index.md#src-000019)、[SRC-000028](index.md#src-000028)、[SRC-000065](index.md#src-000065)、[SRC-000093](index.md#src-000093)–[SRC-000101](index.md#src-000101) | derived；不是统一现成全链。 |
| C-12 | 建议边界为厚度采样、膜层响应、偏振输运、波前导出/传播、光谱探测器和非顺序路径统计。 | 三份原稿的工程建议，无外部来源验证产品接口 | derived；建议占位名，不是产品API。 |
| C-13 | 4070 Ti SUPER/16 GB/32 GB为稿件给定预算，不是实测性能。 | 研究稿2/3及3/3，无外部数据 | reported；无本机基准。 |
| C-14 | 透明端口 `n cosθ` 通量简式与一般端口导纳须按振幅域分派。 | [SRC-000001](index.md#src-000001) §§2–4；[SRC-000077](index.md#src-000077)；原稿1 §2.4、原稿3 §3.2 | reported/derived；吸收端口和 s/p 导纳待数值裁定。 |
| C-15 | 本包 `U/metadata_only` 不覆盖原稿作者的核验级别/命题状态。 | 三份原稿的声明与本包来源登记规则 | derived；后续复核逐条升级。 |

## 待裁决项

1. Jones/Mueller：原稿一给出 V/coherency 候选，原稿三要求固定 Pauli 顺序与 V；没有明确物理冲突，但未对照目标代码。暂不宣布库间一致。
2. 功率归一化：`n cosθ` 用于相应透明端口简式；一般吸收端口按切向场与端口导纳/Poynting定义，需专门样例核对。
3. Optiland：`e73c5ff…`、`4e893f…`及动态 stable/dev 文档是不同快照；逐条声明留在各自版本，不合成同一版本能力。
4. 候选库职责：Optiland顺序设计，Prysm/HCIPy波动成像，Mitsuba/Dr.Jit自定义非顺序，PBRT/Raysect标量对照，是不同用途的组合建议，不互相替代。
5. TMM膜堆内相干多次反射与宏观面间鬼像分开计算，避免重复计能量/相位。

这些项在锁定目标版本、基/单位并完成数值或来源复核前，保持 `unverified`/待裁决。
