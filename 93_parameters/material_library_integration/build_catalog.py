"""Lossless, deterministic reuse import. No external requests or fitted coefficients."""
import json, hashlib, re
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
inputs={}
def read(path):
 p=ROOT/path; b=p.read_bytes(); inputs[path]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 return json.loads(b)
def readtext(path):
 p=ROOT/path;b=p.read_bytes();inputs[path]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def source(s,path,prefix=''):
 sid=s.get('id',s.get('source_id'));return {'id':prefix+sid,'title':s.get('title',sid),'url':s.get('url',s.get('stable_url')),'local_path':path,'locator':s.get('locator',s.get('specific_supported_claims','Source registry entry '+sid)),'access_status':s.get('access_scope',s.get('access_level',s.get('access',s.get('read_scope','see_original_record')))),'original_record':s}
t04='04_coating_and_substrate_materials/'
sources={s['id']:source(s,t04+'data/source_registry.json') for s in read(t04+'data/source_registry.json')['sources']}
props=read(t04+'data/property_records.json')['records'];manifest=read(t04+'data/materials_manifest.json')
materials=[]
def prop(id,name,value,unit,conditions,source_ids,status,notes,original=None):
 p=dict(id=id,name=name,value=value,unit=unit,conditions=conditions,source_ids=source_ids,status=status,notes=notes)
 if original is not None:p['original_record']=original
 return p
for m in manifest:
 mid=m['material_id']; stem=mid.rsplit('_',1)[0]; card=t04+m['card_file'];txt=readtext(card)
 material=dict(id=mid,name=m['label'],formula=None if stem in ['H4','K9'] else stem,roles=['film' if m['role']=='coating' else 'substrate'],aliases=[stem],description='既有T04材料研究；文献/厂家条件化参考，非本机已验证常数。',sources=[sources[s] for s in m['source_ids']],properties=[],gaps=[],topics=['T04'],research_text=txt,research_path=card)
 for r in props:
  if r['material_id']!=mid:continue
  status='quarantined' if r.get('status')=='quarantined' or r.get('conflict_flag') else 'unknown' if r['value'] is None else 'conditional'
  cond=dict(r['conditions']);cond.update(sample_state=r.get('sample_state',r.get('state')),uncertainty=r.get('uncertainty'),original_status=r.get('status'),design_ready=False,use_as_universal_constant=False,provenance_path=t04+'data/property_records.json',source_locator=cond.get('source_locator',r.get('notes','')))
  material['properties'].append(prop(r['record_id'],r['property'],r['value'],r['unit'],cond,[r['source_id']] if r['source_id'] else [],status,r.get('unknown_reason',r.get('conflict_note',r.get('notes','保留来源状态与工艺条件，不自动迁移到本机'))),r))
  if status=='unknown':material['gaps'].append(r.get('unknown_reason',r['property']))
 materials.append(material)
byid={m['id']:m for m in materials}
# Preserve response contract separately: null indexed references mean no chosen row, not no evidence.
r2path=t04+'round2_material_response_contract/data/priority_material_mapping.json';r2=read(r2path)
for m in r2['materials']:
 byid[m['material_id']]['response_contract']={'path':r2path,'fields':m['fields'],'identity_and_transfer_limits':m['identity_and_transfer_limits'],'reference_resolution':r2['reference_resolution']}
 byid[m['material_id']]['topics'].append('T04-R2')
evidence={}
for prefix,ref in r2['reference_resolution'].items():
 if not isinstance(ref,dict):continue
 d=read(ref['path_from_project_root']);d=d.get(ref['container'],[]) if 'container'in ref else d
 if isinstance(d,list):
  for s in d:
   evidence[prefix+':'+s[ref['key']]]={'path':ref['path_from_project_root'],'original_record':s}
   if prefix.endswith('SOURCE'):
    ss=source(s,ref['path_from_project_root'],prefix+':');sources[ss['id']]=ss
for m in materials:
 refs=set()
 for field in m['response_contract']['fields'].values():
  refs.update(field.get('evidence_refs',[]))
 m['resolved_evidence']={ref:evidence[ref] for ref in sorted(refs) if ref in evidence}
 m['unresolved_evidence_refs']=[ref for ref in sorted(refs) if ref not in evidence]
 for ref in sorted(refs):
  if ref in sources and not any(s['id']==ref for s in m['sources']):m['sources'].append(sources[ref])
# The R2 method demonstrator is additional studied bulk material, explicitly not user priority.
rep=r2['representative_combination']; rr=rep['separated_references']; fs=[]
for key in ['bulk_density','bulk_refractive_index']:
 r=rr[key]; sid=r['source_ref']; value=r['value'] if r['value'] is not None else r['model']
 fs.append(prop('R2-fused-silica-'+key,key,value,r.get('unit','model'),dict(r['conditions'],sample_state='bulk_fused_silica',provenance_path=r2path,method_demonstration_only=True),[sid],'conditional','仅bulk参考，不能转为蒸发SiO2膜常数；模型系数在conditions内，未启用自动计算',r))
materials.append(dict(id='fused_silica_method_demonstrator',name='熔融硅石基片（方法示范）',formula='SiO2',roles=['substrate'],aliases=['fused silica','HPFS'],description=rep['scope_warning'],sources=[sources[rr[k]['source_ref']] for k in ['bulk_density','bulk_refractive_index']],properties=fs,gaps=['非用户原始优先材料；不代表已校准SiO2/熔融硅石组合','未给k不得填零'],topics=['T04-R2'],response_contract=rep))
# T05 material/source coupling, qualified candidates only.
t05path='05_evaporation_sources/data/material_source_matrix.json';matrix=read(t05path)
for r in matrix:
 m=byid[r['material']+'_film'];m['topics'].append('T05');m['source_coupling']=r
 sids=[s.removeprefix('T04-') for s in r['source_ids']]
 for key in ['resistance_candidate','electron_beam_candidate','phase_chemistry_boundary','risk']:
  m['properties'].append(prop('T05-'+r['material']+'-'+key,key,r[key],'text',{'state':'source_material_container_pair','provenance_path':t05path,'production_settings':None},sids,'conditional',r['evidence_status']))
 m['gaps'] += ['蒸气物种/分压、蒸发系数、源温测量与有效面积待条件化；不能从目录沉积速率反推绝对通量','粉床有效导热、接触热阻、吸收功率及壁面留存未按本机验证']
# Structure selected numerical facts formerly confined to existing narrative cards.
extract_path='93_parameters/material_library_integration/card_extractions.json'
for i,row in enumerate(read(extract_path)['records'],1):
 mid,key,value,unit,sid,state,note=row
 m=byid[mid];cond={'sample_state':state,'source_locator':m['research_path'],'provenance_path':extract_path,'design_ready':False,'use_as_universal_constant':False}
 match=re.search(r'temperature_degC=(\d+)',note)
 if match:cond['temperature_degC']=float(match.group(1))
 m['properties'].append(prop('CARD-'+str(i).zfill(3),key,value,unit,cond,[sid],'conditional',note))

# Explicit container role entries, not additional coating chemistry.
containers=[('W','钨','W',['W','钨']),('Mo','钼','Mo',['Mo','钼']),('Ta','钽','Ta',['Ta','钽']),('Pt','铂','Pt',['Pt','铂']),('graphite','石墨','C',['石墨']),('glassy_carbon','玻璃碳','C',['玻璃碳']),('FABMATE','FABMATE 商品牌号',None,['FABMATE']),('Cu','铜炉床','Cu',['铜']),('Al2O3','氧化铝坩埚','Al2O3',['Al2O3']),('TiB2_BN','TiB2–BN 复合衬里',None,['TiB2','BN'])]
for cid,label,formula,terms in containers:
 entries=[];sids=set()
 for r in matrix:
  for route in ['resistance_candidate','electron_beam_candidate']:
   if any(t in r[route] for t in terms):
    rs=[s.removeprefix('T04-') for s in r['source_ids']];sids.update(rs)
    entries.append(prop('T05-container-'+cid+'-'+r['material']+'-'+route,'compatibility_candidate',r[route],'text',{'evaporant_material':r['material'],'route':route,'risk':r['risk'],'provenance_path':t05path},rs,'conditional','仅原厂条件化候选；不是通用兼容认证'))
 # Al interaction is explicit in the original card, even though candidate column does not name all metals.
 if cid in ['W','Mo','Ta']:
  entries.append(prop('T05-container-'+cid+'-Al-risk','alloying_embrittlement_risk','Al可与W/Mo/Ta合金化，使舟脆化开裂','text',{'evaporant_material':'Al','provenance_path':t04+'cards/12_Al_film.md'},['M04'],'conditional','由既有Al卡片复用；寿命数值未知'));sids.add('M04')
 materials.append(dict(id=cid+'_source_container',name=label+'（源容器）',formula=formula,roles=['boat','component'],aliases=terms,description='T05已有源容器相容性研究索引；不是独立完整热物性库。',sources=[sources[s] for s in sorted(sids)],properties=entries,gaps=['牌号、几何、温度范围、热/电物性、润湿污染与寿命须按实际容器补充'],topics=['T05']))
# Existing ITO bibliography and sample-linked observations; compound formula intentionally unspecified.
ito='11_transparent_conductive_films/ito/'
idx=read(ito+'sources/source_index.json')['records']
its={s['source_id']:source(s,ito+'sources/source_index.json') for s in idx}
for s in read(ito+'process/sources.json')['sources']:its[s['source_id']]=source(s,ito+'process/sources.json')
eo=read(ito+'electro_optics/evidence_ledger.json')
for s in eo['sources']:its[s['source_id']]=source(s,ito+'electro_optics/evidence_ledger.json')
ledger=read(ito+'process/evidence_ledger.json');app=read(ito+'process/apparatus_conditions.json')
im=dict(id='ITO_film',name='ITO 氧化铟锡薄膜',formula=None,roles=['film'],aliases=['ITO','In2O3:Sn','indium tin oxide'],description='Sn掺杂In2O3体系；源料氧化物质量比、实膜Sn阳离子比、氧缺陷和自由载流子浓度不得互换。',sources=list(its.values()),properties=[],gaps=['无同批项目样片的电学/光学/成分联合标定','源氧化/组分分馏常数未知','有效质量/散射/Drude参数不能跨样本拼接'],topics=['T11'],research_path=ito+'process/report.md',research_text=readtext(ito+'process/report.md'),electro_optics_evidence=eo,apparatus_conditions=app)
units={'AFM_RMS_nm':'nm','FOM_ohm_inverse':'1/ohm','O2_sccm':'sccm','Rs_ohm_sq':'ohm/sq','Rs_ohm_sq_derived':'ohm/sq','T_percent':'%','Tauc_gap_eV':'eV','anneal_C':'degC','anneal_time_h':'h','discharge_A':'A','discharge_V':'V','grain_nm':'nm','mu_cm2_Vs':'cm2/(V*s)','n_cm3':'cm-3','rate_nm_s':'nm/s','rho_ohm_cm':'ohm*cm','rho_ohm_cm_derived':'ohm*cm','rho_text_ohm_cm':'ohm*cm','source_SnO2_wt_percent':'wt%','substrate_C':'degC','substrate_preheat_C':'degC','thickness_nm':'nm'}
for o in ledger['observations']:
 for key,value in o.items():
  unit=units.get(key)
  if key.startswith('anneal_') and key.endswith('_Rs'):unit='ohm/sq'
  if key.startswith('anneal_') and key.endswith('_T'):unit='%'
  if unit is None:continue
  unknown=isinstance(value,str) and ('NR' in value or '实际温升未给' in value)
  status='quarantined' if o['status']=='contradicted' else 'unknown' if unknown else 'conditional'
  cond={'sample':o['sample'],'series':o['series'],'source_locator':o['locator'],'sample_state':'thin_film','provenance_path':ito+'process/evidence_ledger.json','observation_id':o['observation_id'],'paired_observation':o,'apparatus':app.get(o['source_id'],{}),'design_ready':False}
  im['properties'].append(prop(o['observation_id']+'-'+key,key,None if unknown else value,unit,cond,[o['source_id']],status,o['limits'],o))
for c in ledger['claims']:
 im['properties'].append(prop(c['claim_id'],'process_evidence_claim',c['claim_zh'],'text',{'locators':c['locators'],'provenance_path':ito+'process/evidence_ledger.json'},c['source_ids'],'quarantined' if c['status']=='contradicted' else 'conditional',c['limitations'],c))
materials.insert(16,im)
# Supplement included losslessly, kept separate from model-ready coefficients.
supp='99_sources/supplements/2026-10-04_zns_reuse_audit/'
extra=read(supp+'data/parameters.json');extra_sources=read(supp+'sources/source_registry.json')
byid['ZnS_film']['reuse_audit_supplement']={'parameters':extra,'sources':extra_sources,'path':supp+'data/parameters.json'}
# Original-state optical proxy data stay identified as proxies, never empirical k=0.
proxy_path='06_optical_coating_families/data/material_proxies.json';proxies=read(proxy_path)
# Include all canonical source registries, avoiding duplicate archive dependencies.
def collect_refs(obj):
 refs=set()
 if isinstance(obj,dict):
  for key,value in obj.items():
   if key=='source_ref' and isinstance(value,str):refs.add(value)
   elif key=='evidence_refs' and isinstance(value,list):refs.update(value)
   refs.update(collect_refs(value))
 elif isinstance(obj,list):
  for value in obj:refs.update(collect_refs(value))
 return refs
for m in materials:
 refs=collect_refs(m.get('response_contract',{}))
 m['resolved_evidence']={ref:evidence[ref] for ref in sorted(refs) if ref in evidence}
 m['unresolved_evidence_refs']=[ref for ref in sorted(refs) if ref not in evidence]
 for ref in sorted(refs):
  if ref in sources and not any(s['id']==ref for s in m['sources']):m['sources'].append(sources[ref])
 m['provenance_input_files']=dict(inputs)
result={'schema_version':1,'dataset_id':'existing-research-materials-2026-10-04-v1','scope':'16 T04 priority material-role entries + ITO + fused silica method demonstrator + 10 distinct source-container role entries','materials':materials,'reference_sources':list(sources.values()),'optical_proxy_context':{'path':proxy_path,'original_data':proxies,'warning':'Proxy ideal assumptions are not measured material constants.'},'policy':{'unknown_is_zero':False,'automatic_production_defaults':False,'source_pressure_is_chamber_pressure':False,'bulk_qcm_film_density_interchangeable':False,'new_coefficients_fitted':False,'external_research_repeated':False},'input_files':inputs}
(OUT/'researched_materials.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
summary={'materials':len(materials),'primary_material_role_entries':18,'source_container_entries':10,'t04_records':len(props),'ito_observations':len(ledger['observations']),'property_rows':sum(len(m['properties']) for m in materials),'status_counts':dict(Counter(p['status'] for m in materials for p in m['properties'])),'materials_by_id':{m['id']:len(m['properties']) for m in materials},'input_files':len(inputs),'dataset_sha256':hashlib.sha256((OUT/'researched_materials.json').read_bytes()).hexdigest()}
(OUT/'coverage.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
