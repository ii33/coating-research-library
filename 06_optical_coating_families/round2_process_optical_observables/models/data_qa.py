"""Read-only schema, table, dependency and default-plan checks."""
import json,hashlib
from pathlib import Path
import numpy as np
from process_optics import ROOT,validate,evaluate
from batch_driver import run

def main():
 rows=np.array(json.loads((ROOT/'data/al_mcpeak_derived.json').read_text())['rows'])
 assert rows.shape==(121,3) and np.all(np.isfinite(rows)) and np.all(np.diff(rows[:,0])>0) and np.all(rows[:,1]>0) and np.all(rows[:,2]>=0)
 results={}
 for p in sorted((ROOT/'examples').glob('*.json')):
  r=json.loads(p.read_text());validate(r);results[p.stem]=evaluate(r)['status']
 assert sum(v=='conditional_calculation' for v in results.values())==2
 dep=json.loads((ROOT/'data/frozen_dependencies.json').read_text())[0]
 assert hashlib.sha256((ROOT/'models/vendor/optics_kernel.py').read_bytes()).hexdigest()==dep['sha256']
 plan=run(json.loads((ROOT/'data/batch_plan.json').read_text()),json.loads((ROOT/'examples/synthetic_dielectric.json').read_text()))
 assert plan['status']=='plan_only'
 return {'status':'passed','fixtures':results,'al_data_rows':len(rows),'vendored_T07_kernel':'byte_identical','default_batch':'plan_only','device_validation':'not_run'}
if __name__=='__main__':print(json.dumps(main(),indent=2,ensure_ascii=False))
