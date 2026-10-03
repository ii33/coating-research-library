"""Deterministic small synthetic counterexamples; not fitted machine parameters."""
from source_retention import *

def row(kind,theta_s_deg=0.,theta_i_deg=0.,phi_deg=0.,r_m=.5):
 return {'kind':kind,'mu_s':math.cos(math.radians(theta_s_deg)),'mu_i':math.cos(math.radians(theta_i_deg)),'phi_rad':math.radians(phi_deg),'r_m':r_m,'visibility':1.}
def design(anchors=True):
 rows=[row('qcm_mass_rate',ts,ts,ph) for ts,ph in [(0,0),(30,0),(55,0),(40,90)]]
 rows += [row('witness_thickness_rate',ts,ti,ph) for ts,ti,ph in [(20,0,0),(20,50,0),(45,15,90),(45,65,90)]]
 if anchors:rows += [{'kind':'source_mass_rate'},{'kind':'film_density'}]
 return rows

def examples():
 p=Parameters();un=design(False);anch=design(True)
 # Exact global ambiguity: planar parallel witnesses with a=0 versus a=1.
 A=Parameters(Q_kg_s=1e-6,n=3.,c=0.,eta_q=.8,s0=.7,a=0.,rho_kg_m3=2000.)
 B=replace(A,Q_kg_s=2e-6,n=1.,a=1.)
 planar=[row('witness_thickness_rate',a,a) for a in [0,15,30,45,60,70]]
 det={'angles_deg':[0,15,30,45,60,70],'A':asdict(A),'B':asdict(B),'parallel_A':[prediction(r,A) for r in planar],'parallel_B':[prediction(r,B) for r in planar],'axis_QCM_A':prediction(row('qcm_mass_rate'),A),'axis_QCM_B':prediction(row('qcm_mass_rate'),B),'tilted_witness_A':prediction(row('witness_thickness_rate',45,0),A),'tilted_witness_B':prediction(row('witness_thickness_rate',45,0),B),'off_axis_QCM_A':prediction(row('qcm_mass_rate',45,45),A),'off_axis_QCM_B':prediction(row('qcm_mass_rate',45,45),B)}
 pair=[row('witness_mass_rate',30,x) for x in [0,60]]
 paired=paired_retention_a(prediction(pair[0],p),prediction(pair[1],p),pair[0]['mu_i'],pair[1]['mu_i'])
 J=log_jacobian(anch,p)
 # A new independent capture parameter for every QCM (first replaces shared column).
 J_free=np.column_stack([J[:,[0,1,2,4,5,6]],np.array([[1. if i==j else 0. for j in range(4)] for i in range(len(anch))])])
 # R3 genuinely separates time definitions, never shifts q with pose offset.
 clocks={'baseline':two_clocks(1.,0.,0.,1.,.2,0.,.1),'pose_only_shift':two_clocks(1.,0.,.5,1.,.2,0.,.1),'source_only_shift':two_clocks(1.,.5,0.,1.,.2,0.,.1)}
 r=t04.Response(source_scale_kg_s=None,angular_a=(.4,.4))
 bridge=bridge_t04(t04.Scene(),r,(2e-6,2e-6),panels=16)
 unknown=bridge_t04(t04.Scene(),replace(r,sticking_s0=None),None,panels=8)
 negative=bridge_t04(t04.Scene(),replace(r,erosion_mass_kg_m2=(1e-5,1e-5)),(2e-6,2e-6),panels=8)
 return {'dataset_kind':'synthetic_only','parameter_names':PARAMETER_NAMES,'nominal_parameters':asdict(p),'single_qcm':rank_report(log_jacobian([row('qcm_mass_rate')],p)),'unanchored_multidirection':rank_report(log_jacobian(un,p)),'anchored_multidirection':rank_report(J),'independent_capture_each_qcm':rank_report(J_free),'exact_global_ambiguity':det,'paired_tilt':paired,'clock_separation':clocks,'t04_lambert_bridge':bridge,'t04_unknown':unknown,'t04_negative_net':negative,'real_parameters':'unknown','formal_model_chain':'pending'}

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();Path(a.output).write_text(json.dumps(examples(),indent=2,allow_nan=False)+'\n')
