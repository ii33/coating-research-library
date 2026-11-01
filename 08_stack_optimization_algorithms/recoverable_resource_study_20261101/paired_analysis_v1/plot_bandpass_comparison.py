"""Dense sampled visualization, not a continuous certificate or model prediction."""
from pathlib import Path
import argparse,csv,gzip,io,json,sys,hashlib
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--baseline',required=True);p.add_argument('--variant',required=True);p.add_argument('--checks',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    baseline=Path(a.baseline);variant=Path(a.variant);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(baseline))
    from core_bridge import configure_core,CORE_COMMIT
    configure_core(a.repo)
    from coat_sim.core.optical_constants import prepare_optical_set
    from coat_sim.core.film_synthesis_absorption import sample_synthesis_optical
    from coat_sim.core.film_optics import coherent_rta
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,3,figsize=(12.5,7.2),sharey=True)
    records=[];margins=[]
    for rownum,case in enumerate(['train-41000-bandpass','train-41001-bandpass']):
        task=json.loads((variant/'cases'/case/'input.json').read_text());request=task['request']
        result=json.loads((variant/'cases'/case/'result.json').read_text())
        new=json.loads((variant/'cases'/case/'witnesses'/(result['selected_hash']+'.json')).read_text())
        old=json.loads((Path(a.checks)/(case+'.json')).read_text())
        samplers={(m['id'],o['id']):prepare_optical_set(o,k_sampling_policy='source') for m in request['frozen_material_snapshot']['materials'] for o in m['optical_sets']}
        def response(design,objective,waves):
            layers=list(reversed(design['front_layers']));names=[(l['material_id'],l['optical_set_id']) for l in layers]
            substrate=request['environment']['substrate'];sub=(substrate['material_id'],substrate['optical_set_id'])
            indices={key:np.array([complex(*sample_synthesis_optical(samplers[key],float(w),assume_unknown_k_zero=False)[:2]) for w in waves]) for key in set(names+[sub])}
            matrix=np.column_stack([np.ones(len(waves)),*[indices[key] for key in names],indices[sub]])
            thickness=np.array([l['thickness']['value'] for l in layers]);answers=[]
            for angle in objective['angles_deg']:
                pols=('s','p') if objective['polarization']=='unpolarized' else (objective['polarization'],)
                answers.append(np.mean([coherent_rta(waves,matrix,thickness,angle_deg=angle,polarization=pol)[objective['metric']] for pol in pols],axis=0))
            return np.min(answers,axis=0)
        for oi,objective in enumerate(request['objectives']):
            criterion=objective['pointwise'];assert criterion['enabled'] and criterion['lower_bound'] is not None and not objective['mean']['enabled']
            extras=[]
            for audit in (new['audit'],old['audit']):
                report=audit['candidate_reports'][0]['objective_status'][oi]['pointwise']
                extras.extend(x['worst_wavelength_nm'] for x in report['angles'] if x.get('worst_wavelength_nm') is not None)
            waves=np.unique(np.r_[np.linspace(objective['wavelength_min_nm'],objective['wavelength_max_nm'],4097),extras])
            oldcurve=response(old['selected_trial']['candidate_design'],objective,waves);newcurve=response(new['design'],objective,waves)
            bound=criterion['lower_bound'];ax=axes[rownum,oi]
            ax.axhspan(bound*100,100,color='#009E73',alpha=.065)
            ax.plot(waves,oldcurve*100,color='#888888',ls='--',lw=.9)
            ax.plot(waves,newcurve*100,color='#0072B2',lw=1.6)
            ax.axhline(bound*100,color='#D55E00',ls=':',lw=1.4)
            ax.set_xlim(waves[0],waves[-1]);ax.set_ylim(0,101);ax.grid(axis='y',alpha=.18)
            ax.set_title(f"{case.split('-')[1]} | {objective['metric']} window {oi+1}")
            ax.set_xlabel('Wavelength (nm)')
            if oi==0:ax.set_ylabel('Response (%)')
            ax.text(.03,.05,f"new: {result['layer_count']} layers, {result['total_thickness_nm']/1000:.3f} um",transform=ax.transAxes,fontsize=9,color='#0072B2')
            delta=float(np.min(newcurve)-bound)
            margins.append(dict(case_id=case,objective_index=oi,metric=objective['metric'],sampled_points=len(waves),new_min=float(min(newcurve)),required_lower=bound,strict=criterion['strict_lower'],new_min_minus_bound=delta))
            for w,o,n in zip(waves,oldcurve,newcurve):records.append([case,oi,objective['metric'],format(float(w),'.17g'),format(float(o),'.17g'),format(float(n),'.17g'),format(bound,'.17g'),objective['polarization']])
    fig.suptitle('Paired synthetic R/T/R tasks: native structural priors',fontsize=16,y=.985)
    fig.text(.5,.943,'Same original goals and sources; curves show the minimum over requested incidence angles',ha='center',fontsize=10,color='#555555')
    handles=[Line2D([0],[0],color='#888888',ls='--',lw=1.3,label='Old best fit-grid candidate (failed audit)'),Line2D([0],[0],color='#0072B2',lw=1.8,label='Native-prior design (audited)'),Line2D([0],[0],color='#D55E00',ls=':',lw=1.4,label='Required lower bound')]
    fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.025),fontsize=9)
    fig.text(.5,.005,'Sampled visualization only. Neither a continuous certificate nor minimum-resource or forecast-accuracy evidence.',ha='center',fontsize=9,color='#555555')
    fig.tight_layout(rect=(0,.08,1,.92))
    fig.savefig(out/'bandpass-comparison.png',dpi=160,facecolor='white')
    fig.savefig(out/'bandpass-comparison.svg',facecolor='white')
    buffer=io.StringIO(newline='');writer=csv.writer(buffer);writer.writerow(['case_id','objective_index','metric','wavelength_nm','old_candidate_min_over_angles','new_design_min_over_angles','lower_bound','polarization']);writer.writerows(records)
    with open(out/'sampled-curves.csv.gz','wb') as handle:
        with gzip.GzipFile(fileobj=handle,mode='wb',mtime=0) as compressed:compressed.write(buffer.getvalue().encode())
    (out/'plot-check.json').write_text(json.dumps(dict(core_commit=CORE_COMMIT,rows=len(records),window_checks=margins,
        caveat='Plot sampling4097 plus stored audit extrema; not a substitute for original audits. Prior candidate selected posthoc by old fit-grid error.'),indent=2,allow_nan=False))
    print(json.dumps(margins),flush=True)

if __name__=='__main__':main()
