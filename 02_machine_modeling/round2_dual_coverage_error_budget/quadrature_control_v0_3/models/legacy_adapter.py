"""T02 R2 bounded synthetic adapter. No device inputs, optimization or controls.
The copied modules are byte-identical frozen references; only this adapter is new.
"""
from pathlib import Path
from copy import deepcopy
import sys, json, time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'frozen'))
import t01_dual_coverage as t01
import t02_deposition_reference as t02
import t05_source_reference as t05
from t10_ion_assist_reference import E_CHARGE
ROOT=Path(__file__).resolve().parents[1]
SOURCE_LEVELS=[(2,7),(3,13),(5,23)]
TIME_LEVELS=[127,509,1531]
SPACE_LEVELS=[(2,9,17),(4,17,33),(6,29,61)]

class Budget:
    def __init__(self,limit=150_000_000,seconds=180):
        self.limit=limit;self.seconds=seconds;self.rays=0;self.start=time.monotonic()
    def add(self,n):
        if self.rays+n>self.limit: raise RuntimeError('pre-registered ray budget exceeded')
        if time.monotonic()-self.start>self.seconds: raise RuntimeError('pre-registered wall-clock budget exceeded')
        self.rays+=int(n)
    def report(self):
        return {'ray_evaluations':self.rays,'ray_limit':self.limit,'wall_seconds':time.monotonic()-self.start,'wall_limit_seconds':self.seconds}

def config():
    c=json.loads((ROOT/'data/t01_contract.json').read_text())
    c['schema_version']='T02-R2-dual-finite-1.0'
    c['topologies']={'D':c['topologies']['D']}
    c['vapor'].update(kind='finite_disk_cosine',radius_m=.035,exponent=1.,total_atoms_s=2e19*.6**2*np.pi)
    c['ion'].update(kind='finite_disk_ballistic_lobe',radius_m=.045,exponent=12.,total_ions_s=5e18)
    c['plates']['vapor_plate']['thickness_m']=.02
    c['plates']['ion_plate']['thickness_m']=.03
    c['cases']={'both':['vapor_plate','ion_plate'],'none':[]}
    c['excluded_physics']=['C/I topology','CFD/PIC','space charge','beam optics','collisions and scattering','multiple charge states','fast neutrals','energy spread','resputtering','temperature and material response','real machine calibration','moving plates and arbitrary CAD']
    return c

def normals_unit(n):
    n=np.asarray(n,dtype=float)
    if not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n,axis=-1),1,rtol=0,atol=1e-12):
        raise ValueError('receiver normals must be finite unit vectors')
    return n

def pose(c,t,p,n=None):
    if set(c['topologies'])!={'D'}: raise ValueError('adapter admits direct external D only')
    if n is not None: normals_unit(n)
    return t01.pose(c,'D',t,p,n)

def plates(c,case):
    out=[]
    for name in c['cases'][case]:
        p=c['plates'][name]
        if p['owner_frame']!='L' or set(p['opaque_to'])!={'vapor','ion'}: raise ValueError('static ordinary opaque plates only')
        Q=np.column_stack([p['basis_u_L'],p['basis_v_L'],p['normal_L']])
        out.append(t02.RectangleMask(p['origin_L_m'],Q,*p['half_width_m'],p['thickness_m']))
    return out

def emitter(c,channel,nr,na,family='gauss'):
    q=c[channel]
    if channel=='vapor': center=q['position_L_m']; Q=np.eye(3)
    else:
        center=q['origin_L_m'];Q=np.column_stack([q['basis_u_L'],q['basis_v_L'],q['direction_L']])
    if family=='gauss':
        return t02.disk_source(q['radius_m'],nr,na,center,Q,q['exponent'])
    if family!='equal_area': raise ValueError('unknown source quadrature')
    # Independent source quadrature family already frozen in T05.
    s=t05.disk_source(q['radius_m'],nr,na,q['exponent'])
    return t02.Source(s.nodes_m@Q.T+center,s.normals@Q.T,s.fractions,s.exponent)

def integrate(c,points,panels,nr,na,case='both',family='gauss',budget=None):
    points=np.atleast_2d(points); vg=c['clock']['vapor_gate_s'];ig=c['clock']['ion_gate_s']
    ts,ws=t02.time_quadrature(c['clock']['layer_start_s'],c['clock']['layer_end_s'],panels,1,vg+ig)
    sv=emitter(c,'vapor',nr,na,family);si=emitter(c,'ion',nr,na,family);ms=plates(c,case)
    acc=np.zeros((len(points),4))
    for k in range(0,len(ts),16):
        t=ts[k:k+16];w=ws[k:k+16]
        if budget: budget.add(len(t)*len(points)*(len(sv.fractions)+len(si.fractions)))
        x,n=pose(c,t,points)
        gv=c['vapor']['total_atoms_s']*t02.transfer_kernel(x,n,sv,ms)
        gi=c['ion']['total_ions_s']*t02.transfer_kernel(x,n,si,ms)
        gv*=((t>=vg[0])&(t<vg[1]))[:,None]
        gi*=((t>=ig[0])&(t<ig[1]))[:,None]
        acc[:,0]+=w@gv;acc[:,1]+=w@gi
        acc[:,2]+=w@gi*c['ion']['energy_per_ion_eV']*E_CHARGE
        acc[:,3]+=w@((gi>0)&(gv==0))
    return acc,{'time_nodes':len(ts),'source_nodes_each':nr*na,'point_count':len(points),'source_family':family}

def diagnostic_points():
    a=np.arange(12)*2*np.pi/12
    return np.vstack([[0,0,0],np.column_stack([.06*np.cos(a),.06*np.sin(a),np.zeros(12)])])

def grid(level):
    return t01.disk_grid(.06,*SPACE_LEVELS[level])

def metrics(c,a,w):
    z=t01.output_values(c,a)
    out={}
    for key,v in z.items():
        st=t01.statistics(v,w)
        st['finite_area_fraction']=float(np.sum(np.asarray(w)[np.isfinite(v)])/np.sum(w))
        st['nonfinite_witness_count']=int(np.sum(~np.isfinite(v)))
        out[key]=st
    return out

def compare(a,b):
    # b is comparison estimate, NOT exact truth. First 3 have physical units.
    diff=np.abs(a[:,:3]-b[:,:3]); scale=np.mean(np.abs(b[:,:3]),axis=0)
    relative=np.divide(diff,scale,out=np.zeros_like(diff),where=scale>0)
    # A nonzero discrepancy against a zero scale is undefined, never an apparent pass.
    invalid=np.any((scale==0)&np.any(diff>0,axis=0))
    return {'max_relative_integral_difference':float('inf') if invalid else float(relative.max()),
            'ion_only_max_difference_s':float(np.max(np.abs(a[:,3]-b[:,3]))),
            'normalization_status':'undefined_zero_reference' if invalid else 'zero_channels_exact' if np.any(scale==0) else 'positive_reference'}

def stats_compare(a,b):
    keys=['h_nm','ion_fluence_m2','incident_energy_J_m2']
    invalid=any(a[k][f] is None or b[k][f] is None for k in keys for f in ['mean','cv','sample_pv']) or any(b[k]['mean']<=0 for k in keys)
    if invalid:
        return {'mean_relative':float('inf'),'cv_absolute':float('inf'),'sample_pv_absolute':float('inf'),'normalization_status':'undefined_or_nonpositive_reference'}
    return {'normalization_status':'positive_reference','mean_relative':max(abs(a[k]['mean']-b[k]['mean'])/b[k]['mean'] for k in keys),
            'cv_absolute':max(abs(a[k]['cv']-b[k]['cv']) for k in keys),
            'sample_pv_absolute':max(abs(a[k]['sample_pv']-b[k]['sample_pv']) for k in keys)}
