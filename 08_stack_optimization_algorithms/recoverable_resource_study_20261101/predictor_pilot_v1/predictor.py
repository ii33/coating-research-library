"""Lightweight JSON tree inference, no sklearn, synthesis or optimizer required."""
import math
import numpy as np
from features import extract_features,SCHEMA

MODEL_SCHEMA='joint-resource-forest-v1'


def predict_features(model,values):
    if model.get('schema')!=MODEL_SCHEMA or model.get('feature_schema')!=SCHEMA:raise ValueError('unknown model schema')
    # sklearn trees compare float32 features; retain the same threshold convention.
    x=np.asarray(values,dtype=np.float32)
    if x.shape!=(len(model['feature_names']),) or not np.all(np.isfinite(x)):raise ValueError('invalid feature vector')
    trees=model['trees']
    if not isinstance(trees,list) or not 1<=len(trees)<=256:raise ValueError('invalid forest size')
    out=np.zeros(2)
    for tree in trees:
        left,right,feature,threshold,value=(tree[k] for k in ('left','right','feature','threshold','value'))
        n=len(left)
        if not 1<=n<=8191 or any(len(v)!=n for v in (right,feature,threshold,value)):raise ValueError('invalid tree arrays')
        node=0
        for _ in range(n):
            if left[node]==-1:
                y=np.asarray(value[node],dtype=float)
                if right[node]!=-1 or y.shape!=(2,) or not np.all(np.isfinite(y)):raise ValueError('invalid leaf')
                out+=y;break
            f=feature[node]
            if type(f) is not int or not 0<=f<len(x) or not math.isfinite(threshold[node]):raise ValueError('invalid split')
            node=left[node] if float(x[f])<=threshold[node] else right[node]
            if type(node) is not int or not 0<=node<n:raise ValueError('invalid child')
        else:raise ValueError('tree cycle')
    return (out/len(trees)).tolist()


def predict(model,request):
    features=extract_features(request)
    if features['names']!=model['feature_names']:raise ValueError('feature names differ from model')
    y=predict_features(model,features['values'])
    if any(v<0 or v>50 for v in y):raise ValueError('invalid physical resource transform')
    n=math.expm1(y[0]);d=math.expm1(y[1])*features['reference_wavelength_nm']
    x=np.array(features['values']);lo=np.array(model['feature_min']);hi=np.array(model['feature_max'])
    if lo.shape!=x.shape or hi.shape!=x.shape or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi)) or np.any(lo>hi):raise ValueError('invalid training envelope')
    outside=np.flatnonzero((x<lo-1e-10)|(x>hi+1e-10)).tolist()
    return dict(state='research_uncalibrated',estimated_layers_float=n,estimated_layers=int(math.ceil(n)),
        estimated_total_thickness_nm=d,interval=None,interval_state='no_independent_calibration',
        joint_prediction=True,conditional_on_unknown_k=features['conditional_on_unknown_k'],
        outside_training_feature_indices=outside,feature_envelope_pass=not outside,
        warning='Research point estimate of finite-reference resources, not a feasible design or minimum. Feature-envelope membership does not prove applicability.',
        model_validation_status=model.get('validation_status','unvalidated'))


def validate_model(model):
    """Validate all nodes once when loading, including branches not queried yet."""
    if model.get('schema')!=MODEL_SCHEMA or model.get('feature_schema')!=SCHEMA:raise ValueError('unknown model schema')
    names=model['feature_names'];size=len(names)
    if not names or len(set(names))!=size or not all(isinstance(x,str) for x in names):raise ValueError('invalid feature names')
    lo=np.asarray(model['feature_min'],dtype=float);hi=np.asarray(model['feature_max'],dtype=float)
    if lo.shape!=(size,) or hi.shape!=(size,) or not np.all(np.isfinite(lo)) or not np.all(np.isfinite(hi)) or np.any(lo>hi):raise ValueError('invalid feature envelope')
    if not isinstance(model['trees'],list) or not 1<=len(model['trees'])<=256:raise ValueError('invalid forest size')
    for t in model['trees']:
        n=len(t['left'])
        if not 1<=n<=8191 or any(len(t[k])!=n for k in ('right','feature','threshold','value')):raise ValueError('invalid tree arrays')
        nodes=[0];seen=set()
        while nodes:
            i=nodes.pop()
            if type(i) is not int or not 0<=i<n or i in seen:raise ValueError('invalid tree graph')
            seen.add(i);v=np.asarray(t['value'][i],dtype=float)
            if v.shape!=(2,) or not np.all(np.isfinite(v)) or not math.isfinite(t['threshold'][i]):raise ValueError('invalid node values')
            l=t['left'][i];r=t['right'][i]
            if l==-1:
                if r!=-1:raise ValueError('invalid leaf child')
            else:
                f=t['feature'][i]
                if type(f) is not int or not 0<=f<size:raise ValueError('invalid feature index')
                nodes.extend([l,r])
        if len(seen)!=n:raise ValueError('unreachable nodes')
    return model


def load_model(path,expected_sha256):
    import hashlib,json
    from pathlib import Path
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('model SHA256 mismatch')
    return validate_model(json.loads(raw))
