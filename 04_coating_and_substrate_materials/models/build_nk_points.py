#!/usr/bin/env python3
"""Regenerate published sample points from local CC0 originals, without network."""
from pathlib import Path
import hashlib,json
from optical_examples import read_nk,interp_nk
ROOT=Path(__file__).resolve().parents[1]
def build():
    rows=[]
    for meta in json.loads((ROOT/'data/local_originals_manifest.json').read_text()):
        f=ROOT/meta['local_original']
        if not f.exists(): raise FileNotFoundError(f'Local-only original required; see manifest URL: {f.name}')
        if hashlib.sha256(f.read_bytes()).hexdigest()!=meta['sha256']: raise ValueError(f'Original checksum mismatch: {f.name}')
        data=read_nk(f); name=meta['dataset_id']
        for w in [.55,.6328,1.55]+([10.6] if name=='Al_Rakic' else []):
            n,k=interp_nk(data,w)
            rows.append(dict(dataset_id=name,material=name.split('_')[0],source_id=meta['source_id'],wavelength_um=w,n=n,k=k,method='linear interpolation of n and k in wavelength within one source dataset',uncertainty='not estimated by interpolation; see original study and material card',phase_state='thin-film-derived reference; sample conditions dataset-specific',source_sha256=meta['sha256']))
    return rows
if __name__=='__main__':
    (ROOT/'data/metal_nk_derived_points.json').write_text(json.dumps(build(),indent=2)+'\n')
