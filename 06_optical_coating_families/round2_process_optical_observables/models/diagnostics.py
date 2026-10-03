"""A few deterministic falsifiable examples; no broad sweep or hardware work."""
import copy,json
import numpy as np
from process_optics import ROOT,evaluate,set_parameter,alpha_to_k,Blocked
from inference import predicted,fit_synthetic,sensitivity

def load():return json.loads((ROOT/'examples/synthetic_dielectric.json').read_text())
def pure(r,A=1.8,k=0):
 r=copy.deepcopy(r);r['optical_model']['parameters'].update(A=A,B_um2=0,k=k);r['measurement'].update(wavelength_um=[.55],angle_deg=0,polarization='s',backside='semi_infinite');return r

def run():
 out={}; base=load()
 out['representative']=evaluate(json.loads((ROOT/'examples/al_reference_conditional.json').read_text()))
 n1=1.2;n2=1.52/n1;w=.55
 a=set_parameter(pure(base,n1),'thickness_scale',w/(4*n1)/.1)
 b=set_parameter(pure(base,n2),'thickness_scale',w/(4*n2)/.1)
 ra=evaluate(a);rb=evaluate(b)
 a45=copy.deepcopy(a);b45=copy.deepcopy(b);a45['measurement']['angle_deg']=45;b45['measurement']['angle_deg']=45
 out['n_d_nonuniqueness']={'n':[n1,n2],'d_um':[ra['thickness']['geometric_thickness_um'],rb['thickness']['geometric_thickness_um']],'n_d_um':[w/4,w/4],'R_normal':[ra['observables']['R_total'][0],rb['observables']['R_total'][0]],'R_45_s':[evaluate(a45)['observables']['R_total'][0],evaluate(b45)['observables']['R_total'][0]],'counterexample_scope':'one wavelength, lossless quarter-wave pair with n2=ns/n1; not a universal nd-invariance claim'}
 r=pure(base,1.8,.02)
 ps=[{'name':'A','nominal':1.8,'step':1e-4},{'name':'k','nominal':.02,'step':1e-5},{'name':'thickness_scale','nominal':1,'step':1e-4}]
 out['one_angle_one_wavelength']={'R_only':sensitivity(r,ps,['R_detected']),'R_and_T':sensitivity(r,ps,['R_detected','T_detected']),'scope':'dimension/rank at this sampling; a broadband or constrained one-angle model can have more rank'}
 y=predicted(r,[],[],['R_detected']); wrong=pure(base,1.8,0)
 fit=fit_synthetic(wrong,['R_detected'],y,[1e-4],['A'],[1.7],[1.1],[2.5])
 wrong=set_parameter(wrong,'A',fit['parameters']['A']);trueT=predicted(r,[],[],['T_detected'])[0];wrongT=predicted(wrong,[],[],['T_detected'])[0]
 out['absorption_omitted_R_only']={'fit':fit,'true_k':.02,'wrong_k':0,'true_T':trueT,'predicted_T_wrong':wrongT,'holdout_T_error':wrongT-trueT}
 r=pure(base,1.8,0);r['measurement']['scatter'].update(fraction_of_R=.04,fraction_of_T=.08)
 y=predicted(r,[],[],['R_detected','T_detected']);wrong=pure(base,1.8,.02)
 fit=fit_synthetic(wrong,['R_detected','T_detected'],y,[1e-4,1e-4],['k','thickness_scale'],[.02,1],[0,.5],[.2,1.5])
 for n,v in fit['parameters'].items():wrong=set_parameter(wrong,n,v)
 truth=evaluate(r)['observables'];fitted=evaluate(wrong)['observables']
 r['measurement']['angle_deg']=60;wrong['measurement']['angle_deg']=60
 out['scatter_misread_as_absorption']={'fit':fit,'truth_A':truth['A_absorption'][0],'truth_S_out':truth['S_out_of_specular'][0],'fitted_A_wrong':fitted['A_absorption'][0],'holdout_60deg_R_T_error':(predicted(wrong,[],[],['R_detected','T_detected'])-predicted(r,[],[],['R_detected','T_detected'])).tolist()}
 try:alpha_to_k(.5,[.55],'bulk','film')
 except Blocked as e:out['bulk_alpha_cannot_be_film']={'status':'blocked_as_expected','reason':str(e),'bulk_k_dimension_only':alpha_to_k(.5,[.55],'bulk','bulk').tolist()}
 out['unknown_cases']={p.stem:evaluate(json.loads(p.read_text())) for p in (ROOT/'examples').glob('*.json') if p.stem not in ['al_reference_conditional','synthetic_dielectric']}
 return out
if __name__=='__main__':
 x=run();(ROOT/'verification/diagnostics.json').write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in x.items() if k not in ['representative','unknown_cases','one_angle_one_wavelength']},indent=2))
