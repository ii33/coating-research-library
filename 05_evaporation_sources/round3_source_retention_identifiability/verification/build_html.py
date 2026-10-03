from pathlib import Path
import re,html
R=Path(__file__).resolve().parents[1]
docs=[R/'README.md',*sorted((R/'reports').glob('*.md')),*sorted((R/'sources/summaries').glob('*.md')),R/'T06_ROUND3_HANDOFF.md']
ids={str(p.relative_to(R)):'doc-'+str(i) for i,p in enumerate(docs)}
def inline(text,path):
 out=[];end=0
 for m in re.finditer(r'\[([^]]+)\]\(([^)]+)\)',text):
  out.append(html.escape(text[end:m.start()]));label,url=m.group(1),m.group(2)
  if not url.startswith(('http://','https://')):
   key=str((path.parent/url).resolve().relative_to(R.resolve()));url='#'+ids[key] if key in ids else key
  out.append('<a href="'+html.escape(url,quote=True)+'">'+html.escape(label)+'</a>');end=m.end()
 out.append(html.escape(text[end:]));return ''.join(out)
def render(path):
 out=[];table=False
 for line in path.read_text().splitlines():
  if line.startswith('|'):
   if not table:out.append('<div class="tablewrap"><table>');table=True
   cells=[x.strip() for x in line.strip('|').split('|')]
   if all(re.match(r'^:?-+:?$',x) for x in cells):continue
   out.append('<tr>'+''.join('<td>'+inline(x,path)+'</td>' for x in cells)+'</tr>');continue
  if table:out.append('</table></div>');table=False
  if line.startswith('    '):out.append('<pre>'+html.escape(line.strip())+'</pre>');continue
  m=re.match(r'^(#{1,5}) (.*)',line)
  if m:
   h=len(m[1])+1;out.append(f'<h{h}>'+inline(m[2],path)+f'</h{h}>')
  elif line.strip():out.append('<p>'+inline(line,path)+'</p>')
 if table:out.append('</table></div>')
 return '\n'.join(out)
css='''body{margin:0;background:#eef3f7;color:#193146;font:16px/1.8 system-ui,"Noto Sans CJK SC",sans-serif}header{padding:32px 5vw;background:#183b56;color:white}header h1{font-size:30px;line-height:1.3}nav{padding:14px 5vw;display:flex;flex-wrap:wrap;gap:12px;background:#dfe9f0}main{max-width:1080px;background:white;padding:28px 4vw;margin:auto}h2{font-size:27px;line-height:1.4;margin-top:38px}h3{font-size:21px;margin-top:30px}a{color:#126994;overflow-wrap:anywhere}p{margin:13px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f6;padding:10px;font:14px/1.7 ui-monospace,monospace}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:650px;font-size:14px}td{padding:9px;border:1px solid #b9cbd7;vertical-align:top}tr:first-child{background:#e7eff5;font-weight:bold}img{max-width:100%;height:auto}figure{margin:28px 0}figcaption{font-size:14px;color:#516a7b}section{padding-top:15px;margin-bottom:35px}footer{padding:28px 5vw;background:#dfe9f0}@media(max-width:600px){main{padding:18px}header h1{font-size:25px}h2{font-size:23px}}'''
parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T05 源与留存可辨识性</title><style>'+css+'</style><header><h1>T05 蒸发源与材料留存可辨识性</h1><p>相同QCM与平行厚度分布，并不唯一决定源角谱和留存。</p><p>v0.1.0 · Local freeze · Synthetic only · 正式模型链pending · HTML布局未验证</p></header><nav>']
for p in docs:parts.append('<a href="#'+ids[str(p.relative_to(R))]+'">'+html.escape(p.read_text().splitlines()[0].lstrip('# '))+'</a>')
parts.append('</nav><main>')
figs={'01_scope_and_physical_contract.md':('01_contract','图1 源强 角谱 捕集 留存与密度分别保存'),'03_identifiability_and_diagnostic_design.md':('02_exact_ambiguity','图2 全局等效反例与新方向诊断'),'04_frozen_response_bridge_and_algorithm.md':('03_identifiability','图3 局部秩与独立尺度条件')}
for p in docs:
 parts.append('<section id="'+ids[str(p.relative_to(R))]+'">'+render(p)+'</section>')
 if p.name in figs:
  name,cap=figs[p.name];parts.append('<figure><img src="figures/'+name+'.png" alt="'+cap+'"><figcaption>'+cap+'；synthetic示例</figcaption></figure>')
parts.append('</main><footer>来源原文与reader分离。仅本地有界研究；无实机标定、连续源认证或生产放行。</footer></html>');(R/'reader.html').write_text('\n'.join(parts));print('reader.html generated; no browser layout claim')
