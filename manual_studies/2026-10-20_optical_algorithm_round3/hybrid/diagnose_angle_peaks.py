#!/usr/bin/env python3
"""Post-hoc local angle-extremum diagnostics, not continuous certification."""
import json
import numpy as np
from scipy.optimize import minimize_scalar
import run_hybrid as h

def main():
    path=h.ROOT/'results'/'results.json';rs=json.loads(path.read_text())['results'];out=[]
    for r in rs:
        a=r['audit'];delta=a['angle_envelope_dense_worst_R']-a['trained_angles_dense_worst_R']
        if delta<=1e-10:continue
        row=max(a['rows'],key=lambda x:x['max_R']);wl=row['argmax_R_um'];mats,sub=h.materials(r['case']);center=row['angle_deg'];lo=max(0.,center-5);hi=min(45.,center+5);calls=0;points=0
        def evaluate(unit):
            nonlocal calls,points
            angle=lo+unit*(hi-lo);model=h.OpticalModel(np.array([wl]),mats,sub,[angle]);R,P=model.solve(r['thickness_um']);j=next(j for j,s in enumerate(model.scenarios) if s[1]==row['polarization']);calls+=1;points+=len(model.scenarios);return -float(R[j,0])
        fit=minimize_scalar(evaluate,bounds=(0.,1.),method='bounded',options={'xatol':1e-12,'maxiter':120});angle=lo+fit.x*(hi-lo)
        out.append({'case':r['case']['name'],'method':r['method'],'seed':r['seed'],'polarization':row['polarization'],'wavelength_um_fixed':wl,'trained_angle_dense_max_R':a['trained_angles_dense_worst_R'],'five_degree_dense_max_R':a['angle_envelope_dense_worst_R'],'local_refined_angle_deg':angle,'local_refined_R':-float(fit.fun),'additional_R_over_trained_angle_max_percentage_points':100*(-float(fit.fun)-a['trained_angles_dense_worst_R']),'bounded_angle_bracket_deg':[lo,hi],'optimizer_success':bool(fit.success),'diagnostic_optical_calls':calls,'diagnostic_angle_polarization_points':points,'scope':'one wavelength fixed at the observed dense-grid peak; local angle refinement is evidence of a missed angle peak, not a global 2D or continuous-domain certificate'})
    (h.ROOT/'results'/'angle_peak_diagnostic.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
