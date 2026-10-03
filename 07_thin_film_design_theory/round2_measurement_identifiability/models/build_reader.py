"""Build an offline human reader from original reports. No scripts or remote resources."""
from pathlib import Path
import html,re,json
ROOT=Path(__file__).resolve().parents[1]
def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
def render(text):
    out=[];table=False
    for line in text.splitlines():
        if line.startswith('|'):
            if re.match(r'^\|[\s:|\-]+\|$',line):continue
            if not table:out.append('<div class="scroll"><table>');table=True
            cells=line.strip('|').split('|');out.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in cells)+'</tr>');continue
        if table:out.append('</table></div>');table=False
        if not line.strip():continue
        m=re.match(r'^(#{1,4}) (.+)',line)
        if m:out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>')
        else:out.append('<p>'+inline(line)+'</p>')
    if table:out.append('</table></div>')
    return '\n'.join(out)
def build():
    s='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T07 · 测量与可辨识性</title><style>
:root{font-family:system-ui,sans-serif;color:#233d48;background:#f4f7f8;line-height:1.8}body{max-width:1120px;margin:auto;padding:24px}h1{line-height:1.3;color:#123b45}h2{border-bottom:1px solid #bdd0d4;padding-bottom:8px}h3{color:#196a78}header,article,section{background:white;padding:26px 34px;margin:18px 0;border-radius:12px;border:1px solid #dbe5e8}.flag{border-left:5px solid #cc8b24;padding:12px;background:#fff4dd}nav{display:flex;flex-wrap:wrap;gap:8px 22px}a{color:#126f87}table{border-collapse:collapse;font-size:.9rem;min-width:750px}td{border:1px solid #cad8dc;padding:8px;vertical-align:top}tr:first-child{background:#e8f1f3;font-weight:600}.scroll{overflow:auto}code{background:#eef2f4;padding:2px 5px;overflow-wrap:anywhere;font-size:.9em}img{width:100%;height:auto}details{margin:12px 0}summary{cursor:pointer;font-weight:600}p{overflow-wrap:anywhere}.muted{font-size:.9rem;color:#526c76}@media(max-width:700px){body{padding:8px}header,article,section{padding:18px}}@media print{body{max-width:100%;background:white}details{display:block}a{color:inherit}}
</style></head><body><header><p class="muted">镀膜研究库 · T07 ROUND 2 · 2026-10-02</p><h1>测量多了，参数就唯一了吗？</h1><p>条件化测量算子 · 相位基矢 · 有限参数逆问题</p><p class="flag">本地冻结；全部数值为合成条件。用户硬件未知，真实仪器适配、生产校准与完整批量未运行。一次窄核查不代表完整指定审核链通过。</p><nav>'''
    for i,p in enumerate(sorted((ROOT/'reports').glob('*.md')),1):s+=f'<a href="#chapter{i}">第{i}章</a>'
    s+='</nav><p><a href="README.md">使用说明</a> · <a href="freeze_manifest.json">精确冻结清单</a> · <a href="stage_status.json">状态与未运行项</a> · <a href="T08_ROUND2_HANDOFF.md">下一有界交接</a></p></header>'
    for p in sorted((ROOT/'figures').glob('*.png')):s+='<section><img src="'+p.relative_to(ROOT).as_posix()+'" alt="'+html.escape(p.stem)+'"><p class="muted">原创图，仅使用已保存的小型合成结果。不同方案的成本/噪声并未归一，不能作仪器排行榜。</p></section>'
    for i,p in enumerate(sorted((ROOT/'reports').glob('*.md')),1):s+=f'<article id="chapter{i}">'+render(p.read_text())+'</article>'
    s+='<section><h2>六项原始来源</h2>'
    for x in json.loads((ROOT/'sources/source_registry.json').read_text())['sources']:
        s+='<details><summary>'+html.escape(x['id']+' · '+x['title'])+'</summary>'+render((ROOT/x['summary_path']).read_text())+'<p><a href="'+html.escape(x['url'],quote=True)+'">访问原始来源</a></p></details>'
    s+='</section><section><h2>代码、证据与复现</h2><p>命令：<code>PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=models python models/reader.py --directory .</code>。只执行小检查，完整驱动默认plan_only。下载的合法PDF仅在作者本地原件区保存，不在reader允许列表中。</p>'
    for folder in ['models','models/vendor','data','tests','reviews','verification']:
        s+='<details><summary>'+folder+'</summary><ul>'
        for p in sorted((ROOT/folder).glob('*')):
            if p.is_file() and p.name not in ['outside_before.json','outside_scope_check.json','freeze_receipt.json']:s+='<li><a href="'+p.relative_to(ROOT).as_posix()+'">'+html.escape(p.name)+'</a></li>'
        s+='</ul></details>'
    s+='<p class="muted">哈希用于变更检测，并非可信签名。无网站部署、上传或外部分享授权。</p></section></body></html>'
    (ROOT/'index.html').write_text(s)
if __name__=='__main__':build()
