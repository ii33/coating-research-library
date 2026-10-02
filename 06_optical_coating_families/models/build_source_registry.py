#!/usr/bin/env python3
"""Build concise citation registry and source summaries; no original-paper copying."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
# id,title,url,class,locator,evidence,limits
rows=[
('F01','Byrnes, Multilayer optical calculations (arXiv:1603.02720v5)','https://arxiv.org/html/1603.02720v5','primary_author_methods','§§3–6, Appendix B/D','Fresnel/TMM功率与相位约定、厚层非相干边界；本册参考代码独立实现并做解析/递归校核','方法论文不证明本册材料数据或实件性能；HTML页显示日期与版本头不一致，引用版本号'),
('F02','Edmund Optics, Anti-Reflection (AR) Coatings','https://www.edmundoptics.com/knowledge-center/application-notes/lasers/anti-reflection-coatings','manufacturer_application_note','AR types / coating curves','AR类型与有限带宽用途背景；不把商品目录曲线当本册膜系复现','无可复制完整工艺处方；典型曲线不是特定批次验收'),
('F03','Edmund Optics, Optical Filter Orientation, AOI and Cone Half Angle','https://www.edmundoptics.com/knowledge-center/application-notes/optics/optical-filter-orientation/','manufacturer_application_note','orientation / AOI / cone-half-angle sections','滤片照向、AOI和光锥的条件化影响','标记约定属具体产品；不能推广所有供方'),
('F04','Semrock / IDEX, Introduction to Bandpass Optical Filters','https://www.idex-hs.com/resources/intro-to-optical-filters/intro-to-bandpass-optical-filters','manufacturer_application_note','Bandwidth / OD / AOI sections','FWHM与保证带宽区别、阻带与通带定义','厂商定义不构成本机制造能力证据'),
('F05','Semrock Optical Filters FAQs','https://semrock.com/contact/contact-us/faqs/optical-filters-faqs','manufacturer_measurement_note','spectral measurement: feature rounding / noise floor / sideband kink','有限带宽、噪声底、旁带伪影的验收提醒','不是通用仪器误差预算；不替代设备校准'),
('F06','LAYERTEC, Optical Coatings Catalogue','https://www.layertec.de/downloads/LAYERTEC_Catalog.pdf','manufacturer_technical','Metallic coatings and protective layers, printed p162','金属和保护层的光学/化学功能区分','厂商寿命与工艺描述不外推本例；未存原PDF'),
('F07','Amato et al. High-Reflection Coatings for Gravitational-Wave Detectors (2018)','https://doi.org/10.1088/1742-6596/957/1/012006','primary_experiment_inherited_T04','Table1, T04 OX-07; OXP-006/OXP-028','1064nm Spector IBS Ta2O5 n=2.08、SiO2 n=1.474的条件化锚点','仅从已审T04继承；行对应退火状态未完全明示；冻结宽谱不是原文'),
('F08','Merck/EMD, Zinc Sulfide Patinal Product Information','https://www.emdgroup.com/Products/PM/us/ZnS_tcm2080-us.pdf','manufacturer_technical','2019-08, p2 wavelength/n table','ZnS蒸发膜n离散表；IR组合用途；本册使用2–13µm若干点','表无k/不确定度；k=0属本册假设；原厂吸收自由措辞不作计量结论'),
('F09','Merck/EMD, Ytterbium Fluoride Patinal Product Information','https://www.emdgroup.com/Products/PM/us/101601_YbF3_tcm2080_127462-us.pdf','manufacturer_technical','2019-08, p2 n/k table','YbF3条件化n/k点；本册仅在2–5µm点间用于MWIR代理','稀疏插值不能解析水峰；不等于YF3；工艺/误差未齐'),
('F10','Merck/EMD, Magnesium Fluoride Patinal Product Information','https://www.emdgroup.com/Products/PM/us/MgF2_EMD_2022.pdf','manufacturer_technical','2023-01 document; optical table; T04 IRP-037/038','1.5µm膜n=1.375、k<2e-5参考','上限不是零；不定义全波段/所有沉积法'),
('F11','Rahmlow et al. Dual band antireflection coatings for the infrared (2008)','https://www.corning.com/content/dam/corning/media/worldwide/csm/documents/Dual_band_antireflection__Rahmlow.pdf','primary_measured_case','DOI10.1117/12.780288; pp5–7 Tables1–3 Figs22–25','Ge/ZnSe双带AR实件；总外透过与模型分开','完整逐层处方未披露；ZnSe实测样片二/三材料归属不明；不延伸8–14µm'),
('F12','Papatzacos et al. Temperature resistant AR on Si-wafer (2023)','https://pmc.ncbi.nlm.nih.gov/articles/PMC10172777/','primary_measured_case','DOI10.1016/j.heliyon.2023.e15888; Table1 §§1.1–1.3 Figs2/4/5','MgO/ZnS/YF3明确物理层序及300°C1h热暴露','Table1与正文厚度有差异；YF3不是YbF3；未证明长期寿命'),
('F13','Jiang et al. NIR to LWIR Dichroic Beamsplitter (2024)','https://www.mdpi.com/2079-6412/14/2/235','primary_measured_case','DOI10.3390/coatings14020235; Tables1–3 Figs5/6 §2.3','45°NIR反射/中长波透射及环境试验；Table1为背面AR','前面完整处方、背面表方向、偏振/基片厚度未核齐；直接抓取429，使用可读论文副本/索引全文'),
('F14','Boccas et al. Protected-silver coatings for Gemini mirrors (2006)','https://doi.org/10.1016/j.tsf.2005.07.295','primary_measured_case','Thin Solid Films502,275–280; §§1.3,3–4 Figs3–5','四层保护银物理处方；实测反射/发射与耐久研究','99.1%是早期可行性，不是所有后续镜；AOI/偏振、完整n/k未齐'),
('F15','Zhu et al. Wide-Angle Depolarizing Reflector at1064nm (2023)','https://pmc.ncbi.nlm.nih.gov/articles/PMC10303084/','primary_measured_case','DOI10.3390/ma16124258; §3.4 Fig7; Supplement TableS1','Ta2O5/SiO2宽角HR的测量及模型区分','完整S1厚度未取得；depolarizing非随机偏振；BK7非K9'),
('F16','Liu et al. Infrared PBS with ZnSe compensation layers (2024)','https://doi.org/10.1364/OE.515751','primary_measured_case','Optics Express32,10910–10924; §§2–3 Fig7 Table4','45°Ge/ZnSe/YbF3 PBS；实测Tp和透射消光比','光学厚度系数非nm；全物理层表/背面未取齐；367nm为设计带宽'),
('F17','Yu et al. Ultrathin Ge-YF3 AR (2024)','https://doi.org/10.1515/nanoph-2024-0360','primary_measured_case_optional','Nanophotonics13,4067–4078; §§2,4.2–4.3 Figs3–5','单面模型0.54%与双面实测3.31%的重要区别','重优化/实测层厚未取全；方向需复核；不复现标题性能'),
('F18','Frey, Leviton and Madison, Temperature dependent n of Si and Ge','https://arxiv.org/abs/physics/0606168','primary_experiment_inherited_T04','Tables6/7/9; T04 MP-054–056','Ge295K、3/4/5µm的n点和指定不确定度','块材不是Ge膜；无k；只继承T04核验点，未独立再测'),
('F19','Crystran, Germanium optical crystal data','https://www.crystran.com/optical-materials/germanium-ge/','manufacturer_technical_inherited_T04','T04 M10, MP-057/062','11µm n=4.0026和10.6µm条件化吸收界限','两个λ不能混称精密同波长测量；温度/掺杂需核'),
('F20','CDGM H-K9L optical glass datasheet517642','https://www.cdgmgd.com/webapp/pdf/H-K9L.pdf','manufacturer_technical_inherited_T04','single-page n/internal-T tables; T04 IR19','特定牌号n及5/10mm内部透过','不是所有K9/N-BK7；不能外推MWIR/LWIR'),
('F21','Hellma Materials, CVD ZnS and Cleartran','https://www.hellma-materials.com/wp-content/uploads/2024/11/ZincSulfide_Cleartran.pdf','manufacturer_technical_inherited_T04','2020-01, p3 comparison; T04 IR15','标准级/多光谱级必须区分，透过有厚度/阈值条件','目录不能替代逐批散射、强度或整件保证'),
('F22','Crystran, Zinc Selenide optical material data','https://www.crystran.co.uk/optical-materials/zinc-selenide-znse/','manufacturer_technical_inherited_T04','Refractive Index / Product Data; T04 IRP-085','ZnSe n@10.6µm=2.4028供代理锚点','完整k/温度/批次不确定度缺失，不推损伤阈值'),
('F23','Rakić, Intrinsic optical constants of aluminum (1995)','https://doi.org/10.1364/AO.34.004755','primary_optical_model_inherited_T04','Applied Optics34,4755; T04 M07/Al_Rakic dataset','Al复折射率来源；CC0数字化数据经9点重采样','本征重建非单一生产薄膜；不含氧化粗糙；原数据本地专存'),
('F24','Brattain and Briggs, Optical constants of Ge (1949)','https://doi.org/10.1103/PhysRev.75.1705','primary_experiment_inherited_T04','T04 M15 and Ge film card; historical film n>6µm','历史蒸镀Ge膜约n4.3，供LWIR教学冻结值','不是现代工艺；无可用于本例的完整k/热参数，不能外推至MWIR')]
sources=[]
for id,title,url,typ,loc,evidence,limits in rows:
 d=dict(id=id,title=title,url=url,source_class=typ,locator=loc,checked_at='2026-10-02',supported_claims=evidence,limitations=limits,access_basis='T04 evidence inherited with local cards' if 'inherited' in typ else 'read-only primary/vendor source verification',original_archival_status='not_downloaded; summaries and necessary factual data only',redistribution='no full original in publication',summary_path=f'sources/summaries/{id}.md')
 sources.append(d)
 (ROOT/d['summary_path']).write_text(f'# {id} · {title}\n\n- 来源：[{title}]({url})\n- 类型：{typ}\n- 定位：{loc}\n- 核验日期：2026-10-02；{d["access_basis"]}\n\n## 可支持的事实\n\n{evidence}\n\n## 适用边界与缺口\n\n{limits}\n\n## 原文/权利\n\n本专题没有下载该原文；保存链接、原创摘要及必要事实。在线可读不自动等于可公开再分发。实测案例的细节见本册对应章节与`verified_literature_cases.md`。\n')
(ROOT/'data/source_registry.json').write_text(json.dumps(dict(schema_version='1.0',sources=sources),ensure_ascii=False,indent=2)+'\n')
print(len(sources),'source cards')
