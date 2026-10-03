"""ITO conditional bookkeeping reference; SI units; no process-to-carrier prediction."""
import math
NA = 6.02214076e23
KB = 1.380649e-23
M = {'In': .114818, 'Sn': .118710, 'O': .015999}

def finite(x, name, positive=False):
    if not isinstance(x, (int,float)) or not math.isfinite(x) or (x <= 0 if positive else x < 0):
        raise ValueError(name + ' must be finite and ' + ('positive' if positive else 'nonnegative'))
    return x

def source_wt_to_cation_fraction(sn_o2_mass_fraction):
    w=finite(sn_o2_mass_fraction,'SnO2 mass fraction')
    if w>1: raise ValueError('mass fraction exceeds 1')
    ns=w/(M['Sn']+2*M['O']); ni=2*(1-w)/(2*M['In']+3*M['O'])
    return ns/(ns+ni)

def gas_impingement(pressure_pa, temperature_k, particle_mass_kg):
    p=finite(pressure_pa,'pressure');t=finite(temperature_k,'temperature',True)
    m=finite(particle_mass_kg,'particle mass',True)
    return p/math.sqrt(2*math.pi*m*KB*t)

def cosine_point_flux(total_particles_s, exponent, source_cos, receiver_cos, distance_m, visibility=1):
    q=finite(total_particles_s,'rate');n=finite(exponent,'exponent');r=finite(distance_m,'distance',True)
    v=finite(visibility,'visibility')
    if v>1 or not -1<=source_cos<=1 or not -1<=receiver_cos<=1: raise ValueError('geometry bounds')
    if source_cos<=0 or receiver_cos<=0: return 0.0
    return q*(n+1)/(2*math.pi)*source_cos**n*receiver_cos*v/r**2

def inventory_step(inventory_atoms_m2, net_flux_atoms_m2_s, dt_s):
    dt=finite(dt_s,'time step')
    if set(inventory_atoms_m2)!=set(net_flux_atoms_m2_s): raise ValueError('element sets differ')
    out={}
    for e,a in inventory_atoms_m2.items():
        finite(a,'inventory')
        f=net_flux_atoms_m2_s[e]
        if not math.isfinite(f): raise ValueError('nonfinite flux')
        out[e]=a+f*dt
        if out[e]<0: raise ValueError('film inventory exhausted: '+e)
    return out

def mass_per_area(inventory_atoms_m2):
    if set(inventory_atoms_m2)!=set(M): raise ValueError('requires explicit In, Sn, O inventory')
    return sum(finite(a,'inventory')*M[e]/NA for e,a in inventory_atoms_m2.items())

def conditional_thickness(inventory_atoms_m2, density_kg_m3, *, inventory_complete):
    if inventory_complete is not True: raise ValueError('partial elemental inventory')
    return mass_per_area(inventory_atoms_m2)/finite(density_kg_m3,'actual effective film density',True)

def actual_unknown_record():
    return {'schema_version':'ito-material-state-v0.1', 'sample_id':'actual_unmeasured',
            'status':'blocked_missing_measurements','synthetic':False,
            'element_net_inventory_atoms_m2':None,'effective_density_kg_m3':None,
            'thickness_m':None,'carrier_density_m3':None,'mobility_dc_m2_Vs':None,
            'optical_dispersion':None,'production_qualified':False}

if __name__=='__main__':
    import json
    print(json.dumps({'synthetic':True,'source_Sn_cation_fraction_from_90_10_wt':source_wt_to_cation_fraction(.1),
      'O2_impingement_example_particles_m2_s':gas_impingement(5e-5*133.32236842105263,300,2*M['O']/NA),
      'example_assumptions':'Ideal thermal O2 at 300 K; pressure merely illustrative, incorporation not predicted',
      'actual_template':actual_unknown_record()},indent=2))
