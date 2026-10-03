"""Offline self-contained reading page; no remote scripts/fonts/images."""
from pathlib import Path
import html,json,re
ROOT=Path(__file__).resolve().parents[1]
def inline(t):
 t=html.escape(t)
 t=re.sub(r'`([^`]+)`',r'<code>\1</code>',t)
 return re.sub(r'\[RI-S(\d+)\]',lambda m:'<a href="#RI-S'+m[1]+'">[RI-S'+m[1]+']</a>',t)
def render(t):
 out=[];table=False
 for line in t.splitlines():
  if line.startswith('|'):
   if re.fullmatch(r'[|\s:\-]+',line):continue
   if not table:out.append('<div class="scroll"><table>');table=True
   out.append('<tr>'+''.join('<td>'+inline(z.strip())+'</td>' for z in line.strip('|').split('|'))+'</tr>');continue
  if table:out.append('</table></div>');table=False
  if not line.strip():continue
  m=re.match(r'^(#{1,4}) (.+)',line)
  out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>' if m else '<p>'+inline(line)+'</p>')
 if table:out.append('</table></div>')
 return '\n'.join(out)
def build():
 chapters=sorted((ROOT/'reports').glob('*.md'))
 s='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T08 · 稳健有限参数反演</title><style>
:root{font-family:system-ui,sans-serif;color:#183843;background:#eef3f4;line-height:1.85}body{max-width:1160px;margin:auto;padding:24px}header,article,section{background:white;border:1px solid #d8e4e7;border-radius:12px;padding:28px 34px;margin:20px 0}h1{line-height:1.25;color:#114955}h2{border-bottom:1px solid #c9dadd;padding-bottom:8px}h3{color:#1e7179}p,td{overflow-wrap:anywhere}a{color:#086f86}nav{display:flex;gap:10px 22px;flex-wrap:wrap}.flag{border-left:5px solid #d49731;padding:14px;background:#fff4dc}.small{color:#536f78;font-size:.9rem}code{background:#eaf0f2;padding:2px 4px;font-size:.9em}img{width:100%;height:auto}table{border-collapse:collapse;min-width:740px;font-size:.9rem}td{border:1px solid #cfdee2;padding:9px;vertical-align:top}tr:first-child{background:#e8f3f4;font-weight:600}.scroll{overflow:auto}summary{cursor:pointer;font-weight:600}details{margin:15px 0}@media(max-width:700px){body{padding:7px}header,article,section{padding:18px}}@media print{body{max-width:none;background:white}article{break-before:page}a{color:inherit}}
</style></head><body><header><p class="small">镀膜研究库 · T08 ROUND 2 · 2026-10-02</p><h1>拟合得更精确，<br>物理解释就更可信吗？</h1><p>模型失配 · 多解发现 · 剖面与留出 · 候选测量条件信息</p><p class="flag">只到本地冻结。所有数值为合成条件；用户实际仪器未知。完整163,584启动未运行，最多196,391,832次观测向量调用只是预算计划。小测试与一次窄核查不代表生产验证或完整审核链。</p><nav>'''
 for i,p in enumerate(chapters,1):s+=f'<a href="#chapter{i}">第{i}章</a>'
 s+='</nav><p><a href="README.md">使用说明</a> · <a href="stage_status.json">状态</a> · <a href="freeze_manifest.json">精确清单</a> · <a href="T09_ROUND2_HANDOFF.md">下一有界交接</a></p></header>'
 for p in sorted((ROOT/'figures').glob('*.png')):s+='<section><img src="'+p.relative_to(ROOT).as_posix()+'" alt="'+html.escape(p.stem)+'"><p class="small">原创图，使用已保存小型合成证据。无真实测量、仪器排名或全局唯一证书。</p></section>'
 for i,p in enumerate(chapters,1):s+=f'<article id="chapter{i}">'+render(p.read_text())+'</article>'
 s+='<section><h2>原始来源与阅读范围</h2>'
 for q in json.loads((ROOT/'sources/source_registry.json').read_text())['sources']:
  s+='<details id="'+q['id']+'"><summary>'+html.escape(q['id']+' · '+q['title'])+'</summary>'+render((ROOT/q['summary_path']).read_text())+'<p><a href="'+html.escape(q['url'],quote=True)+'">原始来源</a></p></details>'
 s+='</section><section><h2>代码与可复现证据</h2><p>原始PDF/提取文本仅本地保存，未放入reader。数据目录含原件身份清单，不含其内容。下面的链接均为相对路径，离线阅读不依赖外部网站。</p>'
 for folder in ['models','models/vendor','tests','data','reviews','verification']:
  s+='<details><summary>'+folder+'</summary><ul>'
  for p in sorted((ROOT/folder).glob('*')):
   if p.is_file() and p.name not in ['outside_before.json','outside_scope_check.json','freeze_receipt.json','isolated_reader_receipt.json']:
    s+='<li><a href="'+p.relative_to(ROOT).as_posix()+'">'+html.escape(p.name)+'</a></li>'
  s+='</ul></details>'
  if folder=='verification':
   s+='<p><a href="verification/tiny_final/case_000_constant_gaussian.json">最终tiny完整拟合/剖面/设计记录</a> · <a href="verification/tiny_final/case_000_observations.json">tiny原始合成观测</a></p>'
 s+='<p class="small">哈希检测内容变化，不是可信签名；允许列表不构成发布许可。根规划和后续批次由协调者安排。</p></section></body></html>'
 (ROOT/'index.html').write_text(s)
if __name__=='__main__':build()
