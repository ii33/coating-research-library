"""Author-side metadata construction; no network/downloads or sibling writes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
rows=[
('MI-S01','Steven J. Byrnes','Multilayer optical calculations','2016; v5 2020-12-30','https://arxiv.org/html/1603.02720v5','10.48550/arXiv.1603.02720','primary_author_methods','§§2.2,3,4.2; Appendix A','Read primary HTML sections including explicit reflected-p basis and Eq.16; existing T07 local PDF not copied','本原稿以明确方向矢量给出s/p振幅和椭偏相位定义。用于检查相位约定而非材料常数；原稿Eq.16另有负号，不能直接把其Delta等同本册任一基矢比。','平面各向同性非磁；不是退偏仪器模型，也不是生产校准。'),
('MI-S02','J. N. Hilfiker, N. Singh, T. Tiwald, D. Convey, S. M. Smith, J. H. Baker, H. G. Tompkins','Survey of methods to characterize thin absorbing films with Spectroscopic Ellipsometry','2008','https://www.sciencedirect.com/science/article/pii/S0040609008003623','10.1016/j.tsf.2008.04.060','primary_comparative_experiment','Thin Solid Films 516,7979–7989; abstract, introduction and publisher section snippets','Read publisher abstract and section snippets; commercial full text not obtained','原作者比较不同厚度/基片的Cr膜，展示多角干涉增强、联合强度、多样品及参数化的条件作用。方法效果取决于样品和实现；共享光学常数需要验证。','题名虽为Survey，使用的证据是其原始Cr比较实验摘要；未核验全文图表数值，不作通用唯一性保证。'),
('MI-S03','A. Raue, C. Kreutz, T. Maiwald, J. Bachmann, M. Schilling, U. Klingmüller, J. Timmer','Structural and practical identifiability analysis of partially observed dynamical models by exploiting the profile likelihood','2009','https://academic.oup.com/bioinformatics/article/25/15/1923/213246','10.1093/bioinformatics/btp358','primary_methods','Bioinformatics 25(15),1923–1929; §§2.1–2.3 and 3','Read publisher full HTML selected statistical/method sections','以固定一个参数并优化其它参数的剖面检测退化和数据约束。本包保留多起点失败及域边界，不把有限网格局部优化视为全局剖面证明。','原例是动态生化模型；本包没有重现其系统或直接采用其区间覆盖结论。'),
('MI-S04','Oana-Teodora Chis, Julio R. Banga, Eva Balsa-Canto','Structural Identifiability of Systems Biology Models: A Critical Comparison of Methods','2011','https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0027755','10.1371/journal.pone.0027755','primary_methods_comparison','PLOS ONE 6(11),e27755; Methods, structural-identifiability definition; PDF pp1–3','Read publisher HTML definitions/method sections; 16-page official PDF locally archived under explicit CC Attribution','结构辨识属于模型和观测映射；局部/全局与实际噪声问题不同。本册有限维光学等价集自行推导，不声称复现其ODE全局算法。','文中连续时间/解析系统的完整可辨识检验不等于本包有限采样Jacobian。'),
('MI-S05','G. E. Jellison Jr.','Data analysis for spectroscopic ellipsometry','1993','https://www.sciencedirect.com/science/article/pii/0040609093902984','10.1016/0040-6090(93)90298-4','primary_author_methods','Thin Solid Films 234,416–422; publisher abstract','Read publisher abstract only; commercial full text not obtained','原文摘要区分Fresnel前向计算、材料光学参数化、数据拟合三层。这里只作方法结构来源，不引用未读页内公式。','没有用未获全文支持特定误差传播、软件功能或仪器噪声值。'),
('MI-S06','Leonard M. Hanssen','Integrating-Sphere System and Method for Absolute Measurement of Transmittance, Reflectance and Absorptance of Specular Samples','2001','https://www.nist.gov/publications/integrating-sphere-system-and-method-absolute-measurement-transmittance-reflectance-and','10.1364/AO.40.003196','primary_metrology_method','Applied Optics 40(19),3196–3204; NIST official abstract; inherited T06 PO-S05 scope','Re-read official NIST publication abstract; T06 prior full-PDF verification retained as inherited evidence','绝对R/T及由其求A具有具体装置与收集条件。几何及仪器误差不能靠能量缺口公式消失。','NIST能力不代表用户硬件；不把镜面缺口当吸收，不复述装置不确定度为通用数字。')]
sources=[]
for id,authors,title,year,url,doi,typ,locator,extent,summary,limitation in rows:
    p=f'sources/summaries/{id}.md'
    local='sources/originals/MI-S04_Chis_2011.pdf' if id=='MI-S04' else None
    sources.append(dict(id=id,authors=authors,title=title,year=year,url=url,doi=doi,source_class=typ,locator=locator,
                        read_extent=extent,checked_on='2026-10-02',summary_path=p,local_original=local,
                        reader_redistribution=False,limits=limitation))
    (ROOT/p).write_text(f'# {id} · {title}\n\n作者：{authors}。年份/版本：{year}。DOI：{doi}\n\n原始来源：{url}\n\n定位：{locator}\n\n已读范围：{extent}\n\n原创摘要：{summary}\n\n边界：{limitation}\n\n权利：只用原创摘要和链接进入reader；'+('原刊明示CC Attribution，合法PDF仅本地存档，见data/local_source_archive_manifest.json。' if local else '本轮未下载原件；可访问不等于许可镜像或发布。')+'\n')
write(ROOT/'sources/source_registry.json',{'checked_on':'2026-10-02','primary_sources_only':True,'sources':sources,
      'source_claim_scope':'All equations beyond brief attributed summaries are project derivations; all numerical observations synthetic',
      'no_unread_fulltext_claims':True})
project=ROOT.parents[1];deps=json.loads((ROOT/'data/frozen_dependencies.json').read_text())
read_paths=['00_project/工程科研.txt','ROADMAP.md','06_optical_coating_families/round2_process_optical_observables/T07_ROUND2_HANDOFF.md',
 '06_optical_coating_families/round2_process_optical_observables/reports/01_process_to_conditioned_film.md',
 '06_optical_coating_families/round2_process_optical_observables/reports/02_optics_and_measurement_contract.md',
 '06_optical_coating_families/round2_process_optical_observables/reports/03_identifiability_and_failure_cases.md',
 '06_optical_coating_families/round2_process_optical_observables/reports/04_measurement_and_uncertainty_plan.md',
 '07_thin_film_design_theory/reports/01_maxwell_conventions_and_observables.md']
write(ROOT/'data/read_provenance.json',{'read_only_inputs':[{'path':p,'sha256':hashlib.sha256((project/p).read_bytes()).hexdigest(),'runtime_dependency':False} for p in read_paths],
      'preserved_before_snapshot':'verification/outside_before.json'})
write(ROOT/'data/measurement_contract.json',{'evidence':'synthetic','actual_user_hardware':None,'n_k_d_units':['1','1','um'],
 'time':'exp(-i omega t)','passive_index':'n+ik','kernel_amplitude':'tangential_E','ratio_conventions':['opposed_reflected_p','same_tangential_p'],
 'executed_substrate_mode':'semi_infinite_real_n','executed_scatter':'explicit_zero_synthetic',
 'rejected':['unknown scattering','finite/backside substrate','mixed-ray rho average','material transfer as measurement','unverified instrument adapter'],
 'noise_known_for_real_user':False,'device_validation':'not_run_awaiting_device','production_qualified':False})
write(ROOT/'stage_status.json',{'stage_id':'ROUND2.T07_MEASUREMENT_IDENTIFIABILITY','version':'T07-r2-v0.1.0','algorithmic':True,
 'status':'implementation_ready_validation_pending','local_freeze_only':True,'production_qualified':False,
 'actual_hardware':None,'actual_measurements':False,'heavy_run':'not_run_awaiting_device',
 'author_self_check':'completed_in_scope','independent_narrow_check':{'model':'GPT-6 Luna','scope':'phase_basis_and_Jacobian_covariance_units','status':'completed','not_full_review_chain':True},
 'specified_model_chain':{'DeepSeek_execution':'not_run','Seed_Pro_stage_review':'pending_not_run','Sol_full_algorithm_review':'pending_not_run'},
 'tests_meaning':'small correctness only; no production calibration, coverage or performance acceptance',
 'next_handoff':'T08_ROUND2_HANDOFF.md','publication':'not_requested_not_run','stop_condition':'local_freeze_and_receipt'})
