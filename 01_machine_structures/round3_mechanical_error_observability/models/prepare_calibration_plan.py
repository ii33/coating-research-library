"""Plan-only gate for future full calibration; it does not launch hardware or jobs."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--contract',default=str(Path(__file__).resolve().parents[1]/'data/formal_calibration_plan.json'))
p.add_argument('--execute',action='store_true',help='unsupported in this reference package')
a=p.parse_args()
if a.execute: p.exit(2,'Not executed: this package prepares plans only; device execution and a full solver require separately authorized work.\n')
d=json.loads(Path(a.contract).read_text()); assert d['execution_mode']=='plan_only'
print(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False))
