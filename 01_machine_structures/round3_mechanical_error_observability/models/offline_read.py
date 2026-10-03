"""Read, hash-check and normalize the local CSV interface; no network or mutation."""
import argparse,json
from reference import load_observation_dataset
p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--allow-synthetic',action='store_true')
a=p.parse_args()
try: print(json.dumps(load_observation_dataset(a.dataset,a.allow_synthetic),ensure_ascii=False,indent=2,allow_nan=False))
except (ValueError,OSError,KeyError,TypeError) as e: p.exit(2,'Rejected: '+str(e)+'\n')
