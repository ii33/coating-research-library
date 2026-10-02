#!/usr/bin/env python3
"""Deterministic integration of completed research cards; no network or global edits."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
CATALOG=[
('Ta2O5_film','Ta2O5 镀膜材料','oxide_material_cards.md','## 1 Ta2O5'),
('ZnS_film','ZnS 镀膜材料','fluoride_sulfide_substrate_cards.md','## 1. 镀膜材料 ZnS'),
('TiO2_film','TiO2 镀膜材料','oxide_material_cards.md','## 2 TiO2'),
('YbF3_film','YbF3 氟化镱镀膜材料','fluoride_sulfide_substrate_cards.md','## 2. 镀膜材料 YbF'),
('SiO2_film','SiO2 镀膜材料','oxide_material_cards.md','## 3 SiO2'),
('MgF2_film','MgF2 镀膜材料','fluoride_sulfide_substrate_cards.md','## 3. 镀膜材料 MgF'),
('Al2O3_film','Al2O3 镀膜材料','oxide_material_cards.md','## 4 Al2O3'),
('H4_film','H4 商品高折射率镀膜材料','oxide_material_cards.md','## 5 H4'),
('Ge_film','Ge 镀膜材料','metal_ge_material_cards.md','## 09 Ge'),
('Cu_film','Cu 镀膜材料','metal_ge_material_cards.md','## 10 Cu'),
('Cr_film','Cr 镀膜材料','metal_ge_material_cards.md','## 11 Cr'),
('Al_film','Al 镀膜材料','metal_ge_material_cards.md','## 12 Al'),
('ZnS_substrate','ZnS 基片','fluoride_sulfide_substrate_cards.md','## 4. 基片 ZnS'),
('Ge_substrate','Ge 基片','metal_ge_material_cards.md','## 14 Ge'),
('K9_substrate','K9 基片','fluoride_sulfide_substrate_cards.md','## 5. 基片 K9'),
('ZnSe_substrate','ZnSe 基片','fluoride_sulfide_substrate_cards.md','## 6. 基片 ZnSe')]
def save(path,data): (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def integrate_sources():
    sources=[]
    for file in ['oxide_sources.json','ir_sources.json','metal_sources.json']:
        raw=json.loads((ROOT/'data'/file).read_text()); items=raw if isinstance(raw,list) else raw['sources']
        for d in items:
            d=dict(d);d['registry_origin']=file
            if d['id'].startswith('M'):d['summary_path']=f"sources/summaries/metal_{d['id']}.md"
            sources.append(d)
    assert len({s['id'] for s in sources})==len(sources)
    save('data/source_registry.json',dict(schema_version='1.0',frozen_at='2026-10-02',sources=sources))
    return {s['id']:s for s in sources}
def integrate_cards(sources):
    (ROOT/'cards').mkdir(exist_ok=True);manifest=[]
    for i,(mid,title,file,start) in enumerate(CATALOG,1):
        lines=(ROOT/'reports'/file).read_text().splitlines(); a=next(j for j,l in enumerate(lines) if l.startswith(start)); b=next((j for j in range(a+1,len(lines)) if lines[j].startswith('## ')),len(lines))
        body='\n'.join(lines[a+1:b]).rstrip().removesuffix('---').rstrip()
        used=sorted({s for s in sources if re.search(r'(?<![A-Z0-9])'+re.escape(s)+r'(?![A-Z0-9])',body)})
        name=f'cards/{i:02}_{mid}.md'
        header=f'# {i:02} {title}\n\nT04第一轮，2026-10-02。独立卡片由[证据分册](../reports/{file})提取；修改分册后运行 `python models/build_material_package.py` 同步。此卡是公开资料与工程推导，不是本机实测或量产配方。\n'
        footer='\n\n## 本卡证据入口\n\n'+''.join(f"- [{s} {sources[s]['title']}]({sources[s]['url']})\n" for s in used)
        (ROOT/name).write_text(header+body+footer)
        manifest.append(dict(order=i,material_id=mid,label=title,role='substrate' if mid.endswith('substrate') else 'coating',card_file=name,source_chapter=f'reports/{file}',source_ids=used,literature_review='bounded_first_round_complete',experimental_validation='not_performed',design_ready=False))
    save('data/materials_manifest.json',manifest)
    return manifest
def metal_records():
    r=[]
    def add(mid,prop,value,unit,src,state,conditions=None,status='typical',qualifier=None):
        d=dict(record_id=f'MP-{len(r)+1:03}',material_id=mid,property=prop,value=value,unit=unit,source_id=src,state=state,conditions=conditions or {'temperature':'not_reported'},uncertainty={'status':'not_reported','note':'无逐批/逐点误差；不解释为零'},status=status,design_ready=False)
        if qualifier:d['qualifier']=qualifier
        r.append(d)
    for mid,src,rho,tm,kap,cte in [('Ge_film','M01',5.32,937,60,6e-6),('Cu_film','M02',8.92,1083,400,16.5e-6),('Cr_film','M03',7.2,1857,94,4.9e-6),('Al_film','M04',2.7,660,235,23.1e-6)]:
        for prop,v,u in [('source_theoretical_density',rho,'g/cm3'),('melting_temperature',tm,'degC'),('source_thermal_conductivity',kap,'W/(m K)'),('source_linear_expansion',cte,'1/K')]:add(mid,prop,v,u,src,'source_bulk_not_film')
        add(mid,'film_effective_density',None,'g/cm3',None,'user_machine_thin_film',{'notes':'真实膜密度未知，块材不可代填'},'unknown')
        r[-1]['unknown_reason']='需要独立膜厚与面密度或其他适用测量'
    for d in json.loads((ROOT/'data/metal_nk_derived_points.json').read_text()):
        for prop in ['n','k']:
            add(d['material']+'_film','refractive_index_n' if prop=='n' else 'extinction_coefficient_k',d[prop],'1',d['source_id'],'dataset_specific_reference_film',{'wavelength_um':d['wavelength_um'],'dataset_id':d['dataset_id'],'source_sha256':d['source_sha256'],'method':d['method']},'derived')
    for w,n,unc in [(2,4.10973,.000121),(3,4.04579,.0000697),(4,4.02577,.0000652),(5,4.01678,.0000641)]:
        add('Ge_substrate','refractive_index_n',n,'1','M09','crystalline_bulk',{'wavelength_um':w,'temperature_K':295,'locator':'CHARMS Table7; uncertainty Table6'},'measured');r[-1]['uncertainty']={'value':unc,'unit':'1','note':'原论文所列特定测量不确定度，置信定义沿用原文'}
    for prop,v,u,cond in [('refractive_index_n',4.0026,'1',{'wavelength_um':11,'temperature':'not_reported'}),('mass_density',5.33,'g/cm3',{}),('thermal_conductivity',58.62,'W/(m K)',{'temperature_K':293}),('linear_expansion',6.1e-6,'1/K',{'temperature_K':298}),('specific_heat',310,'J/(kg K)',{})]:add('Ge_substrate',prop,v,u,'M10','crystalline_bulk',cond)
    add('Ge_substrate','absorption_coefficient',.027,'1/cm','M10','optical_crystal',{'wavelength_um':10.6,'grade':'not_reported','temperature':'not_reported'},'limit','<')
    return r
def integrate_records():
    records=[]
    for filename in ['oxide_property_records.json','ir_property_records.json']:
        for i,r in enumerate(json.loads((ROOT/'data'/filename).read_text())['records'],1):
            r=dict(r);r.setdefault('record_id',f'IRP-{i:03}')
            r['state']=r.get('sample_state',r['conditions'].get('state',r['conditions'].get('material_state','see_conditions_and_source_card')))
            original=r.get('status');r['original_status']=original
            if r['value'] is None:r['status']='unknown';r.setdefault('unknown_reason',r.get('notes','see uncertainty and source card'))
            elif r.get('eligible_for_pure_material_default') is False or (original and 'quarant' in original):r['status']='quarantined'
            elif r.get('conflict_flag') or (original and 'conflict' in original):r['status']='comparison_only'
            elif r.get('bound_type') or original=='upper_bound':r['status']='limit';r['qualifier']=r.get('value_qualifier',r['conditions'].get('comparison','<' if r.get('bound_type')=='strict_upper_bound' else '<='))
            elif r.get('model_derived'):r['status']='model'
            elif original=='published_experiment':r['status']='measured'
            elif original in ['catalog_typical','separate_supplier_record','supplier_process_range']:r['status']='typical'
            else:r['status']='literature_reference'
            r['design_ready']=False;r['registry_origin']=filename
            records.append(r)
    records.extend(metal_records())
    save('data/property_records.json',dict(schema_version='1.0',frozen_at='2026-10-02',scope='Conditioned reference records, not a complete certified material database',records=records))
    return records
if __name__=='__main__':
    s=integrate_sources();m=integrate_cards(s);r=integrate_records();print(f'{len(m)} cards; {len(s)} sources; {len(r)} conditioned records')
