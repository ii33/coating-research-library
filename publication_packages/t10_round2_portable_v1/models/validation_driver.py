"""Offline/device-data validation driver. Default only emits a plan.

No serial, USB, TCP, vendor commands, power control, instrument scanning or user
computer access is implemented. Device protocol identity and permission are absent.
The implemented driver accepts exported evidence packets, not live device access.
"""
from pathlib import Path
import argparse,json,hashlib,itertools,time,platform
import numpy as np
from ion_observables import *
from evidence_contract import validate_packet
ROOT=Path(__file__).resolve().parents[1]


def plan():
    factors={'theta_deg':[0,20,40],'charge_z':[1,2],'neutral_fraction':[0,0.2,0.5],
             'current_noise_relative':[0.002,0.01,0.03],'seed':[2301,2302,2303,2304]}
    cases=math.prod(len(v) for v in factors.values())
    return {'mode':'plan_only','status':'not_run_awaiting_device','factors':factors,'case_count':cases,
            'replicates_per_case':200,'inverse_solve_upper_bound':cases*200,
            'max_iterations_per_inverse':100,'random_engine':'numpy PCG64 explicit case seed',
            'wall_budget_s':1800,'failure_policy':'Preserve each failed solve; never count failed or nonidentifiable cases as valid coverage',
            'planned_outputs':['per-case conditions and seed','per-replicate solver status','conditional flux bias','declared-noise covariance check','failure count; no production confidence guarantee'],
            'actual_device_validation':'not_run_awaiting_device','live_hardware_adapter':'not_implemented_missing_verified_protocol_and_authorization',
            'heavy_execution_authorized_in_this_round':False,
            'stages':[{'name':'ideal_response_sweep','status':'not_run_awaiting_device'},{'name':'empirical_response_fit','status':'not_run_awaiting_device'},{'name':'actual_exported_packet_check','status':'not_run_awaiting_device'},{'name':'real_device_or_production_validation','status':'not_run_awaiting_device'}]}


def reference_cases():
    # All numerical values below are synthetic, not suggested process settings.
    ch=[Cell(8e17,100,1),Cell(2e17,200,2)]
    m=moments(ch,'complete_conditional')
    charge_q=kinetic_flux_from_charge_spectrum([E_CHARGE*8e17,E_CHARGE*2*2e17],[100,100])
    cx_ch=[Cell(8e17,100,1),Cell(2e17,100,0)]
    cx=moments(cx_ch,'complete_conditional')
    angular=[Cell(1e18,100,1,math.pi/3)]
    a=rfea_matrix(angular,[0,20,30,90],np.ones((4,1)))
    # Two monoenergetic populations at 50/150 eV: threshold 100 separates them.
    basis=[Cell(0,50,1),Cell(0,150,1)]
    b=rfea_matrix(basis,[0,100],np.ones((2,2)))
    truth=np.array([2e18,1e18]); y=b@truth; s=np.array([.005,.005])
    inv=invert_nonnegative(b,y,np.diag(s*s))
    ambiguity=rfea_matrix([Cell(0,100,1),Cell(0,200,2)],[0,50,150],np.ones((3,2)))
    # Same 100 eV/charge, so charge contributions remain inseparable.
    timeline=[{'t0_s':0,'t1_s':2,'ion':1e18,'net':2e18},{'t0_s':2,'t1_s':3,'ion':1e18,'net':0}]
    d=time_integrate(timeline,'ion',0,3);n=time_integrate(timeline,'net',0,3)
    norms={name:net_normalization(d,40,40,bounds) for name,bounds in {'positive':[3.9e18,4.1e18],'zero':[0,0],'crossing':[-1e17,1e17],'erosion':[-2e18,-1e18],'ill_conditioned':[1e17,3e17]}.items()}
    depleted=net_normalization(d,40,40,[3e18,4e18],{'O':[1e17,2e17]},{'O':[[-2e17,-1e17],[2e18,3e18]]})
    # Features fixed before final scores. All synthetic runs independent by construction.
    rows=[]
    for i,(x,t,h,split) in enumerate([(0,0,0,'fit'),(1,0,0,'fit'),(0,1,0,'fit'),(0,0,1,'fit'),(1,1,1,'selection'),(.4,.7,.2,'final')]):
        rows.append({'sample_id':f's{i}','run_id':f'r{i}','split':split,'operator_id':'n_at_declared_lambda_fixed_operator','material_state_id':'synthetic_state','features':[1,x,t,h],'value':1.5+.01*x-.002*t+.004*h,'standard_uncertainty':.001})
    fit=grouped_response_fit(rows,'n_at_declared_lambda_fixed_operator','synthetic_state')
    # Correlated gain cancels in ratio: derivative [1,-1] in log coordinates.
    corr=propagate_linear([[1,-1]],[[.04,.02],[.02,.04]])[0,0]
    fixtures={p.stem:validate_packet(json.loads(p.read_text())) for p in sorted((ROOT/'examples').glob('*.json')) if p.name in {'actual_unknown.json','synthetic_complete.json'}}
    return {'data_origin':'synthetic_only','mixed_charge':{'moments':m,'charge_spectrum_power_w_m2':charge_q,'naive_j_over_e':m['ion_current_a_m2']/E_CHARGE},
            'charge_exchange':cx,'angle_60deg':{'total_energy_ev':100,'normal_energy_ev':25,'rfea_currents_a_m2':(a@np.array([1e18])).tolist()},
            'identifiable_two_bins':inv,'same_energy_per_charge_ambiguity':response_rank(ambiguity),
            'timeline':{'dose_m2':d,'net_atoms_m2':n,'integral_ratio':d/n,'ion_only_duration_s':1},
            'normalization_cases':norms,'transient_inventory_depletion':depleted,'synthetic_response_fit':fit,'correlated_log_ratio_variance':float(corr),'fixture_checks':fixtures,
            'actual_hardware':'not_run_awaiting_device','heavy_sweep':'not_run_awaiting_device'}


def full_synthetic_sweep(config, wall_budget_s=None):
    """Fully implemented deferred batch, bounded in time and iterations.
    This function is not called by default or by this round's tiny tests.
    """
    start=time.monotonic();limit=config['wall_budget_s'] if wall_budget_s is None else finite(wall_budget_s,'wall budget',0,True)
    f=config['factors'];ledger=[];terminated=False
    for theta,z,neutral,noise,seed in itertools.product(*(f[k] for k in ['theta_deg','charge_z','neutral_fraction','current_noise_relative','seed'])):
        rng=np.random.default_rng(seed);th=math.radians(theta)
        cells=[Cell(0,50*z,z,th),Cell(0,150*z,z,th)]
        barriers=[0,100*math.cos(th)**2]
        a=rfea_matrix(cells,barriers,np.ones((2,2)))
        truth=np.array([2e18,1e18])*(1-neutral);mean=a@truth;std=noise*np.maximum(mean,1e-12)
        case={'theta_deg':theta,'charge_z':z,'neutral_fraction':neutral,'noise_relative':noise,'seed':seed,'replicates':[]}
        for rep in range(config['replicates_per_case']):
            if time.monotonic()-start>=limit: terminated=True;break
            measured=mean+rng.normal(size=2)*std
            solve=invert_nonnegative(a,measured,np.diag(std*std),config['max_iterations_per_inverse'])
            result={'replicate':rep,'status':solve['status'],'iterations':solve['iterations']}
            if solve['flux_m2_s'] is not None:
                result['relative_flux_error']=(np.array(solve['flux_m2_s'])/truth-1).tolist()
            case['replicates'].append(result)
        ledger.append(case)
        if terminated: break
    return {'status':'budget_exhausted' if terminated else 'completed_synthetic_only','elapsed_s':time.monotonic()-start,'ledger':ledger,'actual_device_validation':'not_run_awaiting_device','qualification':False}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['plan_only','tiny_synthetic','full_synthetic','offline_packet'],default='plan_only');ap.add_argument('--input',type=Path);ap.add_argument('--raw-root',type=Path);ap.add_argument('--out',type=Path);ap.add_argument('--execute-deferred-synthetic',action='store_true');ap.add_argument('--wall-budget-s',type=float)
    args=ap.parse_args()
    if args.mode=='plan_only': result=plan()
    elif args.mode=='tiny_synthetic': result=reference_cases()
    elif args.mode=='offline_packet':
        if args.input is None: ap.error('--input is required')
        result={'input_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'check':validate_packet(json.loads(args.input.read_text()),args.raw_root),'device_validation':'not_run_awaiting_device'}
    else:
        if not args.execute_deferred_synthetic: ap.error('Explicit --execute-deferred-synthetic required; heavy work deferred this round')
        result=full_synthetic_sweep(plan(),args.wall_budget_s)
    result['environment']={'python':platform.python_version(),'numpy':np.__version__}
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.out:
        if args.out.exists(): ap.error('Output already exists; preserve execution evidence and choose a new path')
        args.out.write_text(payload)
    else: print(payload,end='')
if __name__=='__main__':main()
