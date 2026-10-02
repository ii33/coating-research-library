"""Strict, stdlib-only T04R2 contract validation and bounded arithmetic.
No material-response prediction, device access, optimization or qualification.
"""
from __future__ import annotations
import json, math
from pathlib import Path
E_CHARGE=1.602176634e-19  # exact J/eV, SI definition
N_A=6.02214076e23        # exact mol^-1, SI definition
ROOT=Path(__file__).resolve().parents[1]
AXES=('source','time','space','geometry','kernel','input','model')
class ContractError(ValueError):pass

def schema_errors(x,s,path='$',root=None):
    """Subset engine for EVERY keyword emitted by build_schema.py.
    Rejects unknown assertion keywords so schema expansion cannot silently weaken validation.
    """
    root=s if root is None else root
    known={'$schema','$id','$defs','title','type','properties','required','additionalProperties','items','minItems','maxItems','minLength','minimum','maximum','exclusiveMinimum','enum','const','anyOf','$ref'}
    if set(s)-known:raise ContractError('unsupported schema keywords: '+str(set(s)-known))
    if '$ref' in s:
        target=root
        for p in s['$ref'][2:].split('/'):target=target[p]
        return schema_errors(x,target,path,root)
    if 'anyOf' in s and not any(not schema_errors(x,a,path,root) for a in s['anyOf']):return [path+': no anyOf branch matches']
    errors=[]
    def equal(a,b):return (type(a) is type(b) or type(a) in (int,float) and type(b) in (int,float)) and a==b
    if 'const' in s and not equal(x,s['const']):errors.append(path+': const mismatch')
    if 'enum' in s and not any(equal(x,v) for v in s['enum']):errors.append(path+': enum mismatch')
    check={'object':lambda: isinstance(x,dict),'array':lambda:isinstance(x,list),'string':lambda:isinstance(x,str),'null':lambda:x is None,'boolean':lambda:type(x) is bool,'integer':lambda:type(x) is int,'number':lambda:type(x) in (int,float) and math.isfinite(x)}
    types=s.get('type');types=[types] if isinstance(types,str) else types
    if types and not any(check[t]() for t in types):return errors+[path+': type/finite mismatch']
    if isinstance(x,dict):
        for k in s.get('required',[]):
            if k not in x:errors.append(path+'.'+k+': required missing')
        for k,v in x.items():
            if k in s.get('properties',{}):errors+=schema_errors(v,s['properties'][k],path+'.'+k,root)
            elif s.get('additionalProperties') is False:errors.append(path+'.'+k+': unknown field')
            elif isinstance(s.get('additionalProperties'),dict):errors+=schema_errors(v,s['additionalProperties'],path+'.'+k,root)
    if isinstance(x,list):
        if len(x)<s.get('minItems',0) or len(x)>s.get('maxItems',math.inf):errors.append(path+': array length')
        if 'items' in s:
            for i,v in enumerate(x):errors+=schema_errors(v,s['items'],f'{path}[{i}]',root)
    if isinstance(x,str) and len(x)<s.get('minLength',0):errors.append(path+': string length')
    if type(x) in (float,int):
        if x<s.get('minimum',-math.inf) or x>s.get('maximum',math.inf) or x<=s.get('exclusiveMinimum',-math.inf):errors.append(path+': numeric range')
    return errors

def _quantities(x,path='$'):
    if isinstance(x,dict):
        if 'interval_kind' in x and 'unit' in x:yield path,x
        else:
            for k,v in x.items():yield from _quantities(v,path+'.'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from _quantities(v,f'{path}[{i}]')

def validate(record):
    schema=json.loads((ROOT/'data/material_response.schema.json').read_text())
    errors=schema_errors(record,schema)
    if errors:return errors
    def err(msg):errors.append(msg)
    def unit(q,u,p):
        if q['unit']!=u:err(p+': unit must be '+u)
    for p,q in _quantities(record):
        if q['status'] in ('unknown','calibration_required') and (q['value'] is not None or q['interval'] is not None or q['standard_u'] is not None):err(p+': unknown/calibration value must be null')
        if q['status'] not in ('unknown','calibration_required') and q['value'] is None:err(p+': known status requires value')
        if q['standard_u'] is not None and q['standard_u']<0:err(p+': standard uncertainty negative')
        if q['interval'] is None and q['interval_kind']!='none':err(p+': missing interval')
        if q['interval'] is not None:
            lo,hi=q['interval']
            if q['interval_kind']=='none' or lo>hi or q['value'] is None or not lo<=q['value']<=hi:err(p+': invalid interval/value')
        if q['status']=='synthetic' and record['record_role']!='synthetic_fixture':err(p+': synthetic quantity in nonsynthetic record')
        if q['status'] in ('measured','literature_reference') and not q['source_ids']:err(p+': evidence source required')
    for name in ('film','substrate'):
        m=record[name];unit(m['density'],'kg/m3',name+'.density')
        if m['density']['value'] is not None and (m['density']['value']<=0 or (m['density']['interval'] and m['density']['interval'][0]<=0)):err(name+': density must be positive')
        if m['material_id']=='H4_film' and m['identity_status']=='verified' and not all(m[k] for k in ('manufacturer','grade','lot')):err('H4: verified identity needs manufacturer/grade/lot')
        if 'YbF3' in m['material_id'] and m['nominal_formula']!='YbF3':err('YbF3 is not YF3')
        if m['composition_verified'] and not m['stoichiometry']:err(name+': verified composition requires stoichiometry in v1')
        for e,q in m['element_molar_mass_kg_mol'].items():
            unit(q,'kg/mol',name+'.atomic_mass.'+e)
            if q['value'] is not None and (q['value']<=0 or q['interval'] is not None and q['interval'][0]<=0):err(name+': atomic molar mass value and bounds must be positive')
    if record['film']['physical_state']!='thin_film' or record['substrate']['physical_state']!='bulk_substrate':err('film/substrate physical state mismatch')
    unit(record['initial_thickness'],'m','initial_thickness')
    for e,q in record['initial_inventory_atoms_m2'].items():
        unit(q,'atoms/m2','initial_inventory.'+e)
        if q['value'] is not None and (q['value']<0 or q['interval'] is not None and q['interval'][0]<0):err('negative initial inventory value or bound')
    if record['record_role']=='measured_campaign' and not record['provenance']['measurement_ids']:err('measured campaign requires measurement provenance')
    end=None
    for b in record['bins']:
        if end is not None and abs(b['t_start_s']-end)>1e-9*max(1,abs(end)):err('time bins must be contiguous, ordered and nonoverlapping')
        end=b['t_start_s']+b['dt_s']
        if b['neutral_inventory']=='included' and not any(beam['charge_number']==0 for beam in b['beams']):err('included neutral inventory requires neutral component')
        unit(b['surface_temperature'],'K','temperature');unit(b['surface_potential'],'V','surface_potential');unit(b['reactive_gas_partial_pressure'],'Pa','gas pressure')
        if b['surface_temperature']['value'] is not None and b['surface_temperature']['value']<=0:err('temperature must be absolute positive')
        for e,q in b['net_element_flux'].items():unit(q,'atoms/m2/s','net_flux.'+e)
        for beam in b['beams']:
            for c in beam['cells']:
                unit(c['flux'],'particles/m2/s','cell.flux');unit(c['energy'],'eV/particle','cell.energy');unit(c['theta'],'deg_from_normal','cell.theta');unit(c['phi'],'deg_about_normal','cell.phi')
                if beam['azimuth_policy']=='resolved' and c['phi']['value'] is None:err('resolved azimuth requires phi')
                if beam['azimuth_policy']=='axisymmetric_assumed_for_fixture' and record['record_role']!='synthetic_fixture':err('fixture azimuth assumption cannot transfer to real campaign')
                if c['phi']['value'] is not None and not 0<=c['phi']['value']<360:err('phi in [0,360) required')
                for k in ('flux','energy'):
                    if c[k]['value'] is not None and (c[k]['value']<0 or c[k]['interval'] and c[k]['interval'][0]<0):err('negative '+k)
                if c['theta']['value'] is not None and (not 0<=c['theta']['value']<=90 or c['theta']['interval'] and not 0<=c['theta']['interval'][0]<=c['theta']['interval'][1]<=90):err('angle must be incident 0..90 from normal')
    for y in record['resputter_yield_records']:
        for domain in ('energy_domain_eV','angle_domain_deg','temperature_domain_K','fluence_domain_m2'):
            if y[domain] is not None and y[domain][0]>y[domain][1]:err('yield domain unordered')
            if y['state'] in ('calibrated','literature_reference','synthetic') and y[domain] is None:err('numeric yield needs complete domain')
        if y['state'] in ('calibrated','literature_reference') and not y['evidence_source_ids']:err('yield evidence missing')
        for q in y['values_by_element'].values():unit(q,'atoms/particle','yield')
    for r in record['response_records']:
        expected={'n':'1','k':'1','biaxial_stress':'Pa','rms_roughness':'m'}
        if r['property'] in expected:unit(r['value'],expected[r['property']],'response')
        if r['value']['value'] is not None:
            if r['evidence']=='unavailable':err('numeric response without evidence')
            if not r['value']['source_ids']:err('numeric response needs source')
            if not r['domain']['sample_ids'] or not r['domain']['validation_evidence']:err('numeric response lacks sample/domain evidence')
            if r['sample_id'] not in r['domain']['sample_ids']:err('response sample outside evidence domain')
            if r['evidence']=='validated_model' and not r['model_id']:err('model response lacks model id')
            if r['property'] in ('n','k') and (r['wavelength']['value'] is None or r['wavelength']['value']<=0):err('optical response wavelength missing')
            if r['property']=='adhesion' and (r['method']=='unknown' or r['failure_mode']=='unknown'):err('adhesion test and failure mode required')
        unit(r['wavelength'],'m','response wavelength')
    return errors

# Closed, outward-rounded interval arithmetic. Input intervals retain their own coverage semantics.
def down(x):return math.nextafter(x,-math.inf)
def up(x):return math.nextafter(x,math.inf)
def add(a,b):
    if a==(0.,0.):return b
    if b==(0.,0.):return a
    return (down(a[0]+b[0]),up(a[1]+b[1]))
def mul(a,b):
    if a==(0.,0.) or b==(0.,0.):return (0.,0.)
    v=[i*j for i in a for j in b];return (down(min(v)),up(max(v)))
def scale(a,s):return mul(a,(s,s))
def divide(a,b):
    if b[0]<=0<=b[1]:raise ContractError('denominator contains zero')
    return mul(a,(down(1/b[1]),up(1/b[0])))
def sum_iv(xs):
    xs=list(xs)
    if not xs:return (0.,0.)
    out=xs[0]
    for x in xs[1:]:out=add(out,x)
    return out

def available(q):return q['value'] is not None and q['interval'] is not None and q['status'] in ('measured','derived','synthetic')
def interval(q):
    if not available(q):raise ContractError('quantity unavailable, unbounded or reference only')
    return tuple(q['interval'])
def measure(value,iv,unit,status='conditional_calculation',reason=None):
    return {'value':value,'interval':list(iv) if iv is not None else None,'unit':unit,'status':status,'reason':reason}
def blocked(unit,reason):return measure(None,None,unit,'blocked',reason)

def calculate(r):
    errors=validate(r)
    if errors:raise ContractError('; '.join(errors))
    out={'record_id':r['record_id'],'production_qualified':False,'record_role':r['record_role'],
         'uncertainty_axes':r['uncertainty_axes'],'response_records':r['response_records'],
         'interval_semantics':'outward arithmetic of supplied bounds; not a probabilistic joint coverage or continuous-field certificate',
         'upstream_status':'T02 oracle partial; T03 device validation not_run; inherited without promotion',
         'blocking_reasons':[]}
    elements=set().union(*(b['net_element_flux'] for b in r['bins']))
    net_ok=r['atom_inventory_coverage']=='all_retained_elements' and (not r['film']['composition_verified'] or set(r['film']['stoichiometry'])<=elements) and bool(elements) and all(set(b['net_element_flux'])==elements and all(available(q) for q in b['net_element_flux'].values()) for b in r['bins'])
    # A matched initial inventory is mandatory to prevent erosion beyond existing film.
    inventory_ok=net_ok and elements==set(r['initial_inventory_atoms_m2']) and all(available(q) for q in r['initial_inventory_atoms_m2'].values())
    if inventory_ok:
        running={e:interval(q) for e,q in r['initial_inventory_atoms_m2'].items()}
        for b in r['bins']:
            for e in elements:
                running[e]=add(running[e],scale(interval(b['net_element_flux'][e]),b['dt_s']))
                # An interval extending negative cannot certify same material; never clip inventory at zero.
                if running[e][0] < 0:inventory_ok=False
    Niv=None;Nv=None
    if net_ok and inventory_ok:
        element_iv={e:sum_iv(scale(interval(b['net_element_flux'][e]),b['dt_s']) for b in r['bins']) for e in sorted(elements)}
        Niv=sum_iv(element_iv.values());Nv=sum(q['value']*b['dt_s'] for b in r['bins'] for q in b['net_element_flux'].values())
        out['N_net']=measure(Nv,Niv,'atoms/m2');out['net_by_element_atoms_m2']={e:list(iv) for e,iv in element_iv.items()}
    else:out['N_net']=blocked('atoms/m2','missing signed element flux/bounds or initial inventory; or possible film exhaustion')
    beam_ok=all(b['beams'] and all(available(c[k]) for beam in b['beams'] for c in beam['cells'] for k in ('flux','energy','theta')) for b in r['bins'])
    if beam_ok:
        Ds=[];Us=[];Dv=Uv=0.
        for b in r['bins']:
            for beam in b['beams']:
                for c in beam['cells']:
                    d=scale(interval(c['flux']),b['dt_s'])
                    if beam['charge_number']>0:Ds.append(d);Dv+=c['flux']['value']*b['dt_s']
                    Us.append(scale(mul(d,interval(c['energy'])),E_CHARGE));Uv+=c['flux']['value']*b['dt_s']*c['energy']['value']*E_CHARGE
        Div=sum_iv(Ds);Uiv=sum_iv(Us)
        out['D']=measure(Dv,Div,'charged_particles/m2')
        out['U_observed_components']=measure(Uv,Uiv,'J/m2',reason='only declared species; no heat-absorption equivalence')
        if all(b['neutral_inventory']!='unknown' for b in r['bins']):out['U']=measure(Uv,Uiv,'J/m2')
        else:out['U']=blocked('J/m2','fast neutral inventory unknown; observed-component U is partial')
    else:
        out['D']=blocked('charged_particles/m2','joint surface energy-angle flux records/bounds missing')
        out['U']=blocked('J/m2','joint surface energy-angle flux records/bounds missing')
    film=r['film'];sto=film['stoichiometry'];mass=film['element_molar_mass_kg_mol']
    compatible=net_ok and sto and set(sto)==elements and film['composition_verified']
    if compatible:
        # Measured elemental inventory changes must support the declared fixed stoichiometry.
        for b in r['bins']:
            f=[divide(interval(b['net_element_flux'][e]),(sto[e],sto[e])) for e in sorted(elements)]
            if max(v[0] for v in f)>min(v[1] for v in f):compatible=False
    h_ok=Niv is not None and compatible and film['density_composition_invariant'] and film['density_basis']=='effective_film' and available(film['density']) and set(mass)==elements and all(available(q) for q in mass.values())
    if h_ok:
        nu=sum(sto.values());Miv=sum_iv(scale(interval(mass[e]),sto[e]) for e in sorted(elements));Mv=sum(mass[e]['value']*sto[e] for e in elements)
        atom_density=divide(scale(interval(film['density']),N_A*nu),Miv)
        niv=atom_density;nv=film['density']['value']*N_A*nu/Mv
        out['n_atom']=measure(nv,niv,'atoms/m3')
        out['N_formula_net']=measure(Nv/nu,divide(Niv,(nu,nu)),'formula_units/m2')
        out['h_increment']=measure(Nv/nv,divide(Niv,niv),'m',reason='signed thickness change only under invariant density/composition; not final thickness or compaction')
    else:out['h_increment']=blocked('m','requires actual effective film density, verified fixed composition, matched elemental mass and inventory, invariant state')
    status='stable_positive'
    if Niv is None:status='missing_denominator'
    elif Niv[0]<=0:status='net_erosion' if Niv[1]<0 else 'zero_or_crossing_zero'
    elif Niv[1]-Niv[0]>=Niv[0]:status='ill_conditioned'
    out['ratio_conditioning']=status
    for key,num,unit_ in [('R','D','charged_particles/net_atom'),('epsilon','U','eV/net_atom')]:
        if status=='stable_positive' and out[num]['value'] is not None:
            factor=1/E_CHARGE if key=='epsilon' else 1.
            out[key]=measure(out[num]['value']*factor/Nv,divide(scale(tuple(out[num]['interval']),factor),Niv),unit_)
        elif status=='ill_conditioned' and out[num]['value'] is not None:
            factor=1/E_CHARGE if key=='epsilon' else 1.
            out[key]=blocked(unit_,'ill-conditioned positive denominator; diagnostic interval only, not stable response coordinate')
            out[key]['diagnostic_interval']=list(divide(scale(tuple(out[num]['interval']),factor),Niv))
        else:out[key]=blocked(unit_,status if status!='stable_positive' else out[num]['reason'])
    for k in r['requested_outputs']:
        if out[k]['status']=='blocked':out['blocking_reasons'].append(k+': '+out[k]['reason'])
    out['response_prediction']='not_implemented: experimental response or explicitly validated model records only'
    out['adapter_to_T03']='blocked_signed_or_uncertain' if Niv is None or Niv[0]<0 or any(q['interval'] and q['interval'][0]<0 for b in r['bins'] for q in b['net_element_flux'].values()) else 'conditional_nonnegative_input_only'
    return out

def propagate_covariance(jacobian,covariance):
    """u_y^2 = J C J^T. C is covariance of the independent measured input vector.
    Symmetric positive semidefinite checked by LDL with zero-pivot handling.
    """
    n=len(jacobian)
    if n==0 or len(covariance)!=n or any(len(row)!=n for row in covariance):raise ContractError('covariance shape')
    if any(not math.isfinite(x) for row in covariance for x in row) or any(not math.isfinite(x) for x in jacobian):raise ContractError('nonfinite covariance/J')
    # Scale to correlation-like coordinates to make tolerances dimensionless.
    if any(covariance[i][i]<0 for i in range(n)):raise ContractError('negative variance')
    scales=[math.sqrt(covariance[i][i]) or 1. for i in range(n)]
    a=[[covariance[i][j]/scales[i]/scales[j] for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            if abs(a[i][j]-a[j][i])>1e-12:raise ContractError('covariance nonsymmetric')
    L=[[0.]*n for _ in range(n)];d=[0.]*n
    for i in range(n):
        L[i][i]=1.;d[i]=a[i][i]-sum(L[i][k]**2*d[k] for k in range(i))
        if d[i]<-1e-12:raise ContractError('covariance not PSD')
        if abs(d[i])<1e-12:d[i]=0.
        for j in range(i+1,n):
            v=a[j][i]-sum(L[j][k]*L[i][k]*d[k] for k in range(i))
            if d[i]==0:
                if abs(v)>1e-12:raise ContractError('covariance not PSD zero pivot')
            else:L[j][i]=v/d[i]
    var=sum(jacobian[i]*covariance[i][j]*jacobian[j] for i in range(n) for j in range(n))
    return math.sqrt(max(0.,var))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('record');ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
    record=json.loads(Path(a.record).read_text());errors=validate(record)
    if errors:print(json.dumps({'valid':False,'errors':errors},ensure_ascii=False,indent=2));raise SystemExit(2)
    print(json.dumps({'valid':True} if a.validate_only else calculate(record),ensure_ascii=False,indent=2,allow_nan=False))
