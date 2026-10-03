"""Conditional process -> inventory -> film state -> measurable optics, not calibration.
SI inventory/mass; micrometres only at the optical kernel boundary. exp(-i wt), n+ik.
"""
from pathlib import Path
import copy, json
import numpy as np
from vendor.optics_kernel import scattering, intensity_combine
ROOT=Path(__file__).resolve().parents[1]
NA=6.02214076e23
MOLAR_MASS_KG={'Al':0.0269815385,'Si':0.028085,'O':0.015999}
class Blocked(ValueError): pass

def finite(x,name,lo=None,hi=None):
    if x is None: raise Blocked(name+' unknown')
    if isinstance(x,bool) or not isinstance(x,(float,int)) or not np.isfinite(x): raise ValueError(name+' finite numeric required')
    if lo is not None and x<lo or hi is not None and x>hi: raise ValueError(name+' outside bounds')
    return float(x)

def film_inventory(record):
    """Each input flux already per actual workpiece area. No extra cos(theta).
    Erosion/depletion is not clipped. Piecewise constant state is an explicit restriction.
    """
    p=record['process']; s=record['film_state']; sto=s['stoichiometry']
    if p['net_evidence']=='unknown':raise Blocked('net retention evidence unknown')
    if not sto:raise Blocked('composition unknown')
    if not s['composition_complete']:raise Blocked('incomplete elemental inventory')
    for e,v in sto.items():
        if e not in MOLAR_MASS_KG:raise Blocked('molar mass not registered for '+e)
        if finite(v,'stoichiometry '+e,0)<=0:raise ValueError('positive stoichiometry required')
    if not s['constant_composition_density']:raise Blocked('state evolution requires endpoint mass/density model')
    if set(p['initial_inventory_atoms_m2'])!=set(sto):raise ValueError('initial element coverage mismatch')
    initial={e:finite(p['initial_inventory_atoms_m2'][e],'initial inventory '+e,0) for e in sto}
    inv=initial.copy(); net={e:0.0 for e in sto}; incoming={e:0.0 for e in sto}
    tprev=None
    for b in p['bins']:
        t0=finite(b['start_s'],'start_s',0); t1=finite(b['end_s'],'end_s',0)
        if t1<=t0 or (tprev is not None and t0!=tprev):raise ValueError('positive contiguous time bins required')
        tprev=t1; dt=t1-t0
        finite(b['temperature_K'],'process temperature_K',0)
        if set(b['incident_atoms_m2_s'])!=set(sto):raise ValueError('arrival element coverage mismatch')
        direct=b['net_atoms_m2_s']
        if direct is not None and b['balance'] is not None:raise ValueError('choose direct net or balance, never both')
        if direct is not None and set(direct)!=set(sto):raise ValueError('net element coverage mismatch')
        for e in sto:
            F=finite(b['incident_atoms_m2_s'][e],'arrival '+e,0);incoming[e]+=F*dt
            if direct is not None: g=finite(direct[e],'net flux '+e)
            else:
                terms=b['balance']
                if terms is None:raise Blocked('arrival flux is not net retention; balance missing')
                if set(terms)!=set(sto):raise ValueError('balance element coverage mismatch')
                q=terms[e]
                eta=finite(q['retained_fraction'],'retained_fraction',0,1)
                g=eta*F+finite(q['reaction_gain_atoms_m2_s'],'reaction gain',0)-finite(q['desorption_atoms_m2_s'],'desorption',0)-finite(q['resputter_atoms_m2_s'],'resputter',0)
            inv[e]+=dt*g; net[e]+=dt*g
            if inv[e]<0:raise Blocked('element depleted: '+e)
    formula=[inv[e]/sto[e] for e in sto]
    if not np.allclose(formula,formula[0],rtol=1e-8,atol=0):raise Blocked('final composition differs from declared stoichiometry')
    rho=s['density_kg_m3']
    if s['density_basis'] not in ('measured_film','synthetic_film'):raise Blocked('bulk/source/QCM density cannot replace film density')
    rho=finite(rho,'film density_kg_m3',0)
    if rho==0:raise ValueError('positive density required')
    mass=sum(inv[e]*MOLAR_MASS_KG[e]/NA for e in sto)
    d=mass/rho*1e6
    qcm=p['qcm']
    if qcm is None:qcm_d=None
    else:
        qmass=finite(qcm['sensor_mass_kg_m2'],'QCM mass',0);qrho=finite(qcm['display_density_kg_m3'],'QCM display density',0)
        if qrho==0:raise ValueError('positive QCM display density required')
        qcm_d=qmass/qrho*1e6
    return {'arrival_atoms_m2':incoming,'net_change_atoms_m2':net,'final_inventory_atoms_m2':inv,'areal_mass_kg_m2':mass,'geometric_thickness_um':d,'qcm_equivalent_thickness_um':qcm_d,'design_thickness_um':record['design']['layer_thickness_um'],'net_mode':p['net_evidence'],'production_qualified':False}

def silica_index(wavelength_um):
    w=np.asarray(wavelength_um,float)
    if np.any(w<0.21) or np.any(w>3.71):raise Blocked('Malitson public bulk wavelength domain exceeded')
    B=np.array([0.6961663,0.4079426,0.8974794]); C=np.array([0.0684043,0.1162414,9.896161])**2
    return np.sqrt(1+np.sum(B[:,None]*w[None,:]**2/(w[None,:]**2-C[:,None]),axis=0))

def film_index(record,wavelength_um):
    s=record['film_state'];o=record['optical_model'];w=np.asarray(wavelength_um,float)
    finite(s['measurement_temperature_K'],'measurement temperature_K',0)
    if s['composition_complete'] is not True or s['stoichiometry'] is None:raise Blocked('film composition unknown')
    if s['state_id'] is None:raise Blocked('film state unknown')
    if o['binding']=='unknown':raise Blocked('no justified film n/k binding')
    if o['binding']=='same_sample' and s['sample_id']!=o['sample_id']:raise Blocked('n/k sample mismatch')
    if o['binding']=='assumed_transfer' and not record['exploratory_only']:raise Blocked('assumed material transfer cannot be qualification')
    if o['source_class']=='public_bulk':raise Blocked('public bulk n/k cannot silently become film response')
    if s['state_id']!=o['valid_state_id']:raise Blocked('film state outside source applicability')
    if not o['temperature_range_K'][0]<=s['measurement_temperature_K']<=o['temperature_range_K'][1]:raise Blocked('film measurement temperature outside model domain')
    if np.any(w<o['wavelength_range_um'][0]) or np.any(w>o['wavelength_range_um'][1]):raise Blocked('n/k wavelength extrapolation forbidden')
    if o['kind']=='al_mcpeak_table':
        if o['source_class']!='public_film' or o['source_id'] not in ('PO-S01','PO-S02'):raise Blocked('Al table provenance binding invalid')
        if s['stoichiometry']!={'Al':1}:raise Blocked('Al data used for another composition')
        table=np.array(json.loads((ROOT/'data/al_mcpeak_derived.json').read_text())['rows'])
        if np.any(w<table[0,0]) or np.any(w>table[-1,0]):raise Blocked('derived table range exceeded')
        return np.interp(w,table[:,0],table[:,1])+1j*np.interp(w,table[:,0],table[:,2])
    if o['kind']=='synthetic_cauchy':
        if record['evidence_kind']!='synthetic' or o['source_class']!='synthetic':raise Blocked('invented Cauchy coefficients must remain synthetic')
        A,B,k=[finite(o['parameters'][n],n,0) for n in ['A','B_um2','k']]
        if A<=0:raise ValueError('positive Cauchy A required')
        return A+B/w**2+1j*k
    raise Blocked('unimplemented optical model')

def observable_at(record,w,angle,pol,d):
    """Real-index substrate interface plus separately modeled bulk alpha; small-loss
    radiative-transfer approximation, not exact absorbing-interface composition.
    Scatter is an explicit output redistribution toy, not a roughness Maxwell solver.
    """
    m=record['measurement'];sub=record['substrate'];n=film_index(record,w)
    if sub['kind']=='silica_bulk_malitson':
        if sub['temperature_K']!=293.15:raise Blocked('Malitson temperature fixed at 20 C')
        ns=silica_index(w)
    elif sub['kind']=='synthetic_constant':
        if record['evidence_kind']!='synthetic':raise Blocked('synthetic substrate must be labeled')
        ns=np.full(len(w),finite(sub['n'],'substrate n',1))
    else:raise Blocked('unsupported substrate index')
    front=scattering(w,[1,n,ns],[d],angle,pol)
    if m['backside']=='semi_infinite':
        R,T=front['R'],front['T'];Afilm=front['A'];Abulk=np.zeros(len(w));sem='T is flux entering substrate, not external transmitted light'
    elif m['backside']=='incoherent_finite_all_orders':
        if sub['bulk_absorption_basis'] not in ('synthetic_bulk','measured_bulk'):raise Blocked('bulk alpha evidence missing')
        alpha=finite(sub['bulk_alpha_per_m'],'bulk alpha',0);L=finite(sub['thickness_m'],'substrate thickness',0)
        theta=np.rad2deg(np.arcsin(np.sin(np.deg2rad(angle))/ns))
        # Dispersion means each wavelength has its own reverse angle.
        rr=[];tt=[];aa=[];bf=[];ba=[]
        for i,x in enumerate(w):
            f={k:front[k][i:i+1] for k in ['R','T','A']}
            rev=scattering([x],[ns[i],n[i],1],[d],float(theta[i]),pol)
            rear=scattering([x],[ns[i],1],[],float(theta[i]),pol)
            p=np.exp(-alpha*L/np.cos(np.deg2rad(theta[i])))
            c=intensity_combine(f,rev,rear,p)
            den=1-rev['R'][0]*rear['R'][0]*p*p
            film_abs=f['A'][0]+f['T'][0]*rear['R'][0]*p*p/den*rev['A'][0]
            bulk_abs=f['T'][0]*(1-p)*(1+rear['R'][0]*p)/den
            rr.append(c['R'][0]);tt.append(c['T'][0]);aa.append(c['A'][0]);bf.append(film_abs);ba.append(bulk_abs)
        R,T=np.array(rr),np.array(tt);Afilm,Abulk=np.array(bf),np.array(ba)
        sem='T is external transmitted flux; all incoherent internal round trips collected'
    else:raise Blocked('backside/coherence unsupported')
    sc=m['scatter']
    fr=finite(sc['fraction_of_R'],'scatter fraction R',0,1);ft=finite(sc['fraction_of_T'],'scatter fraction T',0,1)
    if sc['basis'] not in ('synthetic_redistribution','measured_redistribution'):raise Blocked('scatter model unknown')
    if sc['basis']=='synthetic_redistribution' and not record['exploratory_only']:raise Blocked('synthetic scatter is exploratory only')
    sr,st=R*fr,T*ft;Rs,Ts=R-sr,T-st
    er=finite(m['detector']['diffuse_R_collection'],'R diffuse collection',0,1);et=finite(m['detector']['diffuse_T_collection'],'T diffuse collection',0,1)
    A=1-R-T
    if not np.allclose(A,Afilm+Abulk,atol=5e-10,rtol=1e-8):raise FloatingPointError('absorption accounting mismatch')
    return {'R_total':R,'T_total':T,'R_specular':Rs,'T_specular':Ts,'R_detected':Rs+er*sr,'T_detected':Ts+et*st,'A_absorption':A,'A_film':Afilm,'A_bulk':Abulk,'S_out_of_specular':sr+st,'L_specular':1-Rs-Ts,'transmission_meaning':sem}

def spectrum(record):
    """Declared finite detector quadrature, no implicit bandwidth/NA convolution."""
    inv=film_inventory(record);m=record['measurement']; centers=np.asarray(m['wavelength_um'],float)
    if centers.ndim!=1 or not len(centers) or np.any(~np.isfinite(centers)) or np.any(centers<=0):raise ValueError('positive finite wavelengths required')
    def nodes(key):
        n=m[key]; weights=np.array([a['weight'] for a in n],float)
        if not len(n) or np.any(~np.isfinite(weights)) or np.any(weights<0) or not np.isclose(sum(weights),1,atol=1e-12,rtol=0):raise ValueError(key+' weights must sum to one')
        return n
    waves=nodes('bandpass_nodes');angles=nodes('angle_nodes')
    pols={'s':[(1,'s')],'p':[(1,'p')],'unpolarized':[(.5,'s'),(.5,'p')]}[m['polarization']]
    acc={};meaning=None
    for b in waves:
        w=centers+finite(b['offset_um'],'bandpass offset')
        for a in angles:
            angle=finite(m['angle_deg'],'angle',0,89.8)+finite(a['offset_deg'],'angle offset')
            for weight,pol in pols:
                out=observable_at(record,w,angle,pol,inv['geometric_thickness_um']); ww=b['weight']*a['weight']*weight
                meaning=out.pop('transmission_meaning')
                for k,v in out.items():acc[k]=acc.get(k,0)+ww*v
    N=film_index(record,centers)
    return {'status':'conditional_calculation','evidence_kind':record['evidence_kind'],'production_qualified':False,'thickness':inv,'optical_thickness_n_d_um':(N.real*inv['geometric_thickness_um']).tolist(),'extinction_path_k_d_um':(N.imag*inv['geometric_thickness_um']).tolist(),'wavelength_um':centers.tolist(),'observables':{k:v.tolist() for k,v in acc.items()},'transmission_meaning':meaning,'measurement_id':m['id'],'warnings':['conditional material binding; not a process calibration','A=1-Rtotal-Ttotal; specular deficit includes scatter','bulk alpha and film k are distinct evidence quantities']}

def evaluate(record):
    validate(record)
    try:return spectrum(record)
    except Blocked as e:return {'status':'blocked_unknown_or_inapplicable','reason':str(e),'production_qualified':False}

def validate(record):
    from jsonschema import Draft202012Validator
    schema=json.loads((ROOT/'data/process_optics.schema.json').read_text())
    Draft202012Validator(schema).validate(record)

def set_parameter(record,name,value):
    r=copy.deepcopy(record)
    if name=='thickness_scale':
        for e in r['process']['initial_inventory_atoms_m2']:r['process']['initial_inventory_atoms_m2'][e]*=value
        for b in r['process']['bins']:
            if b['net_atoms_m2_s'] is None:raise ValueError('thickness_scale needs direct net fixture')
            for e in b['net_atoms_m2_s']:b['net_atoms_m2_s'][e]*=value
    elif name in ('A','B_um2','k'):r['optical_model']['parameters'][name]=value
    elif name=='density_kg_m3':r['film_state']['density_kg_m3']=value
    elif name=='bulk_alpha_per_m':r['substrate']['bulk_alpha_per_m']=value
    elif name=='scatter_R':r['measurement']['scatter']['fraction_of_R']=value
    elif name=='scatter_T':r['measurement']['scatter']['fraction_of_T']=value
    else:raise ValueError('unsupported parameter '+name)
    return r

def alpha_to_k(alpha_per_m,wavelength_um,evidence_scope,target_scope):
    """Unit identity only, not a bulk->film material transfer model."""
    if evidence_scope!=target_scope:raise Blocked('bulk absorption is not film extinction evidence')
    if evidence_scope not in ('bulk','film'):raise ValueError('scope bulk or film required')
    alpha=finite(alpha_per_m,'alpha_per_m',0)
    w=np.asarray(wavelength_um,float)
    if np.any(~np.isfinite(w)) or np.any(w<=0):raise ValueError('positive wavelength required')
    return alpha*w*1e-6/(4*np.pi)
