"""Frozen-protocol diagnostic training. Never performs optical search or labels unknowns."""
from pathlib import Path
import argparse,hashlib,json,math,platform,time,sys
import numpy as np
import sklearn
from sklearn.ensemble import ExtraTreesRegressor
from features import extract_features,SCHEMA
from predictor import predict,predict_features,MODEL_SCHEMA,validate_model

PARAMETERS=dict(n_estimators=128,max_depth=6,min_samples_leaf=2,max_features=1.,bootstrap=False,
                random_state=20261101,n_jobs=1)


def dump(path,value):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('immutable output differs: '+path.name)
    else:
        with path.open('xb') as f:f.write(raw)


def export_model(estimator,names,X,training_ids):
    trees=[]
    for e in estimator.estimators_:
        t=e.tree_
        trees.append(dict(left=t.children_left.tolist(),right=t.children_right.tolist(),feature=t.feature.tolist(),
            threshold=t.threshold.tolist(),value=t.value[:,:,0].tolist()))
    return dict(schema=MODEL_SCHEMA,feature_schema=SCHEMA,feature_names=names,feature_min=X.min(axis=0).tolist(),
        feature_max=X.max(axis=0).tolist(),trees=trees,parameters=PARAMETERS,
        training_case_ids=training_ids,output_transform=['log1p(N)','log1p(D/reference_wavelength)'],
        validation_status='diagnostic_only_not_production',interval_calibration=None,
        reference_semantics='Observed joint resource pair from pinned finite-budget reference flows, not global minimum or guaranteed feasible prediction')


def metrics(rows):
    known=[r for r in rows if r['true_layers'] is not None]
    positive=[r for r in known if r['true_thickness_nm']>0]
    return dict(case_count=len(rows),scorable_count=len(known),unknown_unscored=len(rows)-len(known),
        scorable_fraction=len(known)/len(rows),
        layers_mae=float(np.mean([abs(r['estimated_layers']-r['true_layers']) for r in known])),
        layers_float_mae=float(np.mean([abs(r['estimated_layers_float']-r['true_layers']) for r in known])),
        thickness_positive_mape=float(np.mean([abs(r['estimated_thickness_nm']/r['true_thickness_nm']-1) for r in positive])),
        joint_underestimate_fraction=float(np.mean([r['estimated_layers']<r['true_layers'] or r['estimated_thickness_nm']<r['true_thickness_nm'] for r in known])),
        feature_envelope_fraction=float(np.mean([r['feature_envelope_pass'] for r in rows])),
        interval_coverage=None,interval_status='not_calibrated',
        caveat='Conditional on successful reference labels; unknown cases excluded from errors, not assigned failure or large-resource labels.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parent));p.add_argument('--verified-manifest-sha256',required=True);args=p.parse_args()
    root=Path(args.root).resolve();manifest=root/'source_manifest.json'
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=args.verified_manifest_sha256:raise ValueError('source manifest mismatch')
    declared=json.loads(manifest.read_text())
    for row in declared['files']:
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('invalid source path')
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('frozen source changed')
    protocol=json.loads((root/'protocol.json').read_text())
    if (protocol['parameters']!=PARAMETERS or protocol['sklearn_version']!=sklearn.__version__ or protocol['numpy_version']!=np.__version__ or protocol['python_version']!=platform.python_version()):raise ValueError('protocol/runtime mismatch')
    import coat_sim,subprocess
    repository=Path(coat_sim.__file__).resolve().parent.parent
    if subprocess.check_output(['git','-C',str(repository),'rev-parse','HEAD'],text=True).strip()!=protocol['core_commit']:raise ValueError('core differs from protocol')
    if subprocess.check_output(['git','-C',str(repository),'status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('core tracked files changed')
    inventory=json.loads((root/'dataset_inventory.json').read_text());parent=root.parent;cases=inventory['cases']
    tasks=[];features=[];names=None
    def verify_data_file(relative,expected):
        path=Path(relative)
        if path.is_absolute() or '..' in path.parts:raise ValueError('invalid data chain path')
        if hashlib.sha256((parent/path).read_bytes()).hexdigest()!=expected:raise ValueError('data chain changed: '+relative)
    for item in inventory['summary']['checkpoint_checks'].values():
        verify_data_file(item['manifest_path'],item['manifest_sha256'])
    for c in cases:
        verify_data_file(c['run_admission_path'],c['run_admission_sha256'])
        for witness in c['witnesses']:
            verify_data_file(witness['path'],witness['file_sha256'])
    for c in cases:
        for key in ('input','result'):
            rel=Path(c[key+'_path'])
            if rel.is_absolute() or '..' in rel.parts:raise ValueError('invalid dataset path')
            if hashlib.sha256((parent/rel).read_bytes()).hexdigest()!=c[key+'_sha256']:raise ValueError('dataset changed')
        task=json.loads((parent/c['input_path']).read_text());f=extract_features(task['request'])
        if names is None:names=f['names']
        if names!=f['names']:raise ValueError('inconsistent feature schema')
        if not math.isclose(f['reference_wavelength_nm'],c['reference_wavelength_nm'],rel_tol=1e-12):raise ValueError('reference scale mismatch')
        tasks.append(task);features.append(f)
    X=np.array([f['values'] for f in features]);known=np.array([c['selected_hash'] is not None for c in cases])
    Y=np.zeros((len(cases),2))
    for i,c in enumerate(cases):
        if known[i]:Y[i]=np.log1p([c['layer_count'],c['total_thickness_nm']/c['reference_wavelength_nm']])
        elif c['layer_count'] is not None or c['total_thickness_nm'] is not None:raise ValueError('unknown label improperly populated')
    output=root/'outputs';dump(output/'feature_matrix.json',dict(names=names,case_ids=[c['case_id'] for c in cases],values=X.tolist()))
    summaries={};parity=0.
    for scheme in ('pair_group','strict_source_component'):
        groups=[c['dataset']+':'+c['group'] if scheme=='pair_group' else c['strict_source_component_id'] for c in cases]
        predictions=[];baseline=[]
        for gi,group in enumerate(sorted(set(groups))):
            test=np.array([g==group for g in groups]);train=(~test)&known
            if not np.any(train):raise ValueError('empty training fold')
            est=ExtraTreesRegressor(**PARAMETERS).fit(X[train],Y[train])
            model=validate_model(export_model(est,names,X[train],[c['case_id'] for c,b in zip(cases,train) if b]))
            dump(output/'fold_models'/f'{scheme}-{gi}.json',model)
            raw=est.predict(X[test]);j=0
            for i in np.flatnonzero(test):
                prediction=predict(model,tasks[i]['request']);log_json=np.array(predict_features(model,X[i]))
                parity=max(parity,float(np.max(np.abs(log_json-raw[j]))));j+=1
                c=cases[i]
                row=dict(case_id=c['case_id'],family=c['family'],dataset=c['dataset'],fold=group,
                    true_layers=c['layer_count'],true_thickness_nm=c['total_thickness_nm'],
                    estimated_layers=prediction['estimated_layers'],estimated_layers_float=prediction['estimated_layers_float'],
                    estimated_thickness_nm=prediction['estimated_total_thickness_nm'],
                    feature_envelope_pass=prediction['feature_envelope_pass'],conditional_on_unknown_k=prediction['conditional_on_unknown_k'])
                predictions.append(row)
                pool=[k for k in np.flatnonzero(train) if cases[k]['family']==c['family']]
                if not pool:pool=np.flatnonzero(train).tolist()
                center=np.median(Y[pool],axis=0)
                medoid=min(pool,key=lambda k:(float(np.sum(np.abs(Y[k]-center))),cases[k]['case_id']))
                n,dnorm=np.expm1(Y[medoid]);br=dict(row);br.update(estimated_layers=cases[medoid]['layer_count'],
                    estimated_layers_float=float(n),estimated_thickness_nm=float(dnorm*c['reference_wavelength_nm']),
                    baseline_source_case=cases[medoid]['case_id']);baseline.append(br)
        dump(output/(scheme+'-predictions.json'),predictions);dump(output/(scheme+'-baseline.json'),baseline)
        summaries[scheme]=dict(folds=len(set(groups)),forest=metrics(predictions),family_medoid_baseline=metrics(baseline),
            by_family={f:metrics([r for r in predictions if r['family']==f]) for f in sorted({c['family'] for c in cases})},
            by_dataset={d:metrics([r for r in predictions if r['dataset']==d]) for d in sorted({c['dataset'] for c in cases})})
    est=ExtraTreesRegressor(**PARAMETERS).fit(X[known],Y[known]);model=validate_model(export_model(est,names,X[known],[c['case_id'] for c,b in zip(cases,known) if b]))
    dump(output/'research_model.json',model)
    for i in range(len(cases)):parity=max(parity,float(np.max(np.abs(np.array(predict_features(model,X[i]))-est.predict(X[i:i+1])[0]))))
    if parity>1e-12:raise ValueError('JSON model differs from offline estimator')
    for i in range(48):predict(model,tasks[i%len(tasks)]['request'])
    timings=[]
    for i in range(240):
        start=time.perf_counter();predict(model,tasks[i%len(tasks)]['request']);timings.append((time.perf_counter()-start)*1000)
    summary=dict(schema='resource-predictor-diagnostic-metrics-v1',case_count=len(cases),known_count=int(known.sum()),
        feature_count=len(names),parameters=PARAMETERS,split_metrics=summaries,serialization_max_abs_log_error=parity,
        runtime=dict(python=platform.python_version(),numpy=np.__version__,sklearn=sklearn.__version__,os=platform.system(),architecture=platform.machine()),
        warm_in_memory_inference_ms=dict(count=len(timings),p50=float(np.percentile(timings,50)),p95=float(np.percentile(timings,95)),max=max(timings)),
        latency_scope='Full feature extraction and JSON tree inference on in-memory frozen requests; excludes model load, imports, source I/O and GUI; no synthesis/optimization/audit',
        independent_calibration=False,blind_test=False,production_ready=False,
        limitations=['Existing data inspected before protocol; diagnostic cross-validation only','Pair-group split shares optical sources','Strict source split has only three components of sizes36,6,6','Four unknown targets remain unscored; conditional success-label bias','No intervals or coverage guarantee','No production software changed'])
    dump(output/'metrics.json',summary);dump(output/'latency_samples_ms.json',timings)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
