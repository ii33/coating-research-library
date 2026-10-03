"""Minimal offline Markdown renderer for this authored report; no network/runtime JS."""
from pathlib import Path
import base64,html,re
R=Path(__file__).resolve().parents[1]

def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',r'<a href="\2">\1</a>',s)

def render(text):
    out=[];para=[];code=[];in_code=False;in_list=False
    def flush():
        if para:out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
    for line in text.splitlines():
        if line.startswith('```'):
            flush()
            if in_list:out.append('</ul>');in_list=False
            if in_code:out.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>');code=[]
            in_code=not in_code;continue
        if in_code:code.append(line);continue
        if line.startswith('#'):
            flush()
            if in_list:out.append('</ul>');in_list=False
            level=min(4,len(line)-len(line.lstrip('#'))+1);out.append(f'<h{level}>'+inline(line.lstrip('# '))+f'</h{level}>')
        elif line.startswith('- '):
            flush()
            if not in_list:out.append('<ul>');in_list=True
            out.append('<li>'+inline(line[2:])+'</li>')
        elif not line.strip():
            flush()
            if in_list:out.append('</ul>');in_list=False
        else:para.append(line)
    flush()
    if in_list:out.append('</ul>')
    if in_code:raise ValueError('unclosed code block')
    return '\n'.join(out)

parts=[('scope','01_scope_physical_objective.md'),('topology','02_topology_trust_region.md'),('bounds','03_forward_intervals_and_decisions.md'),('algorithm','04_complete_algorithm_and_cache.md'),('results','05_results_and_counterexamples.md'),('reproduce','06_reproduction_limits_and_handoff.md')]
nav='<nav aria-label="章节">'+''.join(f'<a href="#{key}">{i+1} '+html.escape(name[3:-3].replace('_',' '))+'</a>' for i,(key,name) in enumerate(parts))+'<a href="#sources">来源</a><a href="#handoff">T04候选</a></nav>'
body='<header><p>T03 · ROUND 3 · v0.1.0 · 2026-10-02 UTC</p><h1>事件感知修正板局部信任域</h1><p>同一冻结有限厚板 · 仅横移与半宽 · 完整前向区间验证</p><p>本地理论与接口冻结。正式模型链、连续源验证与实机证据尚未完成；T02旧缺口不升级。</p></header>'+nav
for key,name in parts:
    body+=f'<section id="{key}">'+render((R/'reports'/name).read_text())
    if key in ('topology','results'):
        img='01_topology_step.png' if key=='topology' else '02_objective_and_gradients.png'
        uri='data:image/png;base64,'+base64.b64encode((R/'figures'/img).read_bytes()).decode()
        alt='仿射guard的精确裁剪与忽略曲率的一阶反例' if key=='topology' else '同一目标的区间对比以及反号和纯事件梯度'
        body+=f'<figure><img src="{uri}" alt="{alt}"><figcaption>{alt}。图像像素已检查；HTML浏览器布局未验证。</figcaption></figure>'
    body+='</section>'
body+='<section id="sources">'+render((R/'sources/source_cards.md').read_text())+'</section>'
body+='<section id="handoff">'+render((R/'T04_ROUND3_HANDOFF.md').read_text())+'</section>'
css='''*{box-sizing:border-box}body{margin:0;background:#f7f8fa;color:#17212b;font:17px/1.8 system-ui,"Noto Sans CJK SC",sans-serif}main{max-width:1080px;margin:auto;padding:44px 36px 80px;background:white}header p{color:#4a5965}h1{font-size:36px;line-height:1.3}h2{margin:46px 0 18px;font-size:27px}h3{margin:30px 0 12px;font-size:21px}h4{font-size:18px}p{margin:12px 0}nav{display:flex;gap:10px 20px;flex-wrap:wrap;padding:20px 0}a{color:#155b93;text-decoration-thickness:1px;text-underline-offset:3px}pre{overflow-x:auto;padding:20px;background:#f0f3f6;font:14px/1.65 ui-monospace,monospace;border-radius:6px}code{overflow-wrap:anywhere}li{margin:8px 0}img{display:block;max-width:100%;height:auto}figure{margin:32px 0}figcaption{font-size:14px;color:#53616d;margin-top:12px}section{scroll-margin-top:20px}footer{margin-top:44px;font-size:14px;color:#596771}@media(max-width:650px){main{padding:22px 18px}h1{font-size:28px}h2{font-size:23px}body{font-size:16px}}@media print{body{background:white}main{max-width:none;padding:0}nav{display:none}a{color:inherit}figure,pre{break-inside:avoid}}'''
page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T03第三轮 事件感知修正板局部信任域</title><style>'+css+'</style></head><body><main>'+body+'<footer>静态离线读者版 · 不含第三方全文 · 无外部脚本或追踪资源 · 浏览器布局未验证</footer></main></body></html>'
(R/'reader.html').write_text(page)
print('Built static reader with 6 report sections, source notes, candidate handoff and 2 embedded PNGs; browser layout unverified')
