"""Author operation: freeze plain-directory payload. Never creates ZIP or uploads."""
from pathlib import Path
import json,hashlib,platform,importlib.metadata,html
from reader import payload_paths,EXCLUDED,verify
R=Path(__file__).resolve().parents[1]
def write(p,data):p.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def build_index():
 links=[]
 for category in ['reports','models','data','examples','figures','sources/summaries','reviews','verification']:
  fs=[p for p in (R/category).glob('*') if p.is_file() and p.relative_to(R).as_posix() not in EXCLUDED]
  if not fs:continue
  links.append('<h2>'+html.escape(category)+'</h2><ul>')
  for p in sorted(fs):
   rel=p.relative_to(R).as_posix();links.append('<li><a href="'+html.escape(rel,quote=True)+'">'+html.escape(p.name)+'</a></li>')
  links.append('</ul>')
 text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T05 QCM flux transfer | local reader</title><style>body{max-width:1040px;margin:2rem auto;padding:0 1rem;font:17px/1.6 system-ui;color:#193440;background:#fafafa}a{color:#176b88}img{max-width:100%;border:1px solid #ccd9de}h2{margin-top:2em}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f5;padding:1em;border-radius:.5em}summary{cursor:pointer;font-weight:600}li{margin:.3em 0}.flag{background:#ffefd9;padding:1em;border-left:5px solid #c98434}</style><h1>T05 · QCM 到工件入射元素通量</h1><p class="flag">本地研究冻结；真实校准、重任务和设备验证未运行。没有生产tooling，没有ZIP，没有部署或上传。</p><p>直接阅读本包原创报告和原始代码。文献全文仅使用官方来源链接；没有声称附件包含未获取的论文原文。</p><p><a href="README.md">README</a> · <a href="freeze_manifest.json">精确清单</a> · <a href="sources/source_registry.json">来源登记</a> · <a href="T06_ROUND2_HANDOFF.md">T06建议</a></p><img src="figures/01_transfer_contract.png" alt="Original QCM transfer flow diagram"><h2>原创报告全文</h2>'''
 for p in sorted((R/'reports').glob('*.md')):
  text+='<details><summary>'+html.escape(p.name)+'</summary><pre>'+html.escape(p.read_text())+'</pre></details>'
 text+=''.join(links)+'<p>完整性复算：python models/reader.py --directory .</p></html>'
 (R/'index.html').write_text(text)
def freeze():
 write(R/'verification/environment.json',{'python':platform.python_version(),'platform':platform.platform(),
 'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','jsonschema','matplotlib']},'device_sampling':'not_performed'})
 build_index()
 files=[]
 for rel in payload_paths(R):
  b=(R/rel).read_bytes();files.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 write(R/'freeze_manifest.json',{'format':'T05-R2-plain-directory-v1','hash_algorithm':'SHA256','files':files,'excluded_paths':sorted(EXCLUDED),'excluded_patterns':['**/__pycache__/**','**/*.pyc'],'raw_primary_sources':0,'zip_created':False})
 report=verify(R)
 write(R/'verification/freeze_receipt.json',report)
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':freeze()
