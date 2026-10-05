#!/usr/bin/env python3
"""Generate and run genuine SPARTA decks; deterministic reference/checker only.

No particle transport is implemented in Python. All trajectories and collisions
are produced by the unmodified official SPARTA serial executable.
"""
from pathlib import Path
import argparse, hashlib, json, math, platform, subprocess, time
import numpy as np
from scipy import stats, special

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'vendor/sparta/src/spa_serial'
KB = 1.380649e-23  # actual pinned SPARTA SI constant, update.cpp
MASS = 6.63e-26

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def surfaces(path, refine=1):
    triangles=[]
    for z, edge, up in [(0.,.01,True),(.1,.05,False)]:
        base=[-.2,-edge,edge,.2]
        edges=np.unique(np.concatenate([np.linspace(a,b,refine+1) for a,b in zip(base[:-1],base[1:])]))
        for xa,xb in zip(edges[:-1],edges[1:]):
            for ya,yb in zip(edges[:-1],edges[1:]):
                typ = (1 if up else 2) if abs((xa+xb)/2)<edge and abs((ya+yb)/2)<edge else 3
                a=(xa,ya,z);b=(xb,ya,z);c=(xb,yb,z);d=(xa,yb,z)
                triangles += [(typ,a,b,c),(typ,a,c,d)] if up else [(typ,a,c,b),(typ,a,d,c)]
    lines=['# Study planes; type 1=source, 2=receiver, 3=loss',f'{len(triangles)} triangles','','Triangles','']
    for i,(typ,*xyz) in enumerate(triangles,1):
        lines.append(f'{i} {typ} '+' '.join(f'{v:.17g}' for p in xyz for v in p))
    path.write_text('\n'.join(lines)+'\n')
    return len(triangles)

def reference(order=24):
    # Tensor Gauss-Legendre integration of view-factor kernel, four coordinates.
    u,w=np.polynomial.legendre.leggauss(order)
    sx,sy=np.meshgrid(.01*u,.01*u,indexing='ij')
    rx,ry=np.meshgrid(.05*u,.05*u,indexing='ij')
    sw=np.outer(w,w).ravel()*.01**2
    rw=np.outer(w,w).ravel()*.05**2
    dx=rx.ravel()[None,:]-sx.ravel()[:,None]
    dy=ry.ravel()[None,:]-sy.ravel()[:,None]
    kernel=.1**2/(np.pi*(.1**2+dx*dx+dy*dy)**2)
    return float(np.sum(sw[:,None]*rw[None,:]*kernel)/.02**2)

def frames(path):
    if not path.exists(): raise FileNotFoundError(path)
    with path.open() as f:
        while True:
            line=f.readline()
            if not line:break
            if line.strip()!='ITEM: TIMESTEP':raise ValueError((path,line))
            step=int(f.readline()); label=f.readline().strip(); n=int(f.readline())
            # Box dimensions then the data header.
            line=f.readline().strip()
            if line.startswith('ITEM: BOX BOUNDS'):
                for _ in range(3):f.readline()
                line=f.readline().strip()
            cols=line.split()[2:]
            data=np.array([[float(x) for x in f.readline().split()] for _ in range(n)])
            yield step,cols,data.reshape(n,len(cols))

def statrows(path):
    # Stats have known numeric columns. Repeated step 500 at run boundary is kept
    # once, so instantaneous exits are never counted twice.
    rows={}
    for line in path.read_text().splitlines():
        tok=line.split()
        if len(tok)==7:
            try:
                vals=[float(x) for x in tok]
                if vals[0].is_integer(): rows.setdefault(int(vals[0]),vals)
            except ValueError:pass
    return [rows[k] for k in sorted(rows) if k>0]

def run(case, deck, meta):
    directory=ROOT/'results'/case;directory.mkdir(parents=True,exist_ok=True)
    (directory/'in.sparta').write_text(deck)
    save(directory/'input_contract.json',meta)
    start=time.perf_counter()
    with (directory/'console.log').open('w') as f:
        p=subprocess.run([str(EXE),'-in','in.sparta','-log','log.sparta'],cwd=directory,stdout=f,stderr=subprocess.STDOUT,timeout=180)
    meta['command']=[str(EXE),'-in','in.sparta','-log','log.sparta']
    meta['working_directory']=str(directory)
    meta['replay_from_study_root']=f'(cd results/{case} && ../../vendor/sparta/src/spa_serial -in in.sparta -log log.sparta)'
    meta['elapsed_seconds']=time.perf_counter()-start;meta['returncode']=p.returncode
    save(directory/'execution.json',meta)
    if p.returncode:raise RuntimeError(f'{case}: SPARTA exited {p.returncode}; read console.log')
    return directory

def geometry(case='geometry_base',grid=10,dt=1e-5,fnum=1e10,refine=1,seed=18457,injection=False,natural_flux=False):
    surf=ROOT/'inputs'/f'surfaces_{refine}.dat'; ntri=surfaces(surf,refine)
    n=50000 if injection else 200*dt/1e-5*1e10/fnum
    emit_steps=1 if injection else round(.005/dt)
    drain_steps=0 if injection else round(.015/dt)
    dt=1e-12 if injection else dt
    source_nrho=5e18
    natural_expected=source_nrho*.02**2*math.sqrt(KB*300/(2*math.pi*MASS))*dt*emit_steps/fnum
    insertion=f'fix inlet emit/surf source source n {n:.17g} perspecies no normal no' if not natural_flux else 'fix inlet emit/surf source source perspecies yes normal no'
    deck=f'''# SYNTHETIC method validation, genuine SPARTA collisionnone.
seed {seed}
dimension 3
units si
boundary oo oo oo
create_box -.2 .2 -.2 .2 0 .1
create_grid {grid} {grid} {max(1,grid//2)}
global fnum {fnum:.17g} nrho 1e18 gridcut 0
species ../../inputs/synthetic.species A
mixture source A temp 300 vstream 0 0 0 nrho {source_nrho:.17g}
read_surf ../../inputs/{surf.name} type
group source surf type 1
group receiver surf type 2
group arrival surf subtract all source
surf_collide absorber specular
surf_react capture global 1 0
surf_modify all collide absorber react capture
collide none
{insertion}
compute hits surf/reaction/tally arrival source id/surf xc yc zc vx/pre vy/pre vz/pre
dump events tally all 1 surface.tally c_hits[*]
dump_modify events format float %.17g
timestep {dt:.17g}
stats 1
stats_style step np nexit nscoll ncoll f_inlet[1] f_inlet[2]
stats_modify format float %.17g
'''
    if injection:deck+='dump injected particle source 1 injected.dump id type x y z vx vy vz\ndump_modify injected format float %.17g\n'
    deck+=f'run {emit_steps}\n'
    if drain_steps:
        deck+='unfix inlet\nvariable zero equal 0\nstats_style step np nexit nscoll ncoll v_zero v_zero\n'
        deck+=f'run {drain_steps}\n'
    directory=run(case,deck,dict(kind='thermal_injection' if injection else 'free_molecular_geometry',data_origin='synthetic',seed=seed,grid=[grid,grid,max(1,grid//2)],dt=dt,fnum=fnum,surface_refine=refine,ntri=ntri,emit_steps=emit_steps,drain_steps=drain_steps,thermal_temperature_K=300,mass_kg=MASS,emission_mode='mixture_flux' if natural_flux else 'prescribed_count_debug_n',source_mixture_nrho=source_nrho,emission_count_target_per_step=natural_expected/emit_steps if natural_flux else n,streaming_velocity=[0,0,0],source_square_halfwidth_m=.01,receiver_square_halfwidth_m=.05,separation_m=.1))
    rows=statrows(directory/'log.sparta')
    emitted=int(round(sum(r[5] for r in rows if r[0]<=emit_steps)))
    exits=int(round(sum(r[2] for r in rows)))
    scoll=int(round(sum(r[3] for r in rows)))
    final_np=int(rows[-1][1]); gascoll=int(round(sum(r[4] for r in rows)))
    blocks=list(frames(directory/'surface.tally'))
    data=np.concatenate([b[2] for b in blocks],axis=0)
    assert len(data)==scoll,(len(data),scoll)
    # Type membership is taken from original immutable input surface file.
    receiver_ids={int(line.split()[0]) for line in surf.read_text().splitlines() if len(line.split())==11 and line.split()[1]=='2'}
    capture=int(np.sum(np.isin(data[:,0],list(receiver_ids))))
    balance=emitted-exits-scoll-final_np
    output=dict(emitted=emitted,capture=capture,other_surface_loss=scoll-capture,open_boundary_escape=exits,inventory_final=final_np,flux_balance_residual_particles=balance,gas_collisions=gascoll,surface_tally_events=len(data),particle_weight_real_molecules=fnum)
    if natural_flux:
        output.update(expected_emitted_from_mixture_flux=natural_expected,emission_count_z_conservative=(emitted-natural_expected)/math.sqrt(natural_expected),emission_flux_pass=bool(abs(emitted-natural_expected)<4*math.sqrt(natural_expected)))
    if injection:
        particles=list(frames(directory/'injected.dump'))[-1][2]
        v=particles[:,-3:];speed=np.linalg.norm(v,axis=1);mu=v[:,2]/speed
        scale=math.sqrt(KB*300/MASS)
        cos_test=stats.kstest(mu,lambda q:np.clip(q,0,1)**2)
        energy=np.sum(v*v,axis=1)*MASS/(2*KB*300)
        energy_test=stats.kstest(energy,'gamma',args=(2,))
        phi=np.mod(np.arctan2(v[:,1],v[:,0]),2*np.pi)/(2*np.pi)
        phi_test=stats.kstest(phi,'uniform')
        correlation=float(np.corrcoef(mu,energy)[0,1])
        output.update(injection_count=len(v),mu_mean=float(np.mean(mu)),mu_expected=2/3,mu_ks_D=float(cos_test.statistic),mu_ks_p=float(cos_test.pvalue),energy_over_kT_mean=float(np.mean(energy)),energy_expected=2,energy_ks_D=float(energy_test.statistic),energy_ks_p=float(energy_test.pvalue),azimuth_ks_p=float(phi_test.pvalue),energy_mu_correlation=correlation,vz2_over_thermal_variance=float(np.mean(v[:,2]**2)/scale**2),vt2_over_thermal_variance=float(np.mean(v[:,0]**2+v[:,1]**2)/scale**2),source_position_bounds=[particles[:,2:5].min(axis=0).tolist(),particles[:,2:5].max(axis=0).tolist()],emission_distribution_pass=bool(cos_test.pvalue>.001 and energy_test.pvalue>.001 and phi_test.pvalue>.001 and abs(correlation)<4/math.sqrt(len(v)) and np.all(mu>0)))
    else:
        exact=reference(); frac=capture/emitted
        ci=stats.binomtest(capture,emitted).proportion_ci(confidence_level=.95,method='exact')
        sigma=math.sqrt(exact*(1-exact)/emitted)
        output.update(reference_capture_fraction=exact,capture_fraction=frac,confidence_interval_95=[float(ci.low),float(ci.high)],inventory_fraction=final_np/emitted,relative_error=(frac-exact)/exact,z_error=(frac-exact)/sigma,geometry_pass=bool(abs(frac-exact)<=max(.01*exact,4*sigma)+final_np/emitted and balance==0 and gascoll==0))
    save(directory/'checked_results.json',output)
    return output

def bath(case='bath_static',tau=.1,temperature=1e-10,grid=10,dt=1e-7,weight=1e8,seed=97343,bgmass=6.63e-20,velocity=1000.):
    # Periodic homogeneous bath has no open exits and therefore no pressure decay.
    # Very heavy/very cold bath is a numerical static-target LIMIT, not exact T=0.
    length=.01;volume=.01*.002*.002;density=1e20;sigma=tau/(density*length)
    duration=length/velocity;nsteps=round(duration/dt);diam=math.sqrt(sigma/math.pi)
    species=f'A 39.948 {MASS:.17g} 0 0 0 0 0 1 0\nB {bgmass/1.66053906660e-27:.17g} {bgmass:.17g} 0 0 0 0 0 1 0\n'
    name=f'{case}.species';(ROOT/'inputs'/name).write_text('# SYNTHETIC tracer A and bath B; not material data\n'+species)
    vss=f'# SYNTHETIC hard-sphere constant cross section; omega=.5,alpha=1\nA 1e-25 .5 300 1\nB 1e-25 .5 300 1\nA B {diam:.17g} .5 300 1\n'
    (ROOT/'inputs'/f'{case}.vss').write_text(vss)
    deck=f'''# SYNTHETIC periodic maintained bath; survival at elapsed time L/v.
seed {seed}
dimension 3
units si
boundary pp pp pp
create_box 0 .01 0 .002 0 .002
create_grid {grid} 2 2
global fnum {weight:.17g} nrho {density:.17g}
species ../../inputs/{name} A B
mixture collision A B group species temp 4800 vstream 1000 0 0
mixture background B nrho {density:.17g} temp {temperature:.17g} vstream 0 0 0
mixture beam A temp 1e-10 vstream {velocity:.17g} 0 0
collide vss collision ../../inputs/{case}.vss
collide_modify remain no vremax 0 no
create_particles background n 0
create_particles beam n 5000
compute counts count A B
compute history gas/collision/tally all all id1 id2 type1 type2 vx1/pre vy1/pre vz1/pre vx2/pre vy2/pre vz2/pre
dump collisions tally all 1 gas.tally c_history[*]
dump_modify collisions format float %.17g
dump pulse particle all {nsteps} pulse.dump id type x y z vx vy vz
dump_modify pulse format float %.17g first yes
timestep {dt:.17g}
stats 1
stats_style step np ncoll nexit c_counts[1] c_counts[2]
stats_modify format float %.17g
run {nsteps}
'''
    directory=run(case,deck,dict(kind='uniform_bath_uncollided',data_origin='synthetic',seed=seed,tau_static=tau,background_density_m3=density,background_temperature_K=temperature,background_mass_kg=bgmass,tracer_mass_kg=MASS,tracer_speed_ms=velocity,path_length_m=length,sigma_m2=sigma,collision_diameter_m=diam,omega=.5,alpha=1,grid=[grid,2,2],dt=dt,steps=nsteps,fnum=weight,bath_boundary='periodic in all directions',bath_maintained='fixed particle number in constant volume; heavy bath limit suppresses feedback',observation='collision-free fraction over elapsed L/v, not deposited fraction'))
    pulses=list(frames(directory/'pulse.dump'))
    assert pulses[0][0]==0 and pulses[-1][0]==nsteps,[(f[0],len(f[2])) for f in pulses]
    initial=pulses[0][2];final=pulses[-1][2]
    ids=initial[initial[:,1]==1,0].astype(np.int64)
    unique=len(np.unique(ids))==len(ids)
    collision_ids=set();events=0;counts_by_tracer={};valid_steps=[]
    for step,_,d in frames(directory/'gas.tally'):
        valid_steps.append(step);events+=len(d)
        for row in d:
            for j in [0,1]:
                if int(row[j+2])==1:
                    pid=int(row[j]);collision_ids.add(pid);counts_by_tracer[pid]=counts_by_tracer.get(pid,0)+1
    assert set(valid_steps)==set(range(0,nsteps+1)),valid_steps[:4]
    count0=len(ids);uncollided=count0-len(collision_ids);fraction=uncollided/count0
    collision_ids_valid=bool(collision_ids.issubset(set(ids.tolist())))
    if temperature<1e-8:
        gmean=velocity;relative_factor=1.
    else:
        a=math.sqrt(2*KB*temperature/bgmass);s=velocity/a
        gmean=a*((s+1/(2*s))*special.erf(s)+math.exp(-s*s)/math.sqrt(math.pi))
        relative_factor=gmean/velocity
    expected=math.exp(-density*sigma*gmean*dt*nsteps)
    std=math.sqrt(expected*(1-expected)/count0)
    ci=stats.binomtest(uncollided,count0).proportion_ci(.95,method='exact')
    bg0=initial[initial[:,1]==2];bg1=final[final[:,1]==2]
    t0=float(bgmass*np.mean(np.sum((bg0[:,5:8]-np.mean(bg0[:,5:8],axis=0))**2,axis=1))/(3*KB))
    t1=float(bgmass*np.mean(np.sum((bg1[:,5:8]-np.mean(bg1[:,5:8],axis=0))**2,axis=1))/(3*KB))
    final_ids=final[final[:,1]==1,0].astype(np.int64)
    id_conserved=bool(np.array_equal(np.sort(ids),np.sort(final_ids)))
    final_vel=final[final[:,1]==1,5:8]
    statcoll=[]
    for line in (directory/'log.sparta').read_text().splitlines():
        tok=line.split()
        if len(tok)==6:
            try:
                r=[float(x) for x in tok]
                if r[0].is_integer() and 0<r[0]<=nsteps:statcoll.append(r)
            except ValueError:pass
    count_consistent=bool(sum(r[2] for r in statcoll)==events and all(r[3]==0 for r in statcoll))
    output=dict(tracer_count=count0,tracer_ids_unique=unique,tracer_ids_conserved=id_conserved,collision_tracer_ids_subset_initial=collision_ids_valid,collision_tally_matches_global_count=count_consistent,collision_tally_frames=len(valid_steps),collisions_total=events,uncollided_count=uncollided,uncollided_fraction=fraction,confidence_interval_95=[float(ci.low),float(ci.high)],expected_fraction=expected,relative_speed_mean_ms=gmean,relative_speed_factor=relative_factor,z_error=(fraction-expected)/std,bath_particles_initial=len(bg0),bath_particles_final=len(bg1),bath_density_initial=len(bg0)*weight/volume,bath_density_final=len(bg1)*weight/volume,bath_thermal_temperature_initial=t0,bath_thermal_temperature_final=t1,bath_mean_velocity_initial=np.mean(bg0[:,5:8],axis=0).tolist(),bath_mean_velocity_final=np.mean(bg1[:,5:8],axis=0).tolist(),tracer_collision_count_histogram={'0':uncollided,**{str(k):sum(v==k for v in counts_by_tracer.values()) for k in sorted(set(counts_by_tracer.values()))}},tracer_final_mean_speed_ms=float(np.mean(np.linalg.norm(final_vel,axis=1))),tracer_final_mean_vx_ms=float(np.mean(final_vel[:,0])),survival_pass=bool(unique and id_conserved and collision_ids_valid and count_consistent and abs(fraction-expected)<=4*std and len(bg0)==len(bg1)))
    save(directory/'checked_results.json',output)
    return output

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['injection','geometry','bath','replicates','all'],default='all');args=parser.parse_args()
    (ROOT/'inputs'/'synthetic.species').write_text('# Synthetic inert atom; physical material identity deliberately absent\nA 39.948 6.63e-26 0 0 0 0 0 1 0\n')
    output={}
    if args.stage in ['injection','all']:output['injection']=geometry('injection',injection=True)
    if args.stage in ['geometry','all']:
        specs=[('geometry_base',{}),('geometry_mesh20',dict(grid=20)),('geometry_mesh40',dict(grid=40)),('geometry_dt_half',dict(dt=5e-6)),('geometry_dt_quarter',dict(dt=2.5e-6)),('geometry_weight_half',dict(fnum=5e9)),('geometry_weight_quarter',dict(fnum=2.5e9)),('geometry_surface2',dict(refine=2)),('geometry_surface4',dict(refine=4)),('geometry_seed2',dict(seed=76321)),('geometry_seed3',dict(seed=90217)),('geometry_physical_flux',dict(natural_flux=True))]
        for case,kwargs in specs:
            print(case,flush=True);output[case]=geometry(case,**kwargs);print(json.dumps(output[case]),flush=True)
        output['reference_convergence']={str(k):reference(k) for k in [12,24,40]}
    if args.stage in ['bath','all']:
        specs=[('bath_static_tau01',dict(tau=.1)),('bath_static_tau001',dict(tau=.01)),('bath_static_tau1',dict(tau=1)),('bath_static_tau3',dict(tau=3)),('bath_static_dt_half',dict(tau=.1,dt=5e-8)),('bath_static_dt_quarter',dict(tau=.1,dt=2.5e-8)),('bath_static_mesh20',dict(tau=.1,grid=20)),('bath_static_mesh40',dict(tau=.1,grid=40)),('bath_static_weight_half',dict(tau=.1,weight=5e7)),('bath_static_weight_quarter',dict(tau=.1,weight=2.5e7)),('bath_thermal',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.)),('bath_thermal_dt_half',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.,dt=5e-8)),('bath_thermal_dt_quarter',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.,dt=2.5e-8)),('bath_thermal_mesh20',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.,grid=20)),('bath_thermal_mesh40',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.,grid=40)),('bath_thermal_weight_half',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.,weight=5e7)),('bath_thermal_weight_quarter',dict(tau=.1,temperature=3e8,bgmass=6.63e-20,velocity=250.,weight=2.5e7))]
        for case,kwargs in specs:
            print(case,flush=True);output[case]=bath(case,**kwargs);print(json.dumps(output[case]),flush=True)
    if args.stage in ['replicates','all']:
        for seed in [18631,47389,81761,124679]:
            for thermal in [False,True]:
                case=f'bath_{"thermal" if thermal else "static"}_seed{seed}'
                kwargs=dict(tau=.1,seed=seed)
                if thermal:kwargs.update(temperature=3e8,bgmass=6.63e-20,velocity=250.)
                print(case,flush=True);output[case]=bath(case,**kwargs);print(json.dumps(output[case]),flush=True)
    save(ROOT/'results'/f'summary_{args.stage}.json',output)

if __name__=='__main__':main()
