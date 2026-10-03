"""Author-only local freeze. Creates no ZIP, uploads, commits, or device task."""
from pathlib import Path
import hashlib,json,html,platform,importlib.metadata,argparse
from reader import paths,EXCLUDED,verify
ROOT=Path(__file__).resolve().parents[1]
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def build_index():
 s='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T06 Process to Optical Observables</title><style>body{max-width:1100px;margin:2rem auto;padding:0 1rem;font:17px/1.7 system-ui;color:#203d4a;background:#fafcfd}a{color:#196b91}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf3f5;padding:1em}img{max-width:100%;margin:1em 0}summary{cursor:pointer;font-weight:bold}.flag{padding:1em;background:#fff1d8;border-left:5px solid #c89532}li{margin:.2em}</style><h1>T06 · 工艺输入到条件化可测光谱</h1><p class="flag">本地研究冻结。实际膜工艺、设备、批量与生产校准未运行；指定审核链未完成。没有ZIP、没有论文原文、没有上传。</p><p><a href="README.md">README</a> · <a href="freeze_manifest.json">精确SHA256清单</a> · <a href="stage_status.json">阶段状态</a> · <a href="T07_ROUND2_HANDOFF.md">T07有界建议</a></p>'''
 for p in sorted((ROOT/'figures').glob('*.png')):s+='<img src="'+p.relative_to(ROOT).as_posix()+'" alt="'+html.escape(p.stem)+'">'
 s+='<h2>原创报告全文</h2>'
 for p in sorted((ROOT/'reports').glob('*.md')):s+='<details><summary>'+html.escape(p.name)+'</summary><pre>'+html.escape(p.read_text())+'</pre></details>'
 for d in ['models','models/vendor','data','examples','tests','sources','sources/summaries','reviews','verification']:
  s+='<h2>'+html.escape(d)+'</h2><ul>'
  for p in sorted((ROOT/d).glob('*')):
   if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED:s+='<li><a href="'+p.relative_to(ROOT).as_posix()+'">'+html.escape(p.name)+'</a></li>'
  s+='</ul>'
 s+='<p>本地自校：python models/reader.py --directory .。此reader不使用兄弟目录、ZIP或文献原文；哈希不是可信签名。</p></html>'
 (ROOT/'index.html').write_text(s)
def freeze(recompute=True):
 write(ROOT/'verification/environment.json',{'python':platform.python_version(),'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','scipy','jsonschema','matplotlib']},'device_benchmark':'not_run'})
 build_index()
 allow=ROOT/'data/reader_allowlist.json'
 if not allow.exists():raise ValueError('exact author-reviewed allowlist required before freezing')
 exact=paths(ROOT)
 if sorted(json.loads(allow.read_text())['paths'])!=exact:raise ValueError('review allowlist changed payload first')
 entries=[]
 for name in exact:
  b=(ROOT/name).read_bytes();entries.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 write(ROOT/'freeze_manifest.json',{'format':'T06-R2-plain-directory-v1','hash_algorithm':'SHA256','files':entries,'excluded_paths':sorted(EXCLUDED),'excluded_patterns':['**/__pycache__/**','**/*.pyc'],'no_zip':True,'raw_primary_sources':0,'authentication':'not_signed'})
 report=verify(ROOT,recompute=recompute)
 if not recompute:
  previous=json.loads((ROOT/'verification/isolated_reader_check.json').read_text())
  for name,digest in previous['tested_payload_hashes'].items():
   if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('tested implementation changed: '+name)
  report['isolated_check_evidence']='verification/isolated_reader_check.json'
  report['unchanged_tested_files']=len(previous['tested_payload_hashes'])
  report['tests_reexecuted_during_final_freeze']=False
 write(ROOT/'verification/freeze_receipt.json',report)
 project=ROOT.parents[1];before=json.loads((ROOT/'verification/outside_before.json').read_text())
 now={p.relative_to(project).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file() and ROOT not in p.parents and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 changed=[k for k in before if now.get(k)!=before[k]];added=sorted(set(now)-set(before))
 status='passed' if not changed and not added else 'changed'
 ack_path=ROOT/'verification/concurrent_planning_changes.json'
 if status=='changed' and ack_path.exists():
  ack=json.loads(ack_path.read_text());known={f['path']:f for f in ack['files']}
  if not added and set(changed)==set(known) and all(before[k]==known[k]['before_sha256'] and now[k]==known[k]['current_sha256'] for k in changed):status='passed_with_attributed_concurrent_changes'
 outside={'status':status,'before_files':len(before),'after_files':len(now),'changed_or_removed':changed,'added':added,'unchanged_outside_files':len(before)-len(changed),'concurrent_change_evidence':'verification/concurrent_planning_changes.json' if status=='passed_with_attributed_concurrent_changes' else None,'meaning':'original snapshot preserved; exact attributed root-planning changes are not a silent rebaseline; not a Git commit'}
 write(ROOT/'verification/outside_scope_check.json',outside)
 if outside['status'] not in ('passed','passed_with_attributed_concurrent_changes'):raise ValueError('outside-scope content changed')
 print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--skip-recompute',action='store_true');a=p.parse_args();freeze(not a.skip_recompute)
