#!/usr/bin/env python3
"""Freeze source cards from checked primary/official sources. No web requests."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[
('S01','Multilayer optical calculations','Steven J. Byrnes','2016; arXiv v5 revised 2020','10.48550/arXiv.1603.02720','https://arxiv.org/html/1603.02720v5','primary_author_methods','Full HTML; local public PDF','§§2–6; Appendices A/B/D','相位/复折射率、界面、吸收半空间、厚层非相干与物理分支可统一处理。用来交叉约束本册基本模型。','本册p切向E约定与其常用p基矢不同；HTML显示日期与版本元数据不同，以v5为准。不是材料或生产证明。','S01_byrnes_1603.02720v5.pdf'),
('S02','Basics of Optics of Multilayer Systems: selected chapters by A. V. Tikhonravov','Sh. A. Furman; A. V. Tikhonravov','1992',None,'https://optilayer.com/content/book_Furm_Tikh.pdf','primary_author_textbook','133-page author-site selection PDF read selectively; downloaded locally','§§1.1–1.6; §2.1 merit formulation; §2.2 needle-like variations','从分层电磁场到导纳、反向谱关系、灵敏度、周期镜、窄带腔和综合的一条教材主线。','使用exp(+iωt)及不同z方向，不能原样拼接本册符号；公开文件注明selected author chapters，不宣称整本已取得。','S02_furman_tikhonravov_selected_chapters.pdf'),
('S03','Improved Formulation of Scattering Matrices for Semi-Analytical Methods That Is Consistent with Convention','Raymond C. Rumpf','2011','10.2528/PIERB11083107','https://www.jpier.org/PIERB/pier.php?paper=11083107','primary_methods_paper','Publisher full PDF; downloaded locally','PIER B 35,241–261; scattering definition and cascade sections','一致端口定义与散射级联是分层计算的重要实现问题；本册标量星积独立推导。','原文含更一般多模问题和特定归一化。本册没有复现其效率比较，不用其多模矩阵替代标量定义。','S03_rumpf_2011.pdf'),
('S04','Matrix method for thin film optics','Leandro N. Acquaroli','2018; arXiv v1','10.48550/arXiv.1809.07708','https://arxiv.org/html/1809.07708v1','primary_author_methods','Full HTML; independent checker read v1 PDF','Eqs.11,21–34; scattering and periodic sections','为多种矩阵表示提供比较对象；本册用裸界面验证其振幅/功率归一化的成对关系。','Eq.30相对Eq.22有整体归一化不一致，30b含ω12自引用；不能将Eq.32当作本册未缩放t直接使用。',None),
('S05','Thin-Film Optical Filters, 5th edition','H. Angus Macleod','2017 copyright, publisher record',None,'https://www.routledge.com/Thin-Film-Optical-Filters-Fifth-Edition-5th-Edition/Macleod/p/book/9781138198241','primary_publisher_textbook_record','Publisher description and table of contents only','ISBN9781138198241; Basic Theory, Theoretical Techniques, tilted coatings and specifications','权威工程教材的范围覆盖理论、膜类、生产、材料、系统与规格；作为进一步系统阅读路线。','未取得商业全文；本册不以未读页码/公式或营销描述作技术证据。',None),
('S06','Equivalent Layers in Multilayer Filters','Alfred Thelen','1966','10.1364/JOSA.56.001533','https://opg.optica.org/josa/abstract.cfm?uri=josa-56-11-1533','primary_methods_paper','Official abstract and bibliographic record only','JOSA56(11),1533–1538','等效层用于多层滤光器的设计是原始理论路线之一。','全文本轮不可读；A=D、等效参数和W06是本册独立代数核验，不称论文处方复现。',None),
('S07','Gradient-index antireflection coatings','W. H. Southwell','1983','10.1364/OL.8.000584','https://opg.optica.org/ol/abstract.cfm?uri=ol-8-11-584','primary_methods_paper','Official abstract and bibliographic record only','Optics Letters8(11),584–586','将折射率梯度剖面作为宽带AR的设计自由度。','未取得完整剖面数据；本册smoothstep是原创合成例，不属于原文实测。',None),
('S08','Application of the needle optimization technique to the design of optical coatings','A. V. Tikhonravov; M. K. Trubetskov; G. W. DeBell','1996','10.1364/AO.35.005493','https://opg.optica.org/ao/abstract.cfm?uri=ao-35-28-5493','primary_methods_paper','Official abstract; full article marked Not Accessible','Applied Optics35(28),5493–5508','needle插入是一种改变层结构的设计路线，原论文讨论物理解释与应用经验。','公式深入依据作者开放章节S02和本册小厚度展开；T07不实现完整优化流程。',None),
('S09','Needle Optimization','OptiLayer GmbH','online documentation; retrieved 2026-10-02',None,'https://optilayer.com/automatic-design-options/needle-optimization/','official_software_documentation','Full relevant web text','Needle Optimization page; synthesis/refinement relation','未知层数和起始结构时，needle与refinement可配合；总厚度和终止准则仍需设定。','软件功能/供应商表述不是全球最优或性能证明；不采纳其营销式普遍能力声称。',None),
('S10','Theory of Double-Chirped Mirrors','Nicolai Matuschek; Franz X. Kärtner; Ursula Keller','1998',None,'https://ulp.ethz.ch/content/dam/ethz/special-interest/phys/quantum-electronics/ultrafast-laser-physics-dam/publications_awards/publications/1998/084__JSTQE_4__197__1998_.pdf','primary_methods_paper','Author university repository full PDF read selectively','IEEE JSTQE4(2),197–208; abstract and coupled-mode/matching discussion','双啁啾通过Bragg波数与耦合强度变化处理匹配问题，降低不期望反射造成的群延迟振荡。','本册只用理论思想，未复现其完整设计、实测反射和超短脉冲实验。',None),
('S11','Generalized matrix method for calculation of internal light energy flux in mixed coherent and incoherent multilayers','E. Centurioni','2005','10.1364/AO.44.007532','https://www.centu.it/30_generalized.pdf','primary_methods_paper','Author-hosted full PDF read selectively; publisher metadata crosscheck','Applied Optics44(35),7532–7539; flux and mixed coherence derivation','混合相干/非相干可以用内部能流建立统一记账。','本册仅实现受限的单非相干分隔体，不声称复现该文全部框架或太阳能器件实验。',None),
('S12','Correlation of errors in optical coating production with broad band monitoring','A. V. Tikhonravov; I. V. Kochikov; I. A. Matvienko; T. F. Isaev; D. V. Lukyanenko; S. A. Sharapova; A. G. Yagola','2018','10.26089/NumMet.v19r439','https://en.num-meth.ru/index.php/journal/article/view/986','primary_methods_paper','Official abstract and CC BY4.0 license; English PDF downloaded and opening inspected','Numerical Methods and Programming19(4), article439; abstract and references','监控会引入厚度误差相关性，评估需结合统计与制程模型。','原文特定分布结论不能移植为本机误差分布；W08高斯仅是说明协方差影响的情景。','S12_error_correlation_2018.pdf'),
('S13','NIST TN1297 Appendix A: Law of Propagation of Uncertainty','NIST; B. N. Taylor and C. E. Kuyatt, TN1297 authors','1994 technical note; official web presentation',None,'https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty','official_metrology_reference','Full official Appendix A web text','Eqs.A-1–A-3','一阶Taylor传播包含敏感度和输入协方差；本册写成JΣJ^T。','线性近似在驻点/强非线性处可能失效；不能从本公式推导未知量产分布。',None),
('S14','Robust Synthesis','OptiLayer GmbH','online documentation; retrieved 2026-10-02',None,'https://optilayer.com/robust-synthesis/','official_software_documentation','Full relevant web text','Robust Synthesis, monitoring dependence and design cloud','名义表现接近的设计可有不同制造灵敏度；稳健性依赖监控方案与误差情景。','供应商演示不构成本项目良率验证；没有照搬经验样本数作为通用收敛证书。',None),
('S15','Deposition and spectral performance of an inhomogeneous broadband wide-angular antireflective coating','V. Janicki; D. Gäbler; S. Wilbrandt; R. Leitel; O. Stenzel; M. Lappschies; B. Görtz; D. Ristau; C. Rickers; M. Vergöhl','2006','10.1364/AO.45.007851','https://fulir.irb.hr/1558/','primary_experimental_paper_repository','Author institution metadata/abstract and reprint-rights statement','Applied Optics45(30),7851–7857; repository abstract','同类混合渐变AR的多种沉积路线及重复性研究，支持设计与工艺映射需单独验证。','本轮没有提取该文完整层表/数值曲线，不以它认证本册合成GRIN的可制造性。',None),
('S16','tmm: tmm_core.py and manual','Steven J. Byrnes','author repository; retrieved 2026-10-02',None,'https://github.com/sbyrnes321/tmm/blob/master/tmm_core.py','primary_author_software','Public source portions read; no import or execution','coh_tmm, T_from_t, power_entering, inc_tmm','作者实现区分R/T、净入射功率及相干/非相干数据；与S01提供可继续核查的外部实现。','master未冻结；本册未安装或调用外部tmm，不能声称做了独立软件包运行对照。',None),
('S17','Cone Angle','OptiLayer GmbH','online documentation; retrieved 2026-10-02',None,'https://optilayer.com/optilayer-tools/cone-angle/','official_software_documentation','Full relevant web text','Biconical transmittance and angular weighting formulas','角光锥积分必须指定分布和立体角权重，均匀与Lambertian不同。','功率角平均不能替代相干焦场；软件推荐点数不直接当作本项目精度保证。',None),
('S18','Phase/GD/GDD Targets','OptiLayer GmbH','online documentation; retrieved 2026-10-02',None,'https://optilayer.com/optilayer-tools/optilayer-provides-a-large-variety-of-design-targets/phase-gd-gdd-targets/','official_software_documentation','Full relevant formulas read','Phase, GD and GDD target polynomial expressions','相位/GD/GDD需要一致符号和频率定义；适合做本册约定转换反例。','可见GD展开缺少由其相位式应导出的GDD·Δω项；只记录网页不一致，不推断内部软件错误。',None)
]
sources=[]
for row in rows:
 sid,title,authors,year,doi,url,kind,access,loc,summary,limit,local=row
 item=dict(id=sid,title=title,authors=authors,year=year,doi=doi,url=url,source_type=kind,
           checked_on='2026-10-02',read_extent=access,locator=loc,summary=summary,limitations=limit,
           summary_path=f'sources/summaries/{sid}.md',local_original=local,
           original_archival_status='public author/publisher copy downloaded for local research only; excluded from published package' if local else 'link and original summary only; no local original claimed')
 if local:
  f=ROOT/'sources/originals'/local
  item['sha256']=hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
  item['bytes']=f.stat().st_size if f.exists() else None
 sources.append(item)
 text=f'''# {sid} · {title}

- 作者/机构：{authors}
- 年份/版本：{year}
- 官方或作者来源：[{title}]({url})
- DOI：{doi or '未在本轮登记；不猜填'}
- 类型：{kind}
- 核验日期：2026-10-02
- 实际读取范围：{access}
- 定位：{loc}

## 原创摘要与本册用途

{summary}

## 条件、限制与证据等级

{limit}

## 原文与权利

{item['original_archival_status']}。原文著作权保留，不因公开可读而宣称可公开再分发；公开交付仅包含链接、原创摘要和自主推导/计算。个人研究副本位于本地排除目录，目录规则和哈希另行记录。
'''
 (ROOT/item['summary_path']).write_text(text)
(ROOT/'data/source_registry.json').write_text(json.dumps(dict(schema_version='1.0',checked_on='2026-10-02',sources=sources),ensure_ascii=False,indent=2)+'\n')
print('18 primary/official source cards written')
