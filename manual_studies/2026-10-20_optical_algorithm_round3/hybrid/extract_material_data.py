#!/usr/bin/env python3
"""Optional material-data provenance reconstruction from a pinned RI snapshot."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import yaml

def main():
    ap=argparse.ArgumentParser();ap.add_argument('snapshot_root',type=Path);ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'data');args=ap.parse_args();args.output.mkdir(exist_ok=True,parents=True)
    meta=[]
    for mat,name in [('MgF2','Franta'),('ZnSe','Querry'),('Si','Franta-300K')]:
        rel=f'database/data/main/{mat}/nk/{name}.yml';p=args.snapshot_root/rel;raw=p.read_bytes();d=yaml.safe_load(raw);tab=d['DATA'][0];assert tab['type']=='tabulated nk';rows=np.array([list(map(float,x.split())) for x in tab['data'].strip().splitlines()]);ix=np.where((rows[:,0]>=2.8)&(rows[:,0]<=12.2))[0];z=rows[max(0,ix.min()-1):min(len(rows),ix.max()+2)];np.savetxt(args.output/f'{mat}_{name}.csv',z,delimiter=',',header='wavelength_um,n,k',comments='',fmt='%.13g');meta.append({'material':mat,'dataset':name,'source_file':rel,'snapshot_commit':args.snapshot_root.name,'sha256_original_yaml':hashlib.sha256(raw).hexdigest(),'original_range_um':rows[[0,-1],0].tolist(),'stored_range_um':z[[0,-1],0].tolist(),'references':d['REFERENCES'],'comments':d.get('COMMENTS',''),'conditions':d.get('CONDITIONS',{})})
    (args.output/'provenance.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
