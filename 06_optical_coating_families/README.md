# T06 各类光学薄膜与应用

近红外、MWIR/LWIR、多光谱优先项的首轮手册与可复算膜系图谱，2026-10-02。范围来自原需求第10行；继承T04材料条件与T05源/厚度接口。当前交付为公开证据与参考数值包，不含本机实测、量产处方或损伤/环境资格。

## 先读什么

1. [应用需求与膜类图谱](reports/01_requirements_and_family_atlas.md)：选择AR、HR、滤光、分色和分束的条件
2. [AR与窗口](reports/02_ar_and_window_engineering.md)：单层/多层/双带、体吸收和背面
3. [介质与金属镜](reports/03_dielectric_and_metal_mirrors.md)：高反、吸收、保护层和损伤边界
4. [带通、边缘与陷波](reports/04_filters_edges_and_cavities.md)：有限带宽、远带阻挡及测量假象
5. [多光谱分色与分束](reports/05_multispectral_dichroics_and_splitters.md)：45°、偏振和两面协同
6. [六组可运行起始膜系](reports/06_reproducible_starter_atlas.md)：完整层序、厚度、输入出处、代码边界
7. [制造、验收与接口](reports/07_manufacturing_acceptance_and_interfaces.md)：从单层计量走向实件
8. [失败与未决证据](reports/08_failures_and_open_evidence.md)：哪些结果不能外推

## 直接复算

```sh
cd 06_optical_coating_families
python models/run_atlas.py
python -m unittest discover -s tests -v
python models/check_package.py
```

仅需Python≥3.10与NumPy≥2.0。已冻结输入可离线运行，不需论文原件。`build_atlas_inputs.py`是可选的T04来源重建，需要本地Al CC0原件；不属于普通读者复算前提。`render_chart_previews.py`是可选Pillow图像预览，不是数值依赖。

## 可复用交付

- [有限带宽结果简表](reports/06a_generated_metrics.md)，[全指标JSON](data/finite_band_metrics.json)
- [6组完整膜系JSON](data/starter_stacks.json)，[逐层物理厚度CSV](data/starter_layer_table.csv)
- [12组带证据/假设的材料代理](data/material_proxies.json)，[6组光谱CSV](data/spectra/)
- [总R/T/A谱图](figures/01_spectral_atlas.svg)，[角度/偏振谱图](figures/02_angle_polarization.svg)
- [24条来源登记](data/source_registry.json)，[逐来源摘要](sources/README.md)
- [6个核心文献实测案例及第7个补充反例](sources/summaries/verified_literature_cases.md)
- [设计需求接口](data/design_request_template.json)，[T07移交](T07_HANDOFF.md)
- [本轮验收与边界](reviews/ROUND1_ACCEPTANCE.md)，[测试日志](reviews/test_output.txt)

## 三个必须带走的结论

双低反射谷不等于双宽通带；滤片中心高T不等于深阻带；低前表面R不等于高整片透射。六组例子有可调起点也有刻意保留的失效，全部与真实文献样片分开。材料未知k、基片α、环境/损伤未测项不自动置零。

原始第三方论文未下载/再分发；合法原件留本地的规则继续遵守。公共同步、全局状态、T07启动由项目协调统一处理。本专题未推送、未改其他专题、未写产品代码或操作设备。
