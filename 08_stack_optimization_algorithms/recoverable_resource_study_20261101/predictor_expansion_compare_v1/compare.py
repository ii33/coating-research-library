"""Fixed-model augmentation diagnostic; literature task labels never enter fitting."""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent
PROTOCOL_SHA='f9472bcea5035f511ec2209a75281da340e1186adaff8b3e34114b0c1f7f3be9'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verified-expansion-manifest-sha256',required=True)
    parser.add_argument('--verified-source-manifest-sha256',required=True)
    args=parser.parse_args()
    if sha(ROOT/'protocol.json')!=PROTOCOL_SHA:raise ValueError('comparison protocol changed')
    if sha(ROOT/'source_manifest.json')!=args.verified_source_manifest_sha256:raise ValueError('comparison source manifest changed')
    for entry in json.loads((ROOT/'source_manifest.json').read_text())['files']:
        relative=Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('invalid comparison source path')
        if sha(ROOT/relative)!=entry['sha256']:raise ValueError('comparison source changed')
    protocol=json.loads((ROOT/'protocol.json').read_text())
    original=PARENT/'predictor_pilot_v1';expansion=PARENT/'material_expansion_v1'
    if sha(original/'source_manifest.json')!=protocol['source_model_manifest_sha256']:raise ValueError('original source manifest changed')
    for entry in json.loads((original/'source_manifest.json').read_text())['files']:
        if sha(original/entry['path'])!=entry['sha256']:raise ValueError('original source changed')
    if sha(expansion/'plan.json')!=protocol['expansion_plan_sha256'] or sha(expansion/'source_manifest.json')!=protocol['expansion_source_manifest_sha256']:raise ValueError('expansion source identity changed')
    for entry in json.loads((expansion/'source_manifest.json').read_text())['files']:
        relative=Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('invalid expansion source path')
        if sha(expansion/relative)!=entry['sha256']:raise ValueError('predeclared expansion source/input changed')
    final_manifest=PARENT/'material_expansion_v1_checkpoints/batch-02.json'
    if sha(final_manifest)!=args.verified_expansion_manifest_sha256:raise ValueError('complete data checkpoint changed')
    sys.path.insert(0,str(expansion));sys.path.insert(0,str(original))
    from artifact_store import verify_manifest,canonical_json
    if not verify_manifest(PARENT,'material_expansion_v1_checkpoints/batch-02.json'):raise ValueError('data checkpoint invalid')
    from features import extract_features
    from predictor import predict,predict_features,validate_model,load_model
    from train_evaluate import PARAMETERS,export_model,metrics,dump
    from sklearn.ensemble import ExtraTreesRegressor
    import sklearn,platform,coat_sim,subprocess
    frozen_protocol=json.loads((original/'protocol.json').read_text())
    if (sklearn.__version__!=frozen_protocol['sklearn_version'] or np.__version__!=frozen_protocol['numpy_version']
            or platform.python_version()!=frozen_protocol['python_version'] or PARAMETERS!=frozen_protocol['parameters']):raise ValueError('runtime/parameters changed')
    core=Path(coat_sim.__file__).resolve().parent.parent
    if subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True).strip()!=frozen_protocol['core_commit']:raise ValueError('physical feature core changed')
    if subprocess.check_output(['git','-C',str(core),'status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('physical feature core dirty')
    inventory=json.loads((original/'dataset_inventory.json').read_text())
    for row in inventory['cases']:
        for kind in ('input','result','run_admission'):
            if sha(PARENT/row[kind+'_path'])!=row[kind+'_sha256']:raise ValueError('old evidence changed')
        for w in row['witnesses']:
            if sha(PARENT/w['path'])!=w['file_sha256']:raise ValueError('old witness changed')
    old_output_manifest=PARENT/'predictor_pilot_v1_checkpoints/outputs-01.json'
    if sha(old_output_manifest)!='758b0d2430e12a79c01653f8cb6c74854457772d3fce7aa9d55cd692eb4f0c57':raise ValueError('original output manifest changed')
    old_outputs=json.loads(old_output_manifest.read_text())
    model_path='outputs/fold_models/strict_source_component-0.json'
    model_entry=next(e for e in old_outputs['files'] if e['path']==model_path)
    baseline=load_model(original/model_path,model_entry['sha256'])
    old_cases={r['case_id']:r for r in inventory['cases']}
    original_training_ids=baseline['training_case_ids']
    expected_old={r['case_id'] for r in inventory['cases'] if r['dataset']=='pilot_v4a'}
    if len(original_training_ids)!=12 or set(original_training_ids)!=expected_old:raise ValueError('old baseline includes literature or unexpected labels')
    def row_for_old(row):
        task=json.loads((PARENT/row['input_path']).read_text())
        return dict(task=task,result=json.loads((PARENT/row['result_path']).read_text()),dataset=row['dataset'])
    train=[row_for_old(old_cases[i]) for i in original_training_ids]
    test=[row_for_old(r) for r in inventory['cases'] if r['dataset']=='material_pilot_v1a']
    expansion_rows=[];plan=json.loads((expansion/'plan.json').read_text())
    if len(plan['case_ids'])!=48 or len(set(plan['case_ids']))!=48:raise ValueError('all48 declared expansion cases required')
    if {p.name for p in (expansion/'cases').iterdir()}!=set(plan['case_ids']):raise ValueError('expansion case identity set changed')
    if set(plan['case_input_sha256'])!=set(plan['case_ids']):raise ValueError('case input hash roster changed')
    from reference import select_witness
    from coat_sim.core.film_synthesis_archive import physical_design_hash
    for case in plan['case_ids']:
        folder=expansion/'cases'/case;task=json.loads((folder/'input.json').read_text());result=json.loads((folder/'result.json').read_text())
        if sha(folder/'input.json')!=plan['case_input_sha256'][case]:raise ValueError('predeclared case input bytes changed')
        if task['case_id']!=case or result['case_id']!=case or result['request_sha256']!=hashlib.sha256(canonical_json(task)).hexdigest():raise ValueError('case binding changed')
        paths={p.stem:p for p in (folder/'witnesses').glob('*.json')}
        if set(paths)!=set(result['retained_witness_hashes']) or len(result['retained_witness_hashes'])!=len(set(result['retained_witness_hashes'])):raise ValueError('retained witness inventory changed')
        witnesses=[]
        for identity,path in paths.items():
            witness=json.loads(path.read_text());reports=witness['audit']['candidate_reports']
            if (witness['request_sha256']!=result['request_sha256'] or witness['physical_design_hash']!=identity
                    or physical_design_hash(witness['design'])!=identity or len(reports)!=1
                    or not all(reports[0][key] is True for key in ('targets_met','solver_acceptable','within_constraints','within_material_pool'))):raise ValueError('retained witness binding invalid')
            layers=witness['design']['front_layers']
            if witness['layer_count']!=len(layers) or not np.isclose(witness['total_thickness_nm'],sum(l['thickness']['value'] for l in layers),rtol=1e-12,atol=1e-9):raise ValueError('witness resource pair does not match design')
            witnesses.append(witness)
        selected=select_witness(witnesses,task['reference_wavelength_nm'])
        if (None if selected is None else selected['physical_design_hash'])!=result['selected_hash']:raise ValueError('selected resource point changed')
        if result['state'] not in ('completed','declared_budget_stopped'):raise ValueError('nonterminal expansion case')
        if result['selected_hash'] is None:
            if result['layer_count'] is not None or result['total_thickness_nm'] is not None or result['retained_witness_hashes']:raise ValueError('unknown was relabeled')
        else:
            witness=json.loads((folder/'witnesses'/f"{result['selected_hash']}.json").read_text())
            reports=witness['audit']['candidate_reports']
            if (witness['request_sha256']!=result['request_sha256'] or witness['physical_design_hash']!=result['selected_hash']
                or witness['layer_count']!=result['layer_count'] or witness['total_thickness_nm']!=result['total_thickness_nm']
                or len(reports)!=1 or not all(reports[0][key] is True for key in ('targets_met','solver_acceptable','within_constraints','within_material_pool'))):raise ValueError('selected witness invalid')
        expansion_rows.append(dict(task=task,result=result,dataset='material_expansion_v1'))
    train+=expansion_rows
    def optical_ids(rows):
        from coat_sim.core.film_resource_prediction import optical_prediction_fingerprint
        return {optical_prediction_fingerprint(o) for row in rows
            for m in row['task']['request']['frozen_material_snapshot']['materials'] for o in m['optical_sets']}
    if optical_ids(train)&optical_ids(test):raise ValueError('training and literature share a numeric optical source')
    train_known=[r for r in train if r['result']['selected_hash'] is not None]
    def feature(row):
        f=extract_features(row['task']['request'])
        if f['names']!=baseline['feature_names']:raise ValueError('feature schema changed')
        return f
    features=[feature(row) for row in train_known]
    X=np.array([f['values'] for f in features]);Y=np.log1p([[r['result']['layer_count'],r['result']['total_thickness_nm']/f['reference_wavelength_nm']] for r,f in zip(train_known,features)])
    train_ids=[r['task']['case_id'] for r in train_known];test_ids=[r['task']['case_id'] for r in test]
    if set(train_ids)&set(test_ids):raise ValueError('test IDs leaked into training')
    estimator=ExtraTreesRegressor(**PARAMETERS).fit(X,Y)
    model=validate_model(export_model(estimator,baseline['feature_names'],X,train_ids))
    parity=max(float(np.max(np.abs(np.array(predict_features(model,x))-y))) for x,y in zip(X,estimator.predict(X)))
    if parity>1e-12:raise ValueError('augmented JSON serialization mismatch')
    output=ROOT/'outputs';dump(output/'augmented_model.json',model)
    methods={name:[] for name in ('old_forest','augmented_forest','augmented_family_representative')}
    for row in test:
        task=row['task'];truth=row['result'];f=feature(row)
        for name,used in (('old_forest',baseline),('augmented_forest',model)):
            value=predict(used,task['request'])
            methods[name].append(dict(case_id=task['case_id'],family=task['family'],
                true_layers=truth['layer_count'],true_thickness_nm=truth['total_thickness_nm'],
                estimated_layers=value['estimated_layers'],estimated_layers_float=value['estimated_layers_float'],
                estimated_thickness_nm=value['estimated_total_thickness_nm'],feature_envelope_pass=value['feature_envelope_pass'],
                conditional_on_unknown_k=value['conditional_on_unknown_k']))
        pool=[i for i,r in enumerate(train_known) if r['task']['family']==task['family']] or list(range(len(train_known)))
        center=np.median(Y[pool],axis=0);selected=min(pool,key=lambda i:(float(np.sum(np.abs(Y[i]-center))),train_ids[i]))
        n,d=np.expm1(Y[selected]);record=dict(methods['augmented_forest'][-1]);record.update(
            estimated_layers=train_known[selected]['result']['layer_count'],estimated_layers_float=float(n),
            estimated_thickness_nm=float(d*f['reference_wavelength_nm']),baseline_source_case=train_ids[selected]);methods['augmented_family_representative'].append(record)
    for name,rows in methods.items():dump(output/(name+'-predictions.json'),rows)
    for i in range(36):predict(model,test[i]['task']['request'])
    times=[]
    for i in range(240):
        start=time.perf_counter();predict(model,test[i%36]['task']['request']);times.append((time.perf_counter()-start)*1000)
    dump(output/'latency_samples_ms.json',times)
    summary=dict(schema='matched-material-transfer-augmentation-results-v1',protocol_sha256=PROTOCOL_SHA,
        complete_expansion_manifest_sha256=args.verified_expansion_manifest_sha256,
        original_training_cases=12,additional_declared_cases=48,additional_known_labels=sum(r['result']['selected_hash'] is not None for r in expansion_rows),
        training_label_count=len(train_known),training_case_ids=train_ids,held_case_ids=test_ids,
        methods={name:dict(overall=metrics(rows),by_family={f:metrics([r for r in rows if r['family']==f]) for f in sorted({r['family'] for r in rows})}) for name,rows in methods.items()},
        warm_in_memory_latency_ms=dict(count=240,p50=float(np.percentile(times,50)),p95=float(np.percentile(times,95)),max=max(times)),
        serialization_max_abs_log_error=parity,parameters=PARAMETERS,feature_count=len(baseline['feature_names']),optical_numeric_source_overlap=False,
        independent_calibration=False,blind_test=False,production_ready=False,
        limitations=['Only same36 previously inspected literature tasks are compared','Additional data changes material and matched-target coverage, so improvement is not attributable solely to material diversity','Synthetic curves are not measured or globally causal/manufacturable models','Unknown labels not fitted or included in numeric error','No intervals or coverage guarantee'])
    dump(output/'metrics.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
