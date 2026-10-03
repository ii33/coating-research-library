# 独立光学量纲核查（窄复核）

## 范围与结论

只核查 `models/process_optics.py`、`models/inference.py`、`models/batch_driver.py` 与本包冻结核 `models/vendor/optics_kernel.py` 的指定接口。新加 7 个单波长/小阵列 spot checks；未改实现、未运行上游整套测试、未做大扫描、未做设备或实物验证。

在这些有限检查点内，量纲、复振幅符号、有限不相干基片多次往返能量分配和散射导致的镜面缺额均与独立公式相符；本复核未发现阻断性偏差。实际未测记录保持阻断，批处理默认保持 `plan_only`。

## 核查与复现

1. **原子面密度 → 面质量 → 几何厚度。** 独立按 `N_atoms/m² × M_kg/mol ÷ N_A` 计算面质量，再按 `面质量/ρ × 10⁶` 转成 µm。合成 Al 夹具给出 `6.026261271943406×10²¹ atoms/m²`、约 `2.70×10⁻⁴ kg/m²`、`0.100 µm`。同一记录的 QCM 等效厚度约 `0.333333 µm`、设计厚度 `0.25 µm`，三者未混作工作片膜厚。

2. **`n+ik` 符号。** 在约定 `exp(-iωt)` 下，膜内传播因子为 `exp(+i2πNd/λ)`，其模为 `exp(-2πkd/λ)`。用单层 Fresnel 复振幅独立手算反射，与本包冻结 vendor 核在 `0.55 µm` 的单点结果相符；被动正 `k` 对应衰减，不是增益。测试不加载兄弟目录的 T07 文件，也不把同一核与自身比较作为独立证据。

3. **体吸收 α 与消光系数 k。** 单位恒等式为 `k = α_per_m × wavelength_um × 10⁻⁶ /(4π)`；例如 `α=25000 m⁻¹`、`λ=0.55 µm` 得 `k≈0.00109433`。`alpha_to_k` 在 bulk→film scope 不同的调用上阻断。基片体吸收按 `p=exp(-αL/cos θ_sub)` 单独进入有限基片模型，没有被当成膜的 `k`。

4. **有限、不相干基片多次往返。** 令前向膜堆为 `(Rf,Tf,Af)`，反向膜堆为 `(Rr,Tr,Ar)`，后表面为 `(Rb,Tb)`，基片单程功率衰减为 `p`，`D=1−Rr·Rb·p²`。独立比较采用：

   - `R=Rf + Tf·Tr·Rb·p²/D`
   - `T=Tf·Tb·p/D`
   - `Afilm=Af + Tf·Rb·p²·Ar/D`
   - `Abulk=Tf·(1−p)·(1+Rb·p)/D`

   对合成单层、`0.55 µm`、35° p 偏振及非零基片 α 的检查中，调用本包冻结核取得前向/反向堆叠及后表面的单程功率系数；有限基片的全往返合成与吸收分配由测试独立手算，再与代码四项比较。结果相符，并满足 `R+T+Afilm+Abulk=1`（数值容差 `1e-12`）。该公式覆盖所有强度往返；它的适用域仍是模型注明的实数基片界面与非相干强度合成，并非吸收界面的通用相干解。

5. **镜面缺额包含散射。** 检查 `S=fr·R+ft·T`、`Lspec=1−Rspec−Tspec=Aabs+S`，以及探测值按漫散射收集率回加。`Afilm+Abulk` 保持为吸收分量，未将未收集散射记作吸收。

6. **未知实际量与默认执行状态。** `actual_unmeasured.json` 返回 `blocked_unknown_or_inapplicable`，不产生 R/T 数值或生产资格声明。真实默认批计划的非执行调用只返回 `plan_only`，不含 `runs`，并标明无自动 GPU、设备验证或物理实验。

`inference.py` 仅作接口级阅读：预测经 `evaluate`，被阻断的情形不会作为正常条件计算返回；`fit_synthetic` 明确限制合成数据。未独立审查优化、协方差推断或拟合稳健性。

**核来源与独立性说明：** 本包冻结核 `models/vendor/optics_kernel.py` 对应来源 `07_thin_film_design_theory/models/optics_kernel.py`；其与稳定 T07 核的逐字哈希对照由现有 `data_qa` 记录负责，本窄复核未重做来源哈希验证。该哈希核查是来源/继承关系的证明，不是独立光学推导；本复核的独立性来自明确写出的 Fresnel 公式与有限基片强度多次往返公式手算。有限基片计算调用冻结核仅提供单程散射系数，不会将核与其自身的结果对比冒充独立验证。

## 验证

仅运行新增测试：

```text
python -m unittest discover -s tests -p 'test_independent_optical.py' -v
Ran 7 tests in 0.060s — OK
```

新增文件：`tests/test_independent_optical.py`、`reviews/independent_optical_check.md`。该项目副本无可识别的 Git 元数据，因此未提供 Git diff 状态。

## 边界声明

这是 GPT-6 Luna 完成的窄量纲/光学核复核，不是 Seed 或 Sol 的完整独立审查，不是全面软件审计、材料适用性验证、制程校准、实物/仪器验证或设备验证。结果只支持上述合成点位和公式的有限交叉核验；未知材料状态、实际 n/k/α、散射、密度与量测条件仍需相应证据。
