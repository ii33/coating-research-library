"""Four original figures and a static offline reader. No model solve/browser."""
from pathlib import Path
from fractions import Fraction as F
import json,html,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f4f6f9','savefig.facecolor':'#f4f6f9','axes.facecolor':'white'})
COL={'teal':'#147d78','orange':'#e6a243','navy':'#203d58','purple':'#80539c','grey':'#c6ced7'}
def save(fig,name):
 fig.savefig(ROOT/'figures'/f'{name}.png',dpi=150,bbox_inches='tight');fig.savefig(ROOT/'figures'/f'{name}.svg',bbox_inches='tight');plt.close(fig)
def block(ax,x,y,w,h,title,body,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012',facecolor=color,edgecolor='none'))
 ax.text(x+.02,y+h-.035,title,va='top',weight='bold',fontsize=13,color=COL['navy']);ax.text(x+.02,y+h-.105,body,va='top',fontsize=11,linespacing=1.5,color=COL['navy'])
def figures():
 fig,ax=plt.subplots(figsize=(12,6));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');fig.suptitle('A result needs a claim and a quantifier',x=.08,ha='left',fontsize=21,weight='bold')
 block(ax,.025,.51,.28,.36,'EXISTS','One verified shared point\ncan support proxy existence\n\nA failed search cannot\nexclude the set','#daf0e9')
 block(ax,.36,.51,.28,.36,'FOR ALL','Keep all retained boxes\nincluding 15 optimum-pruned\n\nA crossing outer bound\nis not a counterexample','#fff0d6')
 block(ax,.695,.51,.28,.36,'MINIMUM','Lower: all eligible boxes\nUpper: verified witness\n\nWide gap = unresolved\nnot proof of poor optimum','#e5e4f2')
 block(ax,.025,.13,.95,.25,'SCOPE GATE BEFORE ANY DECISION','Fixed M0 / M1 + same sample state + inherited source/forward/response contracts\nHard-bound arithmetic only. Actual measurement, source reachability and production remain blocked.','#e2e9ef')
 save(fig,'01_claim_quantifiers')
 p=json.loads((ROOT/'dependencies/t08r3/verification/tiny_final/plane_joint_255.json').read_text());res=json.loads((ROOT/'verification/tiny_final/results.json').read_text());cross=set(next(x for x in res['cases']if x['id']=='all_v_narrow_lower')['result']['claim_crossing_leaf_ids'])
 fig,(ax,bx)=plt.subplots(1,2,figsize=(12,6),gridspec_kw={'width_ratios':[1.7,1]});fig.suptitle('Which unresolved boxes matter to v >= 0.99?',fontsize=19,weight='bold')
 for row in p['leaves']:
  z=list(map(lambda x:float(F(x)),row['box_exact'][0]));v=list(map(lambda x:float(F(x)),row['box_exact'][1]));color=COL['grey']if row['data_class']=='OUT'else COL['orange'];ax.add_patch(Rectangle((v[0],z[0]),v[1]-v[0],z[1]-z[0],facecolor=color,edgecolor='white',linewidth=.5))
  if row['id']in cross:ax.add_patch(Rectangle((v[0],z[0]),v[1]-v[0],z[1]-z[0],fill=False,edgecolor=COL['purple'],linewidth=2))
 ax.axvline(.99,color=COL['navy'],linestyle='--',linewidth=1.5);ax.scatter([1],[1],marker='*',s=150,color=COL['teal'],zorder=5);ax.set(xlim=(.9,1.101),ylim=(float(F(p['domain_exact'][0][0])),float(F(p['domain_exact'][0][1]))),xlabel='Outer-layer multiplier v',ylabel='Shared sample latent z');ax.legend(handles=[Rectangle((0,0),1,1,color=COL['grey'],label='98 OUT'),Rectangle((0,0),1,1,color=COL['orange'],label='32 UNKNOWN'),Line2D([0],[0],color=COL['purple'],label='4 claim-crossing boxes'),Line2D([0],[0],marker='*',color=COL['teal'],linestyle='None',markersize=10,label='Verified proxy point')],loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2,fontsize=9)
 bx.axis('off');bx.text(.05,.93,'Evidence-specific refinement',fontsize=14,weight='bold',color=COL['navy']);bx.text(.05,.81,'32 UNKNOWN retained\n15 are optimum-pruned only\n4 cross this claim boundary\n\nAll v in [0.95, 1.1]:\nCONDITIONAL ACCEPT\n\nAll v in [0.99, 1.1]:\nRETAIN UNKNOWN\n\nNo new measurement taken\nNo hardware task started',va='top',linespacing=1.65);fig.subplots_adjust(top=.88,wspace=.23,bottom=.26);save(fig,'02_claim_crossing_cover')
 fig,ax=plt.subplots(figsize=(12,5.7));fig.suptitle('Same threshold. Different evidence object.',fontsize=21,weight='bold');y=.011583971;e=.001
 ax.axvspan(.010,.012,color='#e1f2ec');ax.axvline(.012,color=COL['navy'],linestyle='--',label='Illustrative upper criterion 0.012')
 ax.plot([y-e,y+e],[1,1],color=COL['orange'],linewidth=8,solid_capstyle='butt');ax.plot([y-e,y-e],[.93,1.07],color=COL['orange']);ax.plot([y+e,y+e],[.93,1.07],color=COL['orange']);ax.scatter([.011583971201202034],[2],color=COL['teal'],s=100,zorder=4)
 ax.text(.01012,2.35,'Point model response: CONDITIONAL ACCEPT',color=COL['teal'],weight='bold');ax.text(.01012,.5,'Synthetic readout interval: RETAIN UNKNOWN',color='#9c641b',weight='bold');ax.text(.01012,.14,'To fit below 0.012 at the same center, a defensible hard bound must be <= 0.000416029.\nThis is an evidence requirement, not permission to shrink uncertainty.',fontsize=10)
 ax.set(xlim=(.010,.013),ylim=(0,2.6),xlabel='M0 reflectance (absolute ratio)',yticks=[1,2],yticklabels=['Readout +/- 0.001','Verified (z, v) = (1, 1)']);ax.legend(loc='upper right',fontsize=10);fig.subplots_adjust(left=.21,bottom=.15,top=.88);save(fig,'03_model_vs_readout')
 fig,ax=plt.subplots(figsize=(12,6.2));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');fig.suptitle('Bounded evidence requests: do not measure blindly',x=.08,ha='left',fontsize=20,weight='bold')
 block(ax,.03,.53,.43,.33,'COMPUTATION GAP','Replay claim-crossing boxes only\nKeep budget, all unresolved leaves\nStop at proof or budget exhaustion','#fff0d6')
 block(ax,.54,.53,.43,.33,'SAME-CHANNEL DATA GAP','Raw paired M0 / M1 observations\nShared calibration + drift retained\nNo divide-by-sqrt(N) assumption','#daf0e9')
 block(ax,.03,.12,.43,.31,'OPERATOR / SOURCE GAP','New state or operator -> new contract\nJoint Q / density / retention required\nUnknown guards never become zero','#e2e9ef')
 block(ax,.54,.12,.43,.31,'REAL ACCEPTANCE GAP','Actual customer criterion unknown\nMethods + sample + calibration missing\nProduction release always false','#e5e4f2')
 save(fig,'04_bounded_requests')

def inline(s):
 s=html.escape(s);return re.sub(r'\[([^\]]+)\]\((https?://[^ )]+)\)',lambda m:'<a href="'+m[2]+'">'+m[1]+'</a>',s)
def md(s):
 lines=s.splitlines();out=[];i=0
 while i<len(lines):
  t=lines[i].strip()
  if not t:i+=1;continue
  if t.startswith('|'):
   rows=[]
   while i<len(lines)and lines[i].strip().startswith('|'):
    cells=lines[i].strip().strip('|').split('|')
    if not all(re.fullmatch(r'[:\- ]+',x)for x in cells):rows.append(cells)
    i+=1
   out.append('<div class="tablewrap"><table>')
   for j,row in enumerate(rows):tag='th'if j==0 else'td';out.append('<tr>'+''.join(f'<{tag}>{inline(c.strip())}</{tag}>'for c in row)+'</tr>')
   out.append('</table></div>');continue
  if t.startswith('#'):
   n=min(4,len(t)-len(t.lstrip('#')));out.append(f'<h{n}>{inline(t.lstrip("# "))}</h{n}>')
  elif t.startswith('- '):out.append('<p class="bullet">• '+inline(t[2:])+'</p>')
  else:out.append('<p>'+inline(t)+'</p>')
  i+=1
 return '\n'.join(out)
def reader():
 docs=sorted((ROOT/'reports').glob('*.md'));toc=[];body=[]
 for i,p in enumerate(docs):
  title=p.read_text().splitlines()[0].lstrip('# ');toc.append(f'<a href="#chapter-{i}">{html.escape(title)}</a>');body.append(f'<section id="chapter-{i}">'+md(p.read_text())+f'<p><a href="reports/{p.name}">原始报告</a></p></section>')
 figs=[('01_claim_quantifiers','量词决定证据要求：存在性、全称性和最优值互不替代'),('02_claim_crossing_cover','4个跨v=0.99门槛的未决盒；15个目标剪枝不能变data OUT'),('03_model_vs_readout','名义模型点通过0.012门槛，合成读数硬界仍跨界；不是实际测量结论'),('04_bounded_requests','补证按缺口路由，固定进入条件和停止条件；无设备任务')]
 gallery=''.join(f'<figure><img src="figures/{n}.png" alt="{html.escape(c)}"><figcaption>{c} · <a href="figures/{n}.svg">SVG</a></figcaption></figure>'for n,c in figs)
 sources=json.loads((ROOT/'sources/source_registry.json').read_text())['sources'];shtml=''.join(f'<li><a href="{html.escape(s["url"],quote=True)}">{s["id"]} · {html.escape(s["title"])}</a><br>{html.escape(s["locator"])}<br>{html.escape(s["summary"])}<br><small>{html.escape(s["limits"])}</small></li>'for s in sources)
 refs=['cases/claims.json','verification/tiny_final/results.json','verification/unit_tests.txt','data/evidence_requests.json','data/frozen_dependencies.json','reviews/narrow_independent_check.md','reviews/AUTHOR_ACCEPTANCE.md','stage_status.json','models/reader.py','models/driver.py','T10_ROUND3_HANDOFF.md'];rhtml=''.join(f'<li><a href="{p}">{p}</a></li>'for p in refs)
 content='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T09 未决证据的有限验收</title><style>*{box-sizing:border-box}body{margin:0;background:#f2f5f8;color:#203448;font:17px/1.85 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}header{padding:50px max(5vw,24px);background:#203d58;color:#fff}header h1{font-size:clamp(28px,4.8vw,46px);line-height:1.3;color:#fff}header p{max-width:950px}main{max-width:1200px;margin:auto;padding:28px 24px}nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;background:#fff;padding:24px;border-radius:12px}nav a{font-size:14px}section{background:#fff;padding:clamp(20px,4vw,48px);margin:28px 0;border-radius:12px}h1,h2,h3{line-height:1.45;color:#203d58}h1{font-size:29px}h2{font-size:23px;margin-top:32px}a{color:#147d78;overflow-wrap:anywhere}p{margin:15px 0}small,figcaption{font-size:14px;color:#5b6d7e}figure{margin:26px 0}img{display:block;width:100%;height:auto}figcaption{margin:10px 0}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.65}td,th{border:1px solid #d5dde5;padding:10px 12px;text-align:left;vertical-align:top}th{background:#e6edf2}li{margin:14px 0}.notice{padding:20px 0;color:#70501e}.bullet{padding-left:14px}footer{font-size:13px;color:#5b6d7e}@media print{body{background:white}header{background:white;color:black}header h1{color:black}nav{display:none}section{padding:10px 0}figure{break-inside:avoid}}</style></head><body><header><p>COATING RESEARCH · ROUND 3 · T09</p><h1>未决证据的有限验收</h1><p>27个明确主张 · 32个UNKNOWN完整保留 · 同一双通道与样品状态</p><p>模型点通过，不代表读数区间通过；限定命题可用，不代表生产合格</p></header><main><p class="notice">只在编码合成模型与项目例值下作条件判断。客户要求unknown；来源实现未证；正式模型链pending。PNG实际像素检查，HTML布局unverified。</p><nav>'''+''.join(toc)+'''<a href="#figures">原创图</a><a href="#sources">一手来源</a><a href="#evidence">复现入口</a></nav><section id="figures"><h1>把不确定结论读对</h1>'''+gallery+'</section>'+''.join(body)+'''<section id="sources"><h1>一手来源与访问边界</h1><ul>'''+shtml+'''</ul></section><section id="evidence"><h1>证据与参考实现</h1><ul>'''+rhtml+'''</ul><p>核心验证无需网络、浏览器或相邻目录。只有明确tiny执行才重放数值；默认plan_only。</p></section><footer>Local freeze only · no upload / push / production release / next-stage execution</footer></main></body></html>'''
 (ROOT/'reader.html').write_text(content)
if __name__=='__main__':figures();reader()
