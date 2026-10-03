"""Default plan only. Only the fixed tiny replay can execute; no heavy mode."""
import argparse,json,time
from pathlib import Path
from acceptance import *
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['plan_only','tiny'],default='plan_only');p.add_argument('--output');a=p.parse_args()
if a.mode=='plan_only':print(json.dumps(plan(),indent=2))
else:
 if not a.output:p.error('tiny needs a fresh output directory inside this package')
 out=Path(a.output).resolve()
 if ROOT not in out.parents or out.exists():p.error('new output directory inside this package required')
 out.mkdir(parents=True);start=time.monotonic();s=replay_tiny();cases=json.loads((ROOT/'cases/claims.json').read_text());rows=[]
 for c in cases:
  got=evaluate(s,c['claim']);rows.append({'id':c['id'],'claim':c['claim'],'expected':c['expected'],'result':got,'pass':got['status']==c['expected']})
 record={'summary':summary(s),'cases':rows,'all_expected':all(x['pass']for x in rows),'elapsed_seconds':time.monotonic()-start,'production_release':False}
 (out/'results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record['summary'],indent=2));print('all_expected',record['all_expected'])
 if not record['all_expected']:raise SystemExit(1)
