"""Original static figures and HTML reader. No browser/server/model optimization."""
from pathlib import Path
import json,html,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f4f6f9','savefig.facecolor':'#f4f6f9','axes.facecolor':'white'})
C={'teal':'#107d7a','blue':'#244863','gold':'#dfad50','purple':'#785595','gray':'#b7c3ca'}
def save(fig,name):
 fig.savefig(ROOT/'figures'/f'{name}.png',dpi=150,bbox_inches='tight');fig.savefig(ROOT/'figures'/f'{name}.svg',bbox_inches='tight');plt.close(fig)
def box(ax,x,y,w,h,title,body,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.013',facecolor=color,edgecolor='none'))
 ax.text(x+.02,y+h-.035,title,va='top',weight='bold',fontsize=12,color=C['blue']);ax.text(x+.02,y+h-.11,body,va='top',fontsize=10.5,linespacing=1.5,color=C['blue'])
def figures():
 p=json.loads((ROOT/'verification/tiny_final.json').read_text())['physics']
 fig,(ax,bx)=plt.subplots(1,2,figsize=(12.8,6));fig.suptitle('Equal totals do not define a material state',fontsize=21,weight='bold',y=.98)
 vals=[p['history'][k]['final_occupancy']for k in ('pulse_then_repair','repair_then_pulse','concurrent_equal_integrals')]
 bars=ax.bar(['Pulse then\nrepair','Repair then\npulse','Concurrent'],vals,color=[C['teal'],C['purple'],C['gold']],width=.65)
 for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+.025,f'{v:.6f}',ha='center',fontsize=11)
 ax.set(ylim=(0,.82),ylabel='Final active occupancy x',title='Same integrated creation and repair')
 for y,label,cells,value,col in [(1,'A',[(0,0),(1,1)],43.75,C['teal']),(0,'B',[(0,1),(1,0)],81.25,C['purple'])]:
  bx.text(-.9,y+.31,label,weight='bold',color=col,fontsize=18)
  for i,(en,an)in enumerate(cells):
   txt=f'{[50,150][en]} eV / {[0,60][an]} deg';bx.add_patch(Rectangle((i*1.65,y),1.5,.55,color=col,alpha=.16));bx.text(i*1.65+.75,y+.28,txt,ha='center',va='center',fontsize=11)
  bx.text(3.35,y+.28,f'{value:.2f} eV',va='center',color=col,weight='bold')
 bx.text(-.9,1.93,'Same energy AND angle marginals',fontsize=12,weight='bold');bx.text(-.9,-.5,'Each cell carries half the dose\nIllustrative response K = E cos²(theta)\nThis is not a real defect or sputter-yield law',linespacing=1.6,fontsize=11)
 bx.set(xlim=(-1,4.7),ylim=(-.8,2.2));bx.axis('off');fig.subplots_adjust(wspace=.22,top=.85,bottom=.17);save(fig,'01_history_and_joint_spectrum')
 fig,(ax,bx)=plt.subplots(1,2,figsize=(12.8,5.8));fig.suptitle('Finite bounds help. They do not invent n/k.',fontsize=21,weight='bold')
 lo,hi=p['neutral_bounds']['finite_neutral_bound']['x_bounds'];ax.hlines(1,0,1,colors=C['gray'],linewidth=12);ax.hlines(2,lo,hi,colors=C['teal'],linewidth=12);ax.scatter([lo,hi],[2,2],s=30,color=C['blue']);ax.text(.46,2.27,f'[{lo:.4f}, {hi:.4f}]',ha='center');ax.set(xlim=(-.02,1.02),ylim=(.4,2.7),yticks=[1,2],yticklabels=['Unknown creation\nphysical support only','Finite rate bounds\nconditional outer box'],xlabel='Active occupancy x')
 rr=p['mass_closed_constitutive'];vals=[rr['n_ratio'],rr['h_ratio'],rr['optical_thickness_ratio']];bars=bx.bar(['n / n0','h / h0','nh / n0h0'],vals,color=[C['teal'],C['gold'],C['purple']]);bx.axhline(1,color=C['blue'],linestyle='--')
 for b,v in zip(bars,vals):bx.text(b.get_x()+b.get_width()/2,v+.02,f'{v:.5f}',ha='center')
 bx.set(ylim=(0,1.2),title='Synthetic mass-closed densification',ylabel='Ratio to baseline');fig.text(.07,.045,'Left: float-reference endpoints, not rigorous interval certificates.   Right: fixed-polarizability hypothesis, not calibrated material data.',fontsize=10,color=C['blue']);fig.subplots_adjust(left=.17,wspace=.4,top=.83,bottom=.18);save(fig,'02_bounds_and_optical_mass')
 fig,ax=plt.subplots(figsize=(12.8,7));ax.axis('off');ax.set(xlim=(0,1),ylim=(0,1));fig.suptitle('Evidence belongs to a specific claim',fontsize=21,weight='bold',y=.98)
 box(ax,.02,.68,.45,.23,'CORRECTED CHARGE ENERGY','Surface charge spectrum + calibrated support\nCan retain charged power; particles / neutrals unknown','#d9efe9')
 box(ax,.53,.68,.45,.23,'SAMPLE OBSERVATION','Sample + operator + raw reading + uncertainty\nCan describe this specimen; process causality unknown','#d9efe9')
 box(ax,.02,.37,.45,.23,'PROCESS TO NEW STATE','Joint spectrum + neutral / T / potential history\nResponse law + net / all-time inventory guards','#fff0d4')
 box(ax,.53,.37,.45,.23,'NEW STATE TO OPTICS','Same-state n/k, density, h + joint uncertainty\nNew validated domain and optical operator','#e7e2f1')
 box(ax,.02,.055,.96,.22,'CHANGED OR UNKNOWN STATE: NEVER MUTATE THE FROZEN OPERATOR','New child contract keeps parent source / forward / response / operator hashes.\nOld n/k and density remain excluded. Conditional dossier readiness is not model execution or qualification.','#e1e9ef')
 save(fig,'03_output_specific_admission')
 fig,ax=plt.subplots(figsize=(12.8,7.1));ax.axis('off');ax.set(xlim=(0,1),ylim=(0,1));fig.suptitle('Source ledger: evidence origin stays visible',fontsize=21,weight='bold',y=.98)
 box(ax,.02,.62,.45,.29,'IG-S01 | YbF3 / Kaufman','Publisher sections rechecked\nGe is a witness substrate\nComposition / optical / water tradeoffs\nNominal voltage is not local energy','#d9efe9')
 box(ax,.53,.62,.45,.29,'IG-S02 | MgF2 / Kaufman','Publisher result sections rechecked\nMethods: frozen official excerpts\nOptical / adhesion tradeoff; interface history\nSource current is not specimen dose','#d9efe9')
 box(ax,.02,.24,.45,.28,'FROZEN PROJECT CHAIN','T01 -> T09: copied dependency bytes\nSynthetic ZnS / YF3 / Ge proxies\n142 dependencies verified by hash\nNot measured material or reachable source','#e1e9ef')
 box(ax,.53,.24,.45,.28,'THIS ROUND\'S ORIGINAL MODELS','History + joint-angle + bound counterexamples\nAll numeric coefficients are synthetic\nNo fitted actual n/k or density\nNo optical / hardware execution','#e7e2f1')
 ax.text(.5,.09,'YbF3 is not YF3.  Candidate state is not actual evidence.  Originals excluded.',ha='center',fontsize=12,weight='bold',color=C['blue']);save(fig,'04_source_ledger')

def inline(s):
 s=html.escape(s);return re.sub(r'\[([^\]]+)\]\((https?://[^ )]+)\)',lambda m:'<a href="'+m[2]+'">'+m[1]+'</a>',s)
def md(s):
 lines=s.splitlines();out=[];i=0
 while i<len(lines):
  t=lines[i].strip()
  if not t:i+=1;continue
  if lines[i].startswith('    '):
   code=[]
   while i<len(lines)and (lines[i].startswith('    ')or not lines[i].strip()):code.append(lines[i][4:] if lines[i].startswith('    ')else '');i+=1
   out.append('<pre>'+html.escape('\n'.join(code))+'</pre>');continue
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
 figs=[('01_history_and_joint_spectrum','同剂量与完整边际仍不定义状态：时序不交换、能角相关性反例'),('02_bounds_and_optical_mass','有限率界可收缩状态支集；质量闭合下n增加而nh下降，均为合成条件例'),('03_output_specific_admission','观测、过程状态与新光学合同分别准入；资料齐备不等于执行或资格'),('04_source_ledger','原始实验、冻结项目链和本轮原创数值分账；YbF3不是YF3')]
 gallery=''.join(f'<figure><img src="figures/{n}.png" alt="{html.escape(c)}"><figcaption>{c} · <a href="figures/{n}.svg">SVG</a></figcaption></figure>'for n,c in figs)
 sources=json.loads((ROOT/'sources/source_registry.json').read_text())['sources'];shtml=''
 for s in sources:
  label=html.escape(s['source_id']+' · '+s['title']);label=f'<a href="{s["url"]}">{label}</a>'if s.get('url')else label
  shtml+='<li>'+label+'<br>'+html.escape(s['access_scope'])+'<br><small>'+html.escape(s['limitations'])+'</small></li>'
 refs=['data/gate_cases.json','verification/tiny_final.json','verification/unit_tests_final.txt','data/evidence_requests.json','data/legacy_binding.json','data/frozen_dependencies.json','reviews/NARROW_INDEPENDENT_CHECK.md','reviews/AUTHOR_ACCEPTANCE.md','stage_status.json','models/reader.py','models/driver.py','ROUND3_FINAL_HANDOFF.md'];rhtml=''.join(f'<li><a href="{p}">{p}</a></li>'for p in refs)
 style='''*{box-sizing:border-box}body{margin:0;background:#f2f5f8;color:#203448;font:17px/1.85 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}header{padding:50px max(5vw,24px);background:#244863;color:white}header h1{font-size:clamp(28px,4.8vw,46px);line-height:1.3;color:white}header p{max-width:980px}main{max-width:1220px;margin:auto;padding:28px 24px}nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:12px;background:white;padding:24px;border-radius:12px}nav a{font-size:14px}section{background:white;padding:clamp(20px,4vw,48px);margin:28px 0;border-radius:12px}h1,h2,h3{line-height:1.45;color:#244863}h1{font-size:29px}h2{font-size:23px;margin-top:32px}a{color:#107d7a;overflow-wrap:anywhere}p{margin:15px 0}small,figcaption{font-size:14px;color:#5b6d7e}figure{margin:26px 0}img{display:block;width:100%;height:auto}figcaption{margin:10px 0}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.65}td,th{border:1px solid #d5dde5;padding:10px 12px;text-align:left;vertical-align:top}th{background:#e6edf2}li{margin:14px 0}.notice{padding:20px 0;color:#70501e}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f6;padding:20px;border-radius:8px;font:14px/1.8 ui-monospace,monospace}footer{font-size:13px;color:#5b6d7e}@media print{body{background:white}header{background:white;color:black}header h1{color:black}nav{display:none}section{padding:10px 0}figure{break-inside:avoid}}'''
 content='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T10 离子状态证据准入</title><style>'+style+'</style></head><body><header><p>COATING RESEARCH · ROUND 3 · T10</p><h1>离子改变膜态以后，旧算子还能用吗？</h1><p>有记忆状态模型 · 联合能角反例 · 有限未知界 · 新state的条件准入</p><p>同剂量不是同状态，候选合同不是实际数据；真实n/k与密度继续留空</p></header><main><p class="notice">原创合成小模型与有限证据逻辑，无真实材料标定、生产资格或新光学执行。旧point12 partial、point2 conditional non-strict和formal pending保留。PNG实际像素检查；HTML布局unverified。</p><nav>'+''.join(toc)+'<a href="#figures">原创图</a><a href="#sources">来源账本</a><a href="#evidence">复现入口</a></nav><section id="figures"><h1>四张图看清本轮增量</h1>'+gallery+'</section>'+''.join(body)+'<section id="sources"><h1>原始来源与访问范围</h1><ul>'+shtml+'</ul></section><section id="evidence"><h1>证据与实现</h1><ul>'+rhtml+'</ul><p>核心不需要网络、浏览器或相邻目录。默认仅出计划；有意重现请用新工作副本保留冻结证据。</p></section><footer>Local freeze only · no upload / push / hardware / fourth-round execution</footer></main></body></html>'
 (ROOT/'reader.html').write_text(content)
if __name__=='__main__':figures();reader()
