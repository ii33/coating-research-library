"""Verify archived phase1 extrema and optionally all archived dense spectra."""
import argparse,gzip,json,hashlib
from pathlib import Path
import numpy as np
from optics import ROOT,BUNDLE,spectrum
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dense',action='store_true');parser.add_argument('--output',type=Path);args=parser.parse_args();rows=[]
for path in sorted((ROOT/'cases').glob('*.json')):
 case=json.loads(path.read_text(encoding='utf-8'));error=0.
 for win in case['windows']:
  for key,col in [('Rmax',0),('Tmin',1),('Amax',2)]:
   value=float(spectrum(case,np.array([win[key+'_nm']]))[0,col]);error=max(error,abs(value-win[key]))
 if args.dense:
  with gzip.open(ROOT/'spectra'/(case['case']+'.csv.gz'),'rt',encoding='utf-8') as stream:data=np.loadtxt(stream,delimiter=',',skiprows=1)
  result=spectrum(case,data[:,0]);error=max(error,float(np.max(abs(result-data[:,1:]))))
 if error>2e-10:raise ArithmeticError(case['case']+' mismatch '+str(error))
 rows.append({'case':case['case'],'max_RTA_difference':error,'guard_pass':case['diagnostic_guard_pass']})
out={'verified_cases':len(rows),'dense_archived_spectra_rechecked':args.dense,'max_RTA_difference':max(r['max_RTA_difference'] for r in rows),'all_reproduced':True,'notes':'Reproduces the reported extrema locations and optional original full sampled spectra; original local-extremum protocol and validation records remain archived. It does not promote finite diagnostics to a continuous certificate.','cases':rows}
if args.output:args.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
