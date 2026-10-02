#!/usr/bin/env python3
"""Freeze explicit T04-linked reference values into reproducible T06 examples.
Optional provenance rebuild; Al extraction requires the local-only CC0 original.
Published run_atlas.py only needs the already frozen JSON, not local originals.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from reference_tmm import coherent
ROOT=Path(__file__).resolve().parents[1]; T04=ROOT.parent/'04_coating_and_substrate_materials'
sys.path.insert(0,str(T04/'models'))
from optical_examples import read_nk,interp_nk
materials={}
def const(id,n,k,bounds,anchors,note):
 materials[id]=dict(id=id,model='constant',n=n,k=k,calculation_bounds_um=bounds,anchor_records=anchors,assumptions=note,uncertainty='not quantified; reference model only',design_ready=False)
def table(id,rows,bounds,anchors,note):
 materials[id]=dict(id=id,model='linear_table',table_wavelength_n_k=rows,calculation_bounds_um=bounds,anchor_records=anchors,assumptions=note,uncertainty='sparse interpolation has unquantified error; cannot resolve absorption bands',design_ready=False)
const('MgF2_NIR_proxy',1.375,0,[1.3,1.7],['T04:IRP-037','T04:IRP-038'],'n frozen from 1.5um catalog film; k=0 is idealization, not the <2e-5 catalog limit')
const('K9_NIR_proxy',1.501060,0,[1.3,2.0],['T04:IRP-064'],'H-K9L n at1.52958um frozen; zero interface k and alpha=0 scenario do not certify real bulk transmission')
const('K9_1064_proxy',1.506743,0,[.78,1.3],['T04:IRP-063'],'H-K9L at1.060um, frozen for 1.064um teaching filter; not all K9')
const('Ta2O5_1064_proxy',2.08,0,[.78,1.3],['T04:OXP-006'],'Spector IBS film n at1.064um frozen; k=0 assumed, not measured; no process transfer')
const('SiO2_1064_proxy',1.474,0,[.78,2.0],['T04:OXP-028'],'Spector IBS film n at1.064um frozen; k=0 assumed, no broadband certified data')
# These sparse primary tabular values are data, not a dispersion fit.
table('ZnS_IR_proxy',[[2,2.24,0],[4,2.22,0],[6,2.21,0],[8,2.19,0],[10,2.17,0],[13,2.12,0]],[3,13],['T04:IR01 p2','T06:F08 p2'],'piecewise-linear catalog n; k=0 not supplied by the table and explicitly idealized')
table('YbF3_MWIR_proxy',[[2,1.529,.0005],[5,1.509,.0015]],[3,5],['T04:IRP-015','T04:IRP-016','T04:IRP-017','T04:IRP-018'],'linear n,k between2 and5um catalog points; water peaks and process dependence unresolved')
table('Ge_MWIR_bulk_proxy',[[3,4.04579,0],[4,4.02577,0],[5,4.01678,0]],[3,5],['T04:MP-054','T04:MP-055','T04:MP-056'],'295K crystalline Ge n; k=0 at interfaces, independent bulk alpha; not Ge film')
const('Ge_dualband_ideal',4.0026,0,[3,12],['T04:MP-057'],'synthetic broad-band constant using11um bulk anchor; not measured3-12um dispersion or absorption')
const('Ge_LWIR_film_proxy',4.3,0,[8,13],['T04:M15','T04:cards/09_Ge_film.md'],'historical evaporated-film n about4.3 above6um frozen; k=0 idealization; not contemporary process data')
const('ZnSe_LWIR_bulk_proxy',2.4028,0,[8,13],['T04:IRP-085'],'10.6um bulk ZnSe n frozen; alpha=0 baseline, no thermal/loss certification')
orig=T04/'sources/originals/Al_Rakic.yml'; expected='e93b31fe821551836e5b000949c67c633b8a1ca1f2c5549f4db0f1c03b24844d'
if hashlib.sha256(orig.read_bytes()).hexdigest()!=expected: raise ValueError('Al original hash mismatch')
raw=read_nk(orig)
rows=[[w,*interp_nk(raw,w)] for w in [1.3,1.4,1.5,1.55,1.6,1.7,1.8,1.9,2.0]]
table('Al_Rakic_sparse',rows,[1.3,2.0],['T04:M07','T04:Al_Rakic CC0 dataset'],'nine wavelength-resampled points; linear interpolation of that derived sample; homogeneous metal, excludes oxide/roughness/microstructure')
materials['Al_Rakic_sparse']['original_sha256']=expected
materials['Al_Rakic_sparse']['data_license']='CC0-1.0'
# A bounded two-variable teaching search, not a global stack optimizer.
w=np.linspace(3.5,4.5,81); nL=np.interp(w,[2,5],[1.529,1.509])+1j*np.interp(w,[2,5],[.0005,.0015]); nH=np.interp(w,[2,4,6],[2.24,2.22,2.21]); ns=np.interp(w,[3,4,5],[4.04579,4.02577,4.01678]);best=None
for dl in np.linspace(.02,.80,79):
 for dh in np.linspace(.10,.70,61):
  out=coherent(w,[1,nL,nH,ns],[dl,dh]); loss=float(out['R'].max())
  if best is None or loss<best[0]:best=(loss,float(dl),float(dh))
E=[]
def add(id,title,substrate,layers,sweep,bands,angles,rear='bare',thickness_mm=3,alpha=0,note=''):
 E.append(dict(id=id,title=title,evidence='synthetic_reference_calculation_not_measured',incident_medium='air',layer_order='incident_to_substrate',substrate=substrate,substrate_mm=thickness_mm,bulk_alpha_cm_inv=alpha,bulk_alpha_status='explicit idealized scenario, not inferred from k or transmission',rear=rear,layers=[dict(material=m,thickness_um=d,thickness_nm=d*1000) for m,d in layers],wavelength_grid_um=sweep,bands_um=bands,angles_deg=angles,polarizations=['s','p'],notes=note,production_ready=False))
add('E01','NIR single-layer AR','K9_NIR_proxy',[('MgF2_NIR_proxy',1.5/(4*1.375))],[1.3,1.7,801],{'NIR':[1.3,1.7]},[0,30],rear='same',note='Both faces coated. Compare bare versus same rear; index matching is imperfect even at design center.')
add('E02','MWIR two-layer AR seed','Ge_MWIR_bulk_proxy',[('YbF3_MWIR_proxy',best[1]),('ZnS_IR_proxy',best[2])],[3,5,1201],{'design_band':[3.5,4.5],'full_MWIR':[3,5]},[0,30],rear='same',thickness_mm=5,note='Finite grid minimum of max front R over3.5-4.5um at0deg with catalog-loss YbF3. 79x61 candidate grid, no robustness or global optimum claim.')
add('E03','Dual-minimum AR counterexample','Ge_dualband_ideal',[('ZnS_IR_proxy',10/(4*2.17))],[3,12,1801],{'MWIR':[3,5],'LWIR':[8,12]},[0,30],rear='same',thickness_mm=5,note='A low-R minimum near10um and its short-wave odd-order minimum do NOT give broadband dual-band AR. Deliberate finite-band failure example; not optimized.')
add('E04','LWIR dielectric HR and notch seed','ZnSe_LWIR_bulk_proxy',[('Ge_LWIR_film_proxy',10/(4*4.3)),('ZnS_IR_proxy',10/(4*2.17))]*5,[8,13,1201],{'HR_band':[9,11],'long_edge':[12,13]},[0,45],rear='bare',note='Five HL pairs at10um. Same stack can act as reflective notch only if transmission in both external passbands is separately verified.')
layers=[('Ta2O5_1064_proxy',1.064/(4*2.08)),('SiO2_1064_proxy',1.064/(4*1.474))]*4+[('Ta2O5_1064_proxy',1.064/(2*2.08))]+[('SiO2_1064_proxy',1.064/(4*1.474)),('Ta2O5_1064_proxy',1.064/(4*2.08))]*4
add('E05','NIR one-cavity bandpass seed','K9_1064_proxy',layers,[.78,1.3,10401],{'pass_core':[1.059,1.069],'left_block':[.97,1.00],'right_block':[1.13,1.16]},[0,10,30,45],rear='bare',note='(HL)^4 2H (LH)^4, lambda0=1.064um. Single cavity lacks remote blocking; specified pass core stays fixed when evaluating angular shift.')
add('E06','Protected Al NIR mirror seed','K9_NIR_proxy',[('SiO2_1064_proxy',.10),('Al_Rakic_sparse',.12)],[1.3,2.,1001],{'NIR':[1.3,2.]},[0,45],rear='bare',note='Hypothetical 100nm silica-like cap /120nm Al. No oxide, adhesion or durability claim; physical optical stack includes metal absorption.')
(ROOT/'data/material_proxies.json').write_text(json.dumps(dict(schema_version='1.0',warning='Every dielectric model has explicit approximations; calculation bounds are not evidence of physical validity.',materials=materials),ensure_ascii=False,indent=2)+'\n')
(ROOT/'data/starter_stacks.json').write_text(json.dumps(dict(schema_version='1.0',created='2026-10-02',two_layer_seed_search=dict(objective='minimum sampled maximum front R',band_um=[3.5,4.5],grid_n=81,dL_um=[.02,.8,79],dH_um=[.1,.7,61],best_max_R=best[0]),examples=E),ensure_ascii=False,indent=2)+'\n')
print('6 stacks;',len(materials),'material proxies; E02 seed',best)
