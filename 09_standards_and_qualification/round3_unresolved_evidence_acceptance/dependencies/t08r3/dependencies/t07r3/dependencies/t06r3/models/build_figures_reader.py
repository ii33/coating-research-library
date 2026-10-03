"""Build original diagrams and a network-free self-contained HTML manual.
No browser launch; browser layout is explicitly unverified.
"""
from pathlib import Path
import json,html,re,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
from bounded_optics import *
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'#f7f9fc','figure.facecolor':'#f7f9fc','axes.facecolor':'white'})

def figures():
    x=json.loads((ROOT/'verification/tiny_results.json').read_text());c=load_case();r=json.loads((ROOT/'data/legacy_selection.json').read_text())['records'][0]
    # Figure 1: full-range separation plus zoom; no sampled spectrum masquerading as bounds.
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),gridspec_kw={'width_ratios':[1,1.2]})
    colors=['#185a9d','#c64d32','#26866b']
    for ax in axs:
        for j,(key,color) in enumerate(zip(['A','B','C'],colors)):
            a,b=x['outcomes'][key]['R_bounds'];a*=100;b*=100
            ax.plot([a-.1,b+.1],[j,j],lw=17,color=color,alpha=.2,solid_capstyle='butt')
            ax.plot([a,b],[j,j],lw=7,color=color,solid_capstyle='butt')
        ax.axvline(5,color='#666',linestyle='--',label='5% target');ax.set_yticks([0,1,2],['A: dose 1','B: dose 1.25','C: dose 1.002']);ax.set_xlabel('Power-weighted reflectance (%)');ax.grid(axis='x',alpha=.2);ax.set_ylim(2.5,-.5)
    axs[0].set_xlim(0,46);axs[0].set_title('Full conservative enclosures');axs[1].set_xlim(0,7);axs[1].set_title('Separation after ±0.1 percentage-point error')
    axs[1].annotate('A/B gap ≥ 2.321 percentage points',xy=(4.6,.52),xytext=(3.5,.9),ha='center',fontsize=10)
    fig.suptitle('T06 R3 | One MIR operator, three synthetic dose variants',fontsize=15,fontweight='bold');fig.text(.5,.015,'4.25 / 4.26 / 4.27 µm, weights 1/4 / 1/2 / 1/4; normal incidence; lossless, semi-infinite substrate',ha='center',fontsize=10);fig.tight_layout(rect=[0,.06,1,.94]);save(fig,'01_bounded_mir_response')
    # Figure 2: shared uncertainty is a line, not independent two-layer square.
    fig,axs=plt.subplots(1,2,figsize=(11.4,4.6));ax=axs[0]
    ax.add_patch(Rectangle((.99,.99),.02,.02,facecolor='#f4c8bc',edgecolor='#c64d32',alpha=.55));ax.plot([.99,1.01],[.99,1.01],color='#185a9d',lw=4,label='One shared latent z')
    ax.set(xlim=(.987,1.013),ylim=(.987,1.013),xlabel='Layer 1: d1 / d1,ref',ylabel='Layer 2: d2 / d2,ref',title='Independent resampling invents off-line states');ax.legend(loc='upper left',fontsize=9);ax.grid(alpha=.2)
    ax=axs[1];ax.bar(['Shared error','False independence'],[6,6**.5],color=['#185a9d','#c64d32'],width=.55);ax.set(title='Six equal positive sensitivities',ylabel='Standard uncertainty of sum / single-layer σ');ax.text(0,6.15,'6σ',ha='center');ax.text(1,2.6,'√6σ ≈ 2.45σ',ha='center');ax.set_ylim(0,7);ax.grid(axis='y',alpha=.2)
    fig.suptitle('Correlation cannot be replaced by independent layer draws',fontsize=15,fontweight='bold');fig.text(.5,.01,'Analytic counterexample only; no probability distribution or Monte Carlo is assigned to the main hard bounds',ha='center',fontsize=9);fig.tight_layout(rect=[0,.06,1,.92]);save(fig,'02_shared_error_counterexample')
    # Figure 3: layer provenance and unit conversion.
    n,d,order=incident_stack(r);fig,ax=plt.subplots(figsize=(11,4.8));pos=0
    for j,(v,old) in enumerate(zip(d,order)):
        name=r['layers'][old-1]['material'];v=float(v);color='#597ec4' if name=='ZnS' else '#55a6a3'
        ax.barh(0,v,left=pos,height=.5,color=color,edgecolor='white')
        if v<.3:
            ax.text(pos+v/2,0,name,ha='center',va='center',color='white',fontsize=8)
            ax.annotate(f'old #{old}: {v:.5f} µm',xy=(pos+v/2,-.24),xytext=(pos+v/2,-.43),ha='center',va='center',fontsize=9,arrowprops={'arrowstyle':'-','color':'#52647c'})
        else:ax.text(pos+v/2,0,f'{name}\nold #{old}\n{v:.5f}',ha='center',va='center',color='white',fontsize=9)
        pos+=v
    ax.set_yticks([]);ax.set_xlim(-.4,pos+.4);ax.set_xlabel('Cumulative nominal physical thickness from incident side (µm)');ax.text(-.1,.35,'Air →',ha='left');ax.text(pos+.05,0,'Ge\nhalf-space',va='center',fontsize=10);ax.set_ylim(-.55,.65);ax.set_title('Legacy order reversed: [1, 2, 3, 4, 5, 6] → [6, 5, 4, 3, 2, 1]',pad=20)
    fig.suptitle('S-AR-DUALIR6 | Explicit layer-order and nm → µm evidence',fontsize=15,fontweight='bold');fig.text(.5,.03,'All n values are frozen lossless synthetic seed constants. Layer widths are nominal, not manufacturing tolerances.',ha='center',fontsize=10);fig.tight_layout(rect=[0,.1,1,.90]);save(fig,'03_order_units_provenance')
    # Save conversion machine evidence.
    rows=[];h=I(*c['bridge']['t04_response']['signed_thickness_change_m'])/f(c['material']['normalization_h_ref_m'])
    for i,(di,old) in enumerate(zip(d,order),1):
        v=r['layers'][old-1];rows.append({'incident_layer':i,'legacy_substrate_layer':old,'material':v['material'],'original_thickness_nm':v['thickness_nm'],'thickness_um_exact':str(di),'nominal_um':float(di),'A_shared_thickness_bounds_um':(I(di)*h).floats(),'note':'marginal bounds only; NOT independent layer boxes'})
    (ROOT/'verification/order_units_and_layer_bounds.json').write_text(json.dumps({'recipe':r['id'],'source_order':'substrate_to_incident_medium','target_order':'incident_to_substrate','source_unit':'nm','target_unit':'um','conversion':'exact rational division by1000 of original encoded float','rows':rows},indent=2)+'\n')
def save(fig,name):
    fig.savefig(ROOT/f'figures/{name}.png',dpi=160);fig.savefig(ROOT/f'figures/{name}.svg');plt.close(fig)
def inline(s):
    s=html.escape(s)
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return s

def markdown(text):
    out=[];incode=False;table=False;ul=False
    for line in text.splitlines():
        if line.startswith('```'):
            if ul:out.append('</ul>');ul=False
            out.append('</code></pre>' if incode else '<pre><code>');incode=not incode;continue
        if incode:out.append(html.escape(line)+'\n');continue
        if line.startswith('|'):
            if not table:out.append('<div class="table-scroll"><table>');table=True
            cells=line.strip('|').split('|')
            if all(re.fullmatch(r'\s*:?-+:?\s*',x) for x in cells):continue
            out.append('<tr>'+''.join('<td>'+inline(v.strip())+'</td>' for v in cells)+'</tr>');continue
        if table:out.append('</table></div>');table=False
        if line.startswith('- '):
            if not ul:out.append('<ul>');ul=True
            out.append('<li>'+inline(line[2:])+'</li>');continue
        if ul:out.append('</ul>');ul=False
        if not line.strip():continue
        h=re.match(r'^(#{1,4}) (.*)',line)
        if h:out.append(f'<h{len(h[1])}>'+inline(h[2])+f'</h{len(h[1])}>')
        elif line.startswith('    '):out.append('<pre>'+html.escape(line[4:])+'</pre>')
        else:out.append('<p>'+inline(line)+'</p>')
    if table:out.append('</table></div>')
    if ul:out.append('</ul>')
    return '\n'.join(out)
def build_reader():
    reports=sorted((ROOT/'reports').glob('*.md'));nav=''.join(f'<a href="#report{i}">{html.escape(p.stem[:2])} {html.escape(p.read_text().splitlines()[0].lstrip("# "))}</a>' for i,p in enumerate(reports,1))
    chapters=[]
    for i,p in enumerate(reports,1):
        body=markdown(p.read_text());extra=''
        for name,cap in ({1:[('03_order_units_provenance','图1：旧层表反序及nm→μm证据')],2:[('02_shared_error_counterexample','图2：共享变量与错误独立化反例')],4:[('01_bounded_mir_response','图3：有限MIR算子的有界反射率及误差扩张')]}).get(i,[]):extra+=f'<figure><img src="figures/{name}.png" alt="{cap}"><figcaption>{cap}。原创图；仅合成条件。</figcaption></figure>'
        chapters.append(f'<section id="report{i}">{body}{extra}</section>')
    sources=json.loads((ROOT/'sources/source_registry.json').read_text());sourcehtml=''.join(f'<li>{html.escape(x["id"]+": "+x["title"])}'+(f' <a href="{html.escape(x["url"])}">来源页面</a>' if 'url' in x else '')+'</li>' for x in sources)
    codehtml=''.join(f'<li><a href="{p.relative_to(ROOT).as_posix()}">{p.name}</a></li>' for p in sorted((ROOT/'models').glob('*.py')))
    doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T06 R3 有界光学响应</title><style>
:root{--ink:#182c45;--muted:#52647c;--line:#dce4ef;--accent:#185a9d}*{box-sizing:border-box}body{margin:0;background:#f5f8fc;color:var(--ink);font:16px/1.85 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}header{background:#173b62;color:white;padding:42px max(5vw,24px)}header h1{margin:5px 0;font-size:clamp(25px,3vw,38px)}header p{max-width:980px;color:#ddeaf9}.badge{display:inline-block;border:1px solid #9db8d6;border-radius:5px;padding:3px 10px;margin:4px 8px 4px 0;font-size:13px}.shell{max-width:1320px;margin:auto;display:grid;grid-template-columns:250px minmax(0,1fr);gap:35px;padding:30px 24px}nav{position:sticky;top:20px;align-self:start}nav a{display:block;margin:7px 0;padding:8px 10px;color:var(--accent);border-left:3px solid var(--line);text-decoration:none;font-size:14px}section{background:white;border:1px solid var(--line);padding:30px;margin-bottom:28px;border-radius:8px;scroll-margin-top:20px}h1{line-height:1.5}h2{margin-top:30px;font-size:21px;color:#1d527d}p{margin:15px 0}a{color:#185a9d}code{background:#eff4f9;padding:2px 4px;border-radius:3px;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eff4f9;padding:14px;font-size:13px;line-height:1.7}pre code{padding:0}.table-scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td{padding:10px;border:1px solid var(--line);vertical-align:top}tr:first-child{background:#edf4fc;font-weight:600}figure{margin:26px 0}img{width:100%;height:auto;display:block}figcaption{font-size:13px;color:var(--muted);margin-top:8px}.warning{border-left:5px solid #d7922a;background:#fff7e8;padding:14px 18px;font-size:14px}footer{padding:25px;text-align:center;color:var(--muted);font-size:13px}@media(max-width:850px){.shell{display:block;padding:18px 12px}nav{position:static;margin-bottom:20px}section{padding:21px}header{padding:28px 20px}}@media print{nav{display:none}.shell{display:block}section{break-before:page;border:0}header{background:white;color:black}header p{color:#333}}
</style></head><body><header><div>T06 · ROUND 3 · ENGINEERING REFERENCE</div><h1>有界膜厚与共享误差<br>怎样传到一个可区分的光学目标？</h1><p>限定一个六层IR种子、固定材料与测量算子，保留全forward来源资格与跨层相关性。区间结论只属于明确的合成模型。</p><span class="badge">LOCAL FREEZE</span><span class="badge">SYNTHETIC ONLY</span><span class="badge">FORMAL REVIEW PENDING</span><span class="badge">HEAVY PLAN ONLY</span></header>'''
    doc+=f'<div class="shell"><nav>{nav}<a href="#sources">来源与算法</a></nav><main><div class="warning">HTML布局未验证：沿用已有localhost/socket权限限制，不作新浏览器或headless尝试。此页做离线资源与静态结构检查；PNG另作实际像素检查。无真实材料参数和生产认证。</div>'+''.join(chapters)+f'<section id="sources"><h1>来源与完整算法</h1><ul>{sourcehtml}</ul><h2>本包代码</h2><ul>{codehtml}</ul><p><a href="verification/tiny_results.json">原始区间结果</a> · <a href="verification/unit_tests.txt">小测试记录</a> · <a href="reviews/narrow_optical_check.md">一次独立窄核查</a> · <a href="T07_ROUND3_HANDOFF.md">T07候选交接</a></p></section></main></div><footer>冻结的条件研究证据 · 不含论文原文 · 不依赖外部脚本/字体/网络 · 不自动推进下一题</footer></body></html>'
    (ROOT/'reader.html').write_text(doc)
if __name__=='__main__':figures();build_reader()
