"""Self-contained original-text reader. No assets, network calls or third-party originals."""
from pathlib import Path
import html,json,re
ROOT=Path(__file__).resolve().parents[1]
def inline(s):
    s=html.escape(s)
    def link(m):
        label,url=m.groups()
        if url.startswith('https://'):
            return '<a href="'+url+'" rel="noreferrer" target="_blank">'+label+'</a>'
        return label+'（本地依赖来源，未随reader复制）'
    return re.sub(r'\[([^\]]+)\]\(([^\s]+)\)',link,s)
def render(md):
    out=[]; paragraphs=[]; ul=False; table=[]
    def para():
        if paragraphs:out.append('<p>'+inline(' '.join(paragraphs))+'</p>');paragraphs.clear()
    def end_ul():
        nonlocal ul
        if ul:out.append('</ul>');ul=False
    def end_table():
        if not table:return
        rows=[r for r in table if not re.match(r'^\|[\s:|\-]+\|$',r)]
        out.append('<div class="tablewrap"><table>')
        for i,row in enumerate(rows):
            tag='th' if i==0 else 'td'
            out.append('<tr>'+''.join('<'+tag+'>'+inline(c.strip())+'</'+tag+'>' for c in row.strip('|').split('|'))+'</tr>')
        out.append('</table></div>');table.clear()
    for line in md.splitlines():
        if line.startswith('|'):
            para();end_ul();table.append(line);continue
        end_table()
        if not line.strip():para();end_ul();continue
        if line.startswith('#'):
            para();end_ul();level=min(5,len(line)-len(line.lstrip('#'))+1)
            out.append(f'<h{level}>'+inline(line.lstrip('#').strip())+f'</h{level}>');continue
        if re.match(r'^(- |\d+\. )',line):
            para()
            if not ul:out.append('<ul>');ul=True
            out.append('<li>'+inline(re.sub(r'^(- |\d+\. )','',line))+'</li>');continue
        if line.startswith('    '):
            para();end_ul();out.append('<pre>'+html.escape(line.strip())+'</pre>');continue
        paragraphs.append(line)
    para();end_ul();end_table();return '\n'.join(out)
reports=sorted((ROOT/'reports').glob('*.md'))
nav='';body=''
for i,p in enumerate(reports,1):
    title=p.read_text().splitlines()[0].lstrip('# ').strip()
    nav+=f'<a href="#chapter-{i}">{html.escape(title)}</a>'
    body+=f'<article class="chapter" id="chapter-{i}">{render(p.read_text())}</article>'
sources=json.loads((ROOT/'sources/source_registry.json').read_text())['sources']
sourcelines=[]
for s in sources:
    url=s['url']
    source_link=f'<a href="{html.escape(url)}" target="_blank" rel="noreferrer">官方来源</a>' if url.startswith('https://') else '本地独立派生分析，原件不在reader中'
    sourcelines.append('<details><summary>'+html.escape(s['source_id']+' '+s['title'])+'</summary><p>'+source_link+'</p>'+''.join('<p><b>'+k+'：</b>'+html.escape(s[key])+'</p>' for k,key in [('读取范围','locator'),('实际访问级别','access_level'),('时点状态','status_as_observed'),('原创短摘要','summary'),('限制','limits')])+'</details>')
reader='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T09第二轮 可追溯验证证据合同</title><style>
:root{color-scheme:light;--ink:#142c3b;--muted:#52646d;--line:#d3dee4;--bg:#f4f7f8;--accent:#006b75}*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--bg);font:17px/1.75 system-ui,-apple-system,"Noto Sans CJK SC","Microsoft YaHei",sans-serif}header{background:#112d3d;color:white;padding:48px max(24px,5vw)}header .eyebrow{color:#a6d6d5;letter-spacing:.13em;font-size:13px}h1{font-size:clamp(28px,3.2vw,46px);line-height:1.25;max-width:1020px;margin:16px 0}header p{max-width:1000px;color:#d2e3e9}.chips{display:flex;gap:10px;flex-wrap:wrap}.chips span{border:1px solid #628391;padding:3px 12px;border-radius:18px;font-size:13px}.layout{display:grid;grid-template-columns:270px minmax(0,1fr);max-width:1480px;margin:auto;gap:34px;padding:32px}aside{position:sticky;top:18px;align-self:start;max-height:94vh;overflow:auto}aside a{display:block;padding:7px 10px;color:var(--muted);text-decoration:none;border-left:2px solid transparent;font-size:14px}aside a:hover,aside a:focus{border-color:var(--accent);background:#e2eef0;color:var(--accent)}aside input{width:100%;padding:12px;margin-bottom:12px;border:1px solid #a7bac5;border-radius:8px;font:inherit;background:white}main{min-width:0}.intro,.chapter,.sources,.artifacts{background:white;border:1px solid var(--line);border-radius:12px;padding:34px 42px;margin-bottom:24px}.chapter{scroll-margin-top:20px}h2{font-size:29px;line-height:1.4;margin-top:0}h3{font-size:21px;margin-top:34px}p{margin:14px 0}a{color:var(--accent);overflow-wrap:anywhere}li{margin:8px 0}pre{background:#edf3f5;padding:12px;overflow:auto;font-size:13px;border-radius:5px}.tablewrap{overflow-x:auto;margin:24px 0}table{border-collapse:collapse;width:100%;min-width:650px;font-size:14px}th,td{border:1px solid var(--line);padding:12px 14px;text-align:left;vertical-align:top}th{background:#e9f0f4}details{border-top:1px solid var(--line);padding:16px 0}summary{cursor:pointer;font-weight:650}details p{font-size:14px}.muted{color:var(--muted);font-size:14px}.noresults{display:none;padding:30px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}.stats b{font-size:28px;display:block}.stats div{padding:14px;background:#f1f6f7;border-radius:8px}footer{padding:32px;text-align:center;color:var(--muted);font-size:13px}.hidden{display:none!important}@media(max-width:820px){.layout{display:block;padding:16px}aside{position:static;max-height:none;margin-bottom:18px}aside nav{display:grid;grid-template-columns:1fr 1fr}aside a{font-size:12px}.intro,.chapter,.sources,.artifacts{padding:23px 20px}header{padding:30px 22px}.stats{grid-template-columns:repeat(2,1fr)}h2{font-size:23px}body{font-size:16px}}@media print{aside,header .chips,.noresults{display:none}.layout{display:block;padding:0}.chapter{break-before:page;border:0}.intro,.sources,.artifacts{border:0}a{color:inherit}header{background:white;color:black}header p{color:black}details{display:block}}
</style></head><body><header><div class="eyebrow">COATING RESEARCH LIBRARY · T09 / ROUND 2</div><h1>可追溯验证与合格判定<br>从条件反演到证据合同</h1><p>先确认数字从哪里来、在什么条件下有效，再判断它能支持哪一类结论。合成拟合优度、局部秩和代码检查都不能签发设备或生产资格。</p><div class="chips"><span>2026-10-02 本地研究</span><span>实际硬件未知</span><span>高算量待设备</span><span>未上传 未部署</span></div></header><div class="layout"><aside><label for="q" class="muted">搜索报告关键词</label><input id="q" placeholder="例如 相关性 / 失锁 / 保护带"><nav>'''+nav+'''<a href="#sources">来源与访问边界</a><a href="#artifacts">合同与复现文件</a></nav></aside><main><section class="intro"><h2>这一轮交付什么</h2><p>把材料身份、测量结果、设计性能、生产验收、环境及损伤资格分开建账。新增2026年BIPM非线性修订与Global ACI现行文件核验；MXC工程案例转为读数来源与事件证据要求。</p><div class="stats"><div><b>10</b>工程章节</div><div><b>22</b>分级来源</div><div><b>17</b>证据门槛</div><div><b>15</b>合成反例</div></div><p class="muted">只完成研究合同和tiny代码检查。真实样品、计量能力、设备接口、产品资格与完整指定审核链尚未完成。</p></section><div class="noresults" id="empty">没有匹配章节，请换一个关键词。</div>'''+body+'''<section class="sources" id="sources"><h2>来源与访问边界</h2><p>官方目录不等于完整规范已读。展开查看具体读取范围、时间状态和不支持的推论。本reader不收录第三方原文或厂家手册截图。</p>'''+''.join(sourcelines)+'''</section><section class="artifacts" id="artifacts"><h2>合同与复现文件</h2><ul><li><a href="contracts/evidence_contract_template.json">完整人工审阅规划模板</a></li><li><a href="contracts/evidence_checklist.csv">17项证据门槛清单 CSV</a></li><li><a href="contracts/evidence_packet.schema.json">tiny记录 JSON Schema</a></li><li><a href="contracts/README.md">合同实现边界</a></li><li><a href="examples/tiny_results.json">15场景及解析公式结果</a></li><li><a href="reviews/tiny_test_output.txt">22项小型测试执行记录</a></li><li><a href="reviews/independent_narrow_check.md">一次独立窄检查及作者修正</a></li><li><a href="T10_ROUND2_HANDOFF.md">T10有界交接</a></li><li><a href="reader_manifest.json">reader精确文件清单</a></li></ul><p>本地命令</p><pre>PYTHONDONTWRITEBYTECODE=1 python models/evidence_contract.py --examples
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python models/reader.py --isolated</pre><p class="muted">代码不会访问网络、读取设备或释放产品。完整规划模板不是tiny检查器已全部验证的协议。</p></section></main></div><footer>原创研究分析 · 指定用途与条件之外不作资格推断 · 本地freeze后停止</footer><script>
const input=document.getElementById('q'),chapters=[...document.querySelectorAll('.chapter')];input.addEventListener('input',()=>{const q=input.value.trim().toLowerCase();let visible=0;chapters.forEach(c=>{const match=!q||c.textContent.toLowerCase().includes(q);c.classList.toggle('hidden',!match);visible+=match;});document.getElementById('empty').style.display=visible?'none':'block';});
</script></body></html>'''
(ROOT/'index.html').write_text(reader,encoding='utf-8')
print('Offline reader bytes',len(reader.encode()))
