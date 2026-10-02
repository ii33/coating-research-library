import csv,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
rows=[
('Q01','身份与初始疵病','ISO 10110-7:2017; ISO 14997:2017','成品与见证片有效口径','同位显微/可见度图','照明/样板/观察路线'),
('Q02','厚度及均匀性','适配并验证的物理/光学厚度方法','膜层与位置映射','原始厚度/坐标/拟合残差','nd与d混淆/工具系数'),
('Q03','nk模型','已验证椭偏/分光反演协议','单层标定片及成品','模型/参数相关/原始谱','非唯一/背面/粗糙层'),
('Q04','光谱AOI偏振','ISO 15368:2021; ISO 13697:2006','指定表面或整片','R/T λ-AOI-p原始数据','带宽/NA/背面/重定位'),
('Q05','散射','ISO 13696:2022','适用曲率与波段样品','前后向及角积分范围','镜面排除/颗粒/曲率'),
('Q06','吸收','ISO 11551:2026','实际基片和膜','吸收率/背景/温度模型','基片吸收/相减大数'),
('Q07','应力与面形','受控曲率/波前协议','见证片及实际安装态','曲率/面形/温度','薄膜假设/夹持'),
('Q08','附着','ISO 9211-4:2022; GB/T 26332.4-2026','批准破坏性样品','方法条件/剥离图/界面','胶带批/划切/基片破裂'),
('Q09','摩擦耐磨','ISO 9211-4:2022; GB/T 26332.4-2026','独立或合同指定序列样品','载荷/动作/磨头/后测','磨屑/动作定义/脆性'),
('Q10','清洗耐久','批准材料兼容清洗协议','实际被清洗面','介质/机械对照/前后谱','残留/拖曳颗粒'),
('Q11','水阻湿热','ISO 9022-2:2015+Amd1:2023; GB/T 2423.3-2016; ISO 9211-4:2022','裸片或批准封装','实测温湿/恢复/光谱','凝露与湿度不等同'),
('Q12','温度与温变','ISO 9022-2:2015+Amd1:2023; GB/T 2423.22-2012','自由片与安装态依用途','实际样品温度/面形/裂纹','热滞后/速率/夹持'),
('Q13','盐环境','ISO 9022-4:2014+Amd1:2023; GB/T 2423.17-2024; GB/T 2423.18-2021','有盐暴露用途才选','溶液/沉降/边缘/光谱','盐浸不等盐雾/腐蚀寿命'),
('Q14','激光损伤','ISO 21254-1:2025; ISO 21254-2:2011; ISO 21254-3:2011','有激光能力要求才选','每点能量/脉冲/光斑/终点','统计/污染/检测/conditioning'),
('Q15','包装储存追踪','批准产品储运/老化协议','实际包装及留样','时效/污染/前后谱','包装放气/留样偏差')]
fields=['test_id','characteristic','candidate_method','sample_object','required_raw_record','confounders','clause','severity','sample_count','acceptance_limits','uncertainty_budget','decision_rule','applicability','approval']
with (P/'templates/test_matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(fields)
 for r in rows:w.writerow(list(r)+['TBD']*8)
blank_keys=('method_id','edition','controlled_text_id','clause','severity_or_method_conditions','sample_plan','pre_post_measurements','acceptance_source','acceptance_limits','decision_rule','uncertainty_budget_id','laboratory_capability_evidence','sequence_and_recovery','safety_review_id')
tests=[]
for tid,char,method,obj,raw,conf in rows:
 t=dict(test_id=tid,characteristic=char,candidate_method_only=method,applicability='undecided',exclusion_reason=None,exclusion_approval=None,normative_procedure_verified=False)
 t.update({k:None for k in blank_keys});tests.append(t)
plan=dict(schema_version='T09-r1-v0.1.0',purpose='planning_template_not_approved',data_class='template',product_id=None,contract_id=None,drawing_revision=None,lot_definition=None,laboratory_id=None,approval_record=None,execution_authorized=False,tests=tests)
(P/'templates/qualification_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
record=dict(schema_version='T09-r1-v0.1.0',record_id=None,test_id=None,product_id=None,lot_id=None,run_id=None,substrate_material_grade_batch=None,coating_recipe_revision=None,surface_id=None,position_map=None,real_or_synthetic=None,method=dict(standard_id=None,edition=None,amendment=None,controlled_copy=None,clause=None,procedure=None,deviations=[],approved_by=None),specimen=dict(sampling_plan=None,preparation=None,cleaning_history=None,exposure_history=None,storage_and_packaging=None),apparatus=dict(instrument_id=None,calibration_id=None,range=None,capability_record=None),conditions=dict(setpoints=None,measured_timeline_file=None,geometry=None,wavelength_grid=None,spectral_bandwidth=None,aoi=None,polarization=None,collection_geometry=None,spot_definition=None,environment=None,recovery=None),results=dict(raw_before=None,raw_after=None,images_before=None,images_after=None,metric_name=None,units=None,unrounded_value=None,standard_uncertainty=None,coverage_factor_or_interval_method=None,expanded_uncertainty=None,covariance_assumptions=None,detection_limit=None),decision=dict(specification_source=None,limits=None,rule_id=None,outcome='not_evaluated',invalid_test_reason=None,retest_link=None,authorized_signer=None),lidt_if_applicable=dict(wavelength=None,pulse_duration_definition=None,repetition_rate=None,energy_trace=None,spot_area_convention=None,aoi_reference_plane=None,site_map=None,pulses_per_site=None,conditioning=None,damage_detection_definition=None,site_damage_records=None,statistical_model=None,confidence_level=None),real_compliance_statement=False)
(P/'templates/test_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
with (P/'templates/uncertainty_budget.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['input','estimate','unit','standard_uncertainty','distribution','sensitivity','correlation_group','dof','evidence','before_after_treatment'])
 for x in ['repeat_reading','reposition','wavelength_calibration','angle_of_incidence','polarization_purity','reference_standard','dark_baseline','spectral_bandwidth','instrument_drift','sample_temperature','spatial_nonuniformity','model_fit']:
  w.writerow([x,'TBD','TBD','TBD','TBD','TBD','TBD','TBD','TBD','TBD'])
with (P/'templates/clause_evidence_map.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['requirement_id','standard_id','edition_and_amendments','clause_or_table','full_text_verified','sample_ids','equipment_and_capability','method_conditions','acceptance_source','limits','sampling','decision_rule','raw_data','uncertainty','result','approval'])
 w.writerow(['REQ-TBD']+['TBD']*3+['false']+['TBD']*11)
with (P/'templates/failure_process_matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['failure_id','observed_symptom','competing_hypotheses','evidence','process_variables_within_approved_window','verification_plan','negative_responses','status'])
 for n,obs,hyp,var,test,neg in [
 (1,'湿热谱移','吸水/厚度/AOI漂移','致密化/保护层/包装','干湿恢复+厚度nk交叉','应力/吸收'),
 (2,'脱层','污染/孔道/界面反应','清洗/等待/首层','界面定位+独立批','光谱/基片损伤'),
 (3,'温循裂纹','热失配/应力/夹持','应力平衡/总厚度/夹具','自由片与安装态对照','面形/附着'),
 (4,'盐腐蚀','针孔/边缘/电偶','覆盖连续/颗粒/边缘','位置图+盐环境重复','吸收/散射'),
 (5,'清洗雾化','残留/颗粒拖曳/溶蚀','兼容介质/布材','介质与机械对照','透射/吸收'),
 (6,'附着试验失败','层间/膜基/基片破裂','前处理/首层','先核方法有效再定位','批一致性'),
 (7,'耐磨好光谱差','保护层吸收/粗糙/应力','保护层策略','联合功能和耐久','光学余量'),
 (8,'LIDT低平均吸收正常','稀疏缺陷/热点/污染','颗粒控制/清洁转运','同条件点位统计+同位图','损伤生长'),
 (9,'相同谱不同LIDT','化学计量/污染/统计条件','反应环境/维护','统一条件+吸收化学对照','散射/应力'),
 (10,'工位差','厚度/能量/温度梯度','位置/运动/遮蔽','位置映射+随机化','边缘性能'),
 (11,'批间漂移','材料批/晶振/腔体/测量','维护/来料/端点','跨批留样与参比','过程稳定'),
 (12,'退火后耐久差','界面/微结构/基片变化','允许热路径','前后面形附着时效','光谱/吸收')]:
  w.writerow([f'F{n:02d}',obs,hyp,'TBD',var,test,neg,'hypothesis_not_confirmed'])
