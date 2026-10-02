# 13 ZnS 基片

T04第一轮，2026-10-02。独立卡片由[证据分册](../reports/fluoride_sulfide_substrate_cards.md)提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。

### 4.1 身份、制备与等级

两类都叫ZnS，但标准CVD/FLIR一般为未HIP的多晶材料；多光谱等级在CVD之后经HIP处理以降低散射、改善可见/中红外使用。**Cleartran是特定产品名，不应给所有“多光谱ZnS”自动贴同样数值**。[IR15,IR16,IR17] 膜材颗粒的纯度、密度和n不能用来验收毫米级窗口。

### 4.2 光谱与厚度卡

| 数据 | 标准ZnS | 多光谱/Cleartran | 条件/来源 |
|---|---|---|---|
| 10%透过率边界 | 1.0–14 µm | 0.37–14 µm | Hellma，厚6 mm，阈值明确；未镀膜状态应随图/订单确认 [IR15] |
| n@1.014 µm | 2.29165 | 2.29165 | Hellma表；即使n相同，散射仍可能不同 |
| n@4 / 10 / 13 µm | 2.25231 / 2.20084 / 2.15252 | 同左 | 目录值；未给温度与误差 [IR15] |
| α@10.6 µm | 0.2 cm⁻¹ | 0.2 cm⁻¹ | Hellma，不能假定HIP消除此长波吸收 |
| α@3.8 µm | 0.02 cm⁻¹ | 0.0006 cm⁻¹ | 标准Crystran、MS多源一致 [IR16,IR17] |
| α@9.27 µm | 未列 | 0.006 cm⁻¹ | Hellma/Crystran [IR15,IR16] |

没有完整k谱。可在单个已知α点计算k=αλ/(4π)：10.6 µm、α0.2 cm⁻¹对应k≈1.69×10⁻⁵；3.8 µm、α0.0006 cm⁻¹对应k≈1.81×10⁻⁸。这是**单位转换的派生值**，误差继承α，并非增加有效数字。近可见散射不能塞入材料本征k里。

### 4.3 热、力学与冲突表

| 参数 | 标准CVD | Cleartran/HIP | 条件/证据 |
|---|---:|---:|---|
| 密度 | 4.09 | 4.09 g/cm³ | 298 K [IR15] |
| 晶粒 | 2–8 | 20–35 µm | Hellma牌号典型 [IR15] |
| CTE@273 K | 6.6 | 6.3×10⁻⁶ K⁻¹ | Hellma [IR15]；MS其他资料6.5并非同条件 |
| 导热@298 K | 16.7 | 28.4 W/(m·K) | Hellma [IR15]；Crystran MS为27.2 [IR16] |
| 比热 | 469 J/(kg·K) | 515 J/(kg·K) | Crystran，温度未在该行列明 [IR16,IR17]，不与Hellma不同温点混并 |
| E | 74.5 | 74.5 GPa | Hellma；误差未列 [IR15] |
| ν | 0.29 | 0.28 | 同上 |
| 四点弯曲破坏强度 | 103 | 75 MPa | Hellma，几何/统计分布未列；不是设计许用应力 [IR15] |
| Knoop，50 g | 200–235 | 160 kgf/mm² | Hellma [IR15] |
| Knoop，50 g，冲突来源 | 160 | 240 | Crystran [IR16,IR17]；**不得平均，不能用于等级硬度排序** |
| dn/dT@3.39 µm | 4.3×10⁻⁵ | 3.87×10⁻⁵ K⁻¹ | Hellma，298–358 K [IR15] |

Crystran MS纸版还列“apparent elastic limit”68.9 MPa，当前网页26.9 MPa，且名称与四点弯曲强度不同；全部隔离于设计许用值之外。[IR16] 数值冲突不阻止研究，但阻止结构放行。

### 4.4 加工/镀膜接口与失效

- HIP改善光谱不代表机械指标全面提高；对压差窗口优先看有统计基础的弯曲强度、表面缺陷与边缘支撑，不能只比较硬度。
- 采购必须写标准CVD还是HIP/MS、厚度、通光口径、T(λ)阈值、散射/均匀性、允许夹杂与表面缺陷；有可见共光路时必须实际测可见散射，不能以10 µm透过率替代。
- 镀膜热预算应受基片、夹具、胶和已镀层共同限制。Crystran提醒空气中正常使用不超过250°C；这不是证明真空更高温安全的实验。[IR16,IR17]
- 清洗、离子轰击、保护层会影响表面化学、微裂纹、散射与附着；蒸发膜的基片温度窗口不能直接当块材热冲击限制。曲率、透过波前、划伤、湿热、擦拭和夹具压紧应分项目验收。
- 官方数据表存在排版风险：Crystran旧PDF 9 µm的n重复8 µm值，现网页/Hellma为2.21290；本文用交叉一致值，不静默修补整表。[IR15,IR16]

### 4.5 选型算例

5 mm窗在3.8 µm，标准α=0.02 cm⁻¹时内部透过率exp(−0.02×0.5)=99.00%；MS α=0.0006时为99.97%。这还没有加散射，MS在可见共轴对准的优势也未体现在此算式。到10.6 µm，两者若α均0.2 cm⁻¹，5 mm内部透过率都仅90.48%。因此“升级MS”不能替代长波吸收/热载荷计算；可见透过、机械裕量、厚度及成本应一起权衡。

### 4.6 安全与未决

官方ZnS FLIR与MS SDS入口分别保留。[IR04,IR18] 磨削粉尘和酸接触风险必须纳入工序；CVD生产使用的H₂S不意味着已加工窗口会在正常条件自行持续放气。未决项：供应商批次强度统计、温度依赖n/k、雨蚀/砂蚀、实际镀膜界面强度、目标波段散射。不能拿目录强度直接校核高压窗口。

## 本卡证据入口

- [IR04 Crystran Zinc Sulphide FLIR Optical SDS](https://www.crystran.com/media/wysiwyg/MSDS/zinc-sulphide-flir-zns-msds.pdf)
- [IR15 Hellma Materials CVD Zinc Sulfide and Cleartran](https://www.hellma-materials.com/wp-content/uploads/2024/11/ZincSulfide_Cleartran.pdf)
- [IR16 Crystran Zinc Sulphide Multispectral product page and datasheet](https://www.crystran.com/optical-materials/zinc-sulphide-zinc-sulfide-multispectral-zns/)
- [IR17 Crystran Handbook — Zinc Sulphide FLIR materials data](https://www.crystran.com/media/wysiwyg/PDF/Handbook_2023_website.pdf)
- [IR18 Crystran Zinc Sulphide Multispectral Optical SDS](https://www.crystran.com/wp-content/uploads/2025/09/zinc-sulphide-multispectral-zns-msds.pdf)
