"""Synthetic material-state bridge, not source-setting-to-property prediction."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'electro_optics'))
from reference_state import conditional_thickness
from model import DrudeLorentz,dc_conductivity,sheet_resistance,incoherent_substrate_rt
inventory={'In':2.8e21,'Sn':2.0e20,'O':4.6e21} # ALL synthetic, retained atoms/m2
thickness=conditional_thickness(inventory,7100,inventory_complete=True)
N=3e26;mu_dc=.0025;mu_opt=.0035
optical=DrudeLorentz(N,mu_opt,.35,3.9)
r=incoherent_substrate_rt(550e-9,[(optical.nk(550e-9),thickness)])
rs=sheet_resistance([(dc_conductivity(N,mu_dc),thickness)])
assert thickness>0 and rs>0 and abs(r.R+r.T+r.A-1)<1e-12 and r.A>=0
print(json.dumps({'status':'SYNTHETIC_NOT_CALIBRATED','inventory_atoms_m2':inventory,
 'effective_density_kg_m3':7100,'thickness_m':thickness,
 'independent_assumed_electrical_state':{'N_m3':N,'mu_dc_m2_Vs':mu_dc,'mu_opt_m2_Vs':mu_opt},
 'Rs_ohm_square':rs,'550nm':{'R':r.R,'T':r.T,'A':r.A},
 'limitations':['No process parameters were inverted','N and mobilities supplied separately, not derived from composition','Pure Drude finite-domain example, no fitted interband response','Normal incidence, lossless incoherent glass']},indent=2))
