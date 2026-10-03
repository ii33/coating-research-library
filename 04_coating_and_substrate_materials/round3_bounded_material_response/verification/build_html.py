from pathlib import Path
import html,re,json
R=Path(__file__).resolve().parents[1]
docs=[R/'README.md',*sorted((R/'reports').glob('*.md')),*sorted((R/'sources/summaries').glob('*.md')),R/'T05_ROUND3_HANDOFF.md']
ids={str(p.relative_to(R)):'doc-'+str(i) for i,p in enumerate(docs)}
def inline(text,path):
 def link(m):
  label,url=m.group(1),m.group(2)
  if not re.match(r'https?://',url):
   key=str((path.parent/url).resolve().relative_to(R.resolve()));url='#'+ids[key] if key in ids else key
  return f'<a href="{html.escape(url,quote=True)}">{html.escape(label)}</a>'
 text=html.escape(text)
 # Input is authored local markdown with simple links; unescape captures before link.
 text=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:link(m),text)
 return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text)
def render(path):
 lines=path.read_text().splitlines();out=[];table=False;ul=False;code=False
 for line in lines:
  if line.startswith('|'):
   if not table:out.append('<div class="tablewrap"><table>');table=True
   cells=[c.strip() for c in line.strip('|').split('|')]
   if all(re.match(r'^:?-+:?$',c) for c in cells):continue
   out.append('<tr>'+''.join('<td>'+inline(c,path)+'</td>' for c in cells)+'</tr>');continue
  if table:out.append('</table></div>');table=False
  if line.startswith('    '):
   out.append('<pre>'+html.escape(line.strip())+'</pre>');continue
  m=re.match(r'^(#{1,6}) (.*)',line)
  if m:out.append(f'<h{len(m[1])+1}>{inline(m[2],path)}</h{len(m[1])+1}>');continue
  if re.match(r'^(- |\d+\. )',line):out.append('<p class="item">'+inline(line,path)+'</p>');continue
  if line.strip():out.append('<p>'+inline(line,path)+'</p>')
 if table:out.append('</table></div>')
 return '\n'.join(out)
css='''body{font-family:system-ui,"Noto Sans CJK SC",sans-serif;color:#172635;line-height:1.75;margin:0;background:#f6f8fa}header{padding:32px max(5vw,24px);background:#17334d;color:white}header h1{margin:0;font-size:30px}header p{max-width:1000px}nav{position:sticky;top:0;background:#e8eef4;padding:10px 4vw;display:flex;flex-wrap:wrap;gap:12px;z-index:1}nav a{color:#214864;font-size:14px}main{max-width:1040px;margin:auto;padding:28px 5vw;background:white}section{padding-top:24px;margin-bottom:44px}h2{font-size:27px;color:#122f47;line-height:1.35}h3{font-size:21px;margin-top:30px}p{margin:12px 0}a{color:#1761a1;overflow-wrap:anywhere}table{border-collapse:collapse;font-size:14px;min-width:660px;width:100%}td{padding:10px;border:1px solid #ccd4dc;vertical-align:top}tr:first-child{background:#e9eff5;font-weight:600}.tablewrap{overflow-x:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f7;padding:8px 12px}.item{margin-left:16px}figure{margin:28px 0}img{max-width:100%;height:auto}figcaption{font-size:14px;color:#4d6071}footer{padding:24px;background:#e9eff5;font-size:14px}@media(max-width:600px){header h1{font-size:24px}h2{font-size:23px}main{padding:20px}nav{position:static}body{line-height:1.65}}'''
parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T04 材料响应有界传递</title><style>'+css+'</style><header><h1>T04 材料响应有界传递</h1><p>固定几何和时钟下，从传递积分到有界材料响应。synthetic反例可复算；真实材料参数仍unknown。</p><p>Local freeze · 指定模型链pending · HTML布局未经浏览器验证</p></header><nav>']
for p in docs:
 title=p.read_text().splitlines()[0].lstrip('# ');parts.append(f'<a href="#{ids[str(p.relative_to(R))]}">{html.escape(title)}</a>')
parts.append('</nav><main>')
for p in docs:
 parts.append(f'<section id="{ids[str(p.relative_to(R))]}">'+render(p)+'</section>')
 if p.name in ['01_physical_contract.md','04_counterexamples_and_results.md','03_bounded_kernel_and_ranking.md']:
  name,caption={'01_physical_contract.md':('01_response_contract','图1 保留完整上游forward，材料未知不补数'),'04_counterexamples_and_results.md':('02_ranking_intervals','图2 同一候选与目标，材料情景可使排序反转或无法分辨'),'03_bounded_kernel_and_ranking.md':('03_kernel_shape','图3 合成核形状与同D信息丢失反例')}[p.name]
  parts.append(f'<figure><img src="figures/{name}.png" alt="{caption}"><figcaption>{caption}</figcaption></figure>')
parts.append('</main><footer>完整输入、依赖hash、小测试和plan_only入口随reader提供。原文单独本地保存，不在本包。没有实机工艺或生产放行。</footer></html>')
(R/'reader.html').write_text('\n'.join(parts));print('reader.html generated; no browser/layout claim')
