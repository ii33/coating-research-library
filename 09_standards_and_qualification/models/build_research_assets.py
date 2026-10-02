"""Build original metadata/summary assets from author-checked public source records.
Does not download or reproduce any standards text.
"""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
DATE='2026-10-02'
# identity, official URL, public status, date field as presented, role, scope/limit, prior version
R=[
('ISO 10110-9:2016','https://www.iso.org/standard/63596.html','Published; 90.92 to be revised','2016-07','drawing','表面处理与镀膜的图样表达；ISO/DIS 10110-9仍是草案，不能当作发布版本','ISO 10110-9:1996'),
('ISO 10110-7:2017','https://www.iso.org/standard/65444.html','Published; 90.93 confirmed 2022','2017-08','drawing','表面疵病的允许程度，可选尺寸或可见度表述；不等于粗糙度指标','ISO 10110-7:2008'),
('ISO 10110-8:2019','https://www.iso.org/standard/69532.html','Published; 90.93 confirmed 2025','2019-11','drawing','表面纹理、粗糙度及中频起伏；主要针对抛光光学件','ISO 10110-8:2010'),
('ISO 14997:2017','https://www.iso.org/fr/standard/63464.html','Published; 90.93 confirmed 2022','2017-08','test_method','疵病的可见度与尺寸检验路线须与图样相匹配','ISO 14997:2011'),
('ISO 9211-1:2024','https://www.iso.org/standard/82935.html','Published; 60.60','2024-02','vocabulary','光学薄膜术语；不规定生产工艺，排除眼镜光学','ISO 9211-1:2018'),
('ISO 9211-2:2024','https://www.iso.org/standard/82934.html','Published; 60.60','2024-02','specification','光学性质及光谱表达；DAmd 1仍在制定，不可静默并入','ISO 9211-2:2010'),
('ISO 9211-3:2024','https://www.iso.org/standard/84707.html','Published; 60.60','2024-02','environment_selection','按用途选择环境耐久试验，指向9022与9211-4；用途类别不是统一生产配方','ISO 9211-3:2008'),
('ISO 9211-4:2022','https://www.iso.org/standard/82042.html','Published; 60.60','2022-03','test_method','光学涂层耐磨、附着、耐水方法；完整程序未读，不能从题名补出参数','ISO 9211-4:2012'),
('ISO 9211-5:2018','https://www.iso.org/standard/69398.html','Published; 90.92 to be revised','2018-11','minimum_requirements','减反膜最低要求；DIS后继在研；未获全文不填写最低数值',None),
('ISO 9211-6:2018','https://www.iso.org/standard/69399.html','Published; 90.92 to be revised','2018-10','minimum_requirements','适用基于铝或银的金属反射膜，不能推广为所有介质高反膜标准；DIS在研',None),
('ISO 9211-7:2021','https://www.iso.org/standard/80475.html','Published; 90.60 close of review','2021-09','minimum_requirements','中性分束膜最低要求；当前产品页与缓存委员会页审查阶段不同','ISO 9211-7:2018'),
('ISO 9211-8:2018','https://www.iso.org/standard/69401.html','Published; 90.93 confirmed 2025','2018-12','minimum_requirements','激光光学用膜的光学与耐久最低要求；不是任意波长下的统一LIDT数值',None),
('ISO 9022-1:2016','https://www.iso.org/standard/69938.html','Published; 90.60 close of review','2016-07','environment_general','光学和光子仪器环境试验定义与基本特征；2026-09-03结束本轮复审','ISO 9022-1:2012'),
('ISO 9022-2:2015','https://www.iso.org/standard/63316.html','Published; 90.92 to be revised','2015-03','test_method','冷、热、湿环境；有2023修改单，CD后继尚未发布','ISO 9022-2:2002'),
('ISO 9022-2:2015/Amd 1:2023','https://www.iso.org/standard/84356.html','Published; 60.60','2023-07','amendment','针对9022-2:2015的修改单，应与主标准一起受控',None),
('ISO 9022-4:2014','https://www.iso.org/standard/66490.html','Published; 90.93 confirmed 2025','2014-11','test_method','光学仪器盐雾暴露，需指明试样及适用环境；有2023修改单','ISO 9022-4:2002'),
('ISO 9022-4:2014/Amd 1:2023','https://www.iso.org/standard/84357.html','Published; 60.60','2023-02','amendment','针对9022-4:2014的修改单，不能只写基础年份',None),
('ISO 21254-1:2025','https://www.iso.org/standard/83937.html','Published; 60.60','2025-08','lidt_general','LIDT术语与通则；2011版本已撤销，需检查与其余分部规范引用的兼容','ISO 21254-1:2011'),
('ISO 21254-2:2011','https://www.iso.org/standard/43002.html','Published; 90.60 close of review','2011-07','lidt_threshold','1-on-1和S-on-1阈值测定；2026-06-05复审结束不等于撤销','ISO 11254-1:2000; ISO 11254-2:2001'),
('ISO 21254-3:2011','https://www.iso.org/standard/43003.html','Published; 90.93 confirmed 2022','2011-07','lidt_assurance','功率/能量承受能力保证；抽样/置信试验不同于阈值探索','ISO 11254-3:2006'),
('ISO/TR 21254-4:2011','https://www.iso.org/standard/43004.html','Published Technical Report; 60.60','2011-09','informative_detection','损伤检查、检测与测量技术报告；TR性质不能写成同等强制验收条款',None),
('ISO 15368:2021','https://www.iso.org/standard/72598.html','Published; 90.60 close of review','2021-03','metrology','平面/平行平板的规则反射与透射，不适用于漫射或有光焦度试样','ISO 15368:2001'),
('ISO 13697:2006','https://www.iso.org/standard/38483.html','Published; 90.92 to be revised','2006-05','metrology','激光光学件镜面反射与规则透射的精密测量；实际能力仍须证明',None),
('ISO 13696:2022','https://www.iso.org/standard/72956.html','Published; 60.60','2022-06','metrology','总散射及前/后向分量；摘要限定表面曲率半径大于10 m，波段与几何需核适用性','ISO 13696:2002'),
('ISO 11551:2026','https://www.iso.org/standard/90409.html','Published; 60.60','2026-08','metrology','激光光学件吸收率可比测量；2019版于2026-08-20撤销','ISO 11551:2019'),
('ISO 11554:2025','https://www.iso.org/standard/85866.html','Published; 60.60; corrected en/fr 2025-10','2025-06','metrology','激光功率、能量、脉冲形状/时宽/重频与稳定性；记录2025-10更正版','ISO 11554:2017'),
('ISO/IEC 17025:2017','https://www.iso.org/standard/66912.html','Published; 90.93 confirmed 2023','2017-11','laboratory_competence','实验室能力、公正性与一致运作；实验室认可范围需要匹配具体方法和量程','ISO/IEC 17025:2005'),
('ISO 2859-1:2026','https://www.iso.org/standard/85464.html','Published; 60.60','2026-01','sampling','计数逐批AQL检验方案；1999及其修改勘误已撤销；本轮不复制抽样表','ISO 2859-1:1999 + Amd 1:2011 + Cor 1:2001'),
('ASTM D3359-23','https://store.astm.org/standards/d3359','Active','2023-03-07','test_method','金属基底相对延性涂层的划切胶带等级；§1.1,1.4,1.5与§5.2/5.4提示适用性和非绝对结合强度限制',None),
('ASTM D4060-25','https://store.astm.org/standards/d4060','Active','2025-02-14','test_method','平面刚性基底有机涂层Taber磨耗；§1.1/1.3不支持自动当无机光学膜通用耐磨或ISO等效',None),
('ASTM B117-26a','https://store.astm.org/b0117-26a.html','Active','2026-09-22','test_method','盐雾设备运行；§3.2说明单独盐雾数据与自然环境服役性能相关性不足',None),
('ASTM D2247-25','https://store.astm.org/standards/d2247','Active','2025-06-10','test_method','100%RH凝露水阻；§1.4不规定试样准备或结果评价，不是一般恒定湿热等效',None),
('ASTM D1003-21','https://store.astm.org/standards/d1003','Active','2021-06-07','metrology','透明塑料等平面材料雾度与明视觉透射；不能代替红外元件散射/光谱指标',None),
('JCGM 106:2012','https://www.bipm.org/en/doi/10.59161/jcgm106-2012','Official guidance publication','2012','decision_guidance','合格评定中测量不确定度与风险；本项目的保护带示例为原创推导而非规定强制方案',None),
('ILAC G8:09/2019','https://ilac.org/publications-and-resources/ilac-guidance-series/','Listed on official guidance page','2019-09','decision_guidance','合格声明与决策规则指导；不能推出所有检验必须使用同一保护带',None),
('NIST optical scattering from surfaces','https://www.nist.gov/programs-projects/optical-scattering-surfaces','Official research overview',None,'research','角分辨与偏振散射表征可用于区分表面粗糙度、颗粒和亚表面线索；不是膜系验收标准',None),
('Ma et al. Optics Letters 42 478-481 (2017)','https://opg.optica.org/ol/abstract.cfm?uri=ol-42-3-478','Publisher abstract inspected','2017-01-24','research','Ta2O5/SiO2高反膜人工结节边界连续性与纳秒损伤的研究；不得将其工艺/结果推广至本项目所有材料',None),
('Cheng et al. Applied Optics 65 A52-A57 (2026)','https://opg.optica.org/ao/abstract.cfm?uri=ao-65-5-A52','Publisher abstract inspected','2025-10-24 online; 2026 issue','research','COC上AR膜前处理、首层材料、残余应力与耐久关系；聚合物基底特定证据，不移植到ZnS/Ge/K9/ZnSe配方',None),
('Gibson et al. durable infrared coatings Applied Optics 59 2731 (2020)','https://opg.optica.org/ao/abstract.cfm?uri=ao-59-9-2731','Publisher abstract and public table metadata inspected','2020','research','a-C:H/Ge红外膜的耐久案例；论文引用旧MIL-C并不改变DLA现行状态，论文参数非标准通用要求',None)
]
records=[]
for i,(name,url,status,date,role,summary,prior) in enumerate(R,1):
    sid=f'T09-S{i:03d}'
    publisher='ISO' if name.startswith('ISO') else 'ASTM International' if name.startswith('ASTM') else 'BIPM/JCGM' if name.startswith('JCGM') else 'ILAC' if name.startswith('ILAC') else 'NIST' if name.startswith('NIST') else 'Optica Publishing Group'
    loc='General information; Abstract; Life cycle' if publisher=='ISO' else 'Active/version; Scope; Significance and Use' if publisher.startswith('ASTM') else 'official abstract/guidance list'
    rec=dict(source_id=sid,identity=name,publisher=publisher,url=url,accessed_date=DATE,evidence_level='A',claim_status='reported',official_status=status,date_value=date,date_semantics='ISO publication month; ASTM last-updated field; research publication as labelled',implementation_date=None,implementation_note='ISO/ASTM没有从公开目录读取统一强制实施日，适用时点由合同/法规另核',role=role,summary=summary,locator=loc,predecessor=prior,full_text_reviewed=False,available_content='official catalogue/abstract; selected public metadata',normative_clause_verified=False,original_archived=False,redistribution_allowed=False,summary_redistribution_allowed=True,limitations='目录身份与摘要范围核验，不代表完整规范条款、数值、抽样表或方法验证',summary_path=f'sources/summaries/{sid}.md')
    records.append(rec)
    (P/rec['summary_path']).write_text(f'# {sid} {name}\n\n- 发布/提供者：{publisher}\n- 官方来源：{url}\n- 查询日期：{DATE}\n- 目录状态：{status}\n- 日期字段：{date}；日期语义见登记JSON\n- 原文定位：{loc}\n- 证据：A / reported，仅针对已读目录及公开内容\n\n## 原创摘要与用途\n\n{summary}。\n\n## 边界\n\n前版/替代线索：{prior or "本记录未作完整历史追溯"}。正文、数值条款与合格规则未完整核验，不能据此出具符合声明。未下载/转载标准或论文全文；原文传播权未授予。保留链接和原创摘要即可。本页不含实测数据。\n',encoding='utf-8')
(P/'data/source_registry.json').write_text(json.dumps(dict(version='T09-r1-v0.1.0',queried_date=DATE,sources=records),ensure_ascii=False,indent=2)+'\n')
(P/'data/standards_map_base.json').write_text(json.dumps(dict(version='T09-r1-v0.1.0',as_of_date=DATE,contract_ready=False,standards=[r for r in records if r['role']!='research']),ensure_ascii=False,indent=2)+'\n')
