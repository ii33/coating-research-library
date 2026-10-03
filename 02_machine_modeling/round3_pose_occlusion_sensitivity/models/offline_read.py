"""Strict, offline, synthetic input contract; real adapter deliberately unavailable."""
from pathlib import Path
import argparse,json,sys
from dataclasses import fields
from event_reference import Scene,evaluate

def load(path,allow_synthetic=False):
    d=json.loads(Path(path).read_text())
    if set(d)!={'schema_version','dataset_kind','scene','source_nodes_m','source_weights','units','scope'}:raise ValueError('exact top-level schema required')
    if d['schema_version']!='t02-r3-affine-slice-1':raise ValueError('unsupported schema')
    if d['dataset_kind']!='synthetic' or not allow_synthetic:raise ValueError('only explicitly allowed synthetic scene is supported; no inferred measured parameters')
    if d['units']!={'length':'m','time':'s','angle':'rad','output':'s/m^2'}:raise ValueError('SI units required')
    if d['scope']!='fixed_affine_y0_slab_cosine_source':raise ValueError('out-of-scope geometry')
    if set(d['scene'])!={x.name for x in fields(Scene)}:raise ValueError('complete scene required; unknown keys forbidden')
    sc=Scene(**d['scene']).validate()
    import numpy as np
    s=np.asarray(d['source_nodes_m'],dtype=float);w=np.asarray(d['source_weights'],dtype=float)
    if s.ndim!=1 or len(s)<1 or len(s)>4096 or w.shape!=s.shape or not np.all(np.isfinite(s)) or not np.all(np.isfinite(w)) or np.any(w<=0) or not np.isclose(w.sum(),1.,atol=1e-12,rtol=0):raise ValueError('finite nodes, positive normalized weights and bounded size required')
    return sc,s,w

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--allow-synthetic',action='store_true');a=p.parse_args()
    try:
        sc,s,w=load(a.input,a.allow_synthetic);rows=[evaluate(float(x),sc) for x in s]
        print(json.dumps({'dataset_kind':'synthetic','status':'conditional_interface_evaluation','value_s_m2':sum(float(ww)*r['value_s_m2'] for ww,r in zip(w,rows)),'node_statuses':[r['sensitivity_status'] for r in rows],'continuous_source_convergence':'not_claimed'},indent=2))
    except (ValueError,TypeError,KeyError) as e:print(str(e),file=sys.stderr);sys.exit(2)
