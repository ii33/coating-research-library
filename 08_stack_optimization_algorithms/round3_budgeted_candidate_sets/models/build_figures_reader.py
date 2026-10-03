"""Original static figures from saved evidence. No optical evaluation or browser."""
from pathlib import Path
import json,html,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'#f6f8fb','figure.facecolor':'#f6f8fb','axes.facecolor':'white'})
C={'OUT':'#c7d0db','IN':'#16877b','UNKNOWN':'#efa544'}
def save(fig,name):
 fig.savefig(ROOT/'figures'/f'{name}.png',dpi=160,bbox_inches='tight');fig.savefig(ROOT/'figures'/f'{name}.svg',bbox_inches='tight');plt.close(fig)
def block(ax,x,y,w,h,title,text,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.014',facecolor=color,edgecolor='none'))
 ax.text(x+.018,y+h-.034,title,weight='bold',va='top',fontsize=12);ax.text(x+.018,y+h-.092,text,va='top',fontsize=10,linespacing=1.5)
def figures():
 fig,ax=plt.subplots(figsize=(12,6));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');fig.suptitle('Evidence has a direction',fontsize=20,weight='bold',x=.12,ha='left')
 block(ax,.025,.56,.27,.33,'T05 / T06 source chain','Full forward + response\nLambert normalization + guards\nZ is an outer envelope', '#dbe9f5')
 block(ax,.365,.56,.27,.33,'T07 observation contract','One specimen, shared z\nM0: 3 nodes; M1: 10 um\nFixed synthetic material state','#dceee9')
 block(ax,.705,.56,.27,.33,'T08 candidate cover','Two coordinates: (z, v6)\nOUT / IN / UNKNOWN\nBounded, charged subdivision','#ffe9c7')
 for a,b in [(.30,.36),(.64,.70)]:ax.annotate('',xy=(b,.73),xytext=(a,.73),arrowprops={'arrowstyle':'->','lw':2,'color':'#46556b'})
 block(ax,.025,.11,.44,.30,'Permitted conclusion','A complete OUT cover excludes all subsets\nof that encoded domain under this contract.', '#e4e9ee')
 block(ax,.525,.11,.45,.30,'Unproved reverse direction','An IN box / point does not establish\na joint Q / density / retention realization.','#f7dfde')
 ax.text(.03,.015,'No measured n/k inferred | no production release | formal model chain pending',fontsize=10,color='#46556b');save(fig,'01_contract_and_implications')
 runs=[json.loads((ROOT/'verification/tiny_final'/p).read_text()) for p in ['plane_M0_63.json','plane_joint_255.json']]
 fig,axes=plt.subplots(1,2,figsize=(13,5.8),sharex=True,sharey=True)
 for ax,r,label in zip(axes,runs,['M0 only | 63 evaluated nodes','M0 + M1 | 255 evaluated nodes']):
  for row in r['leaves']:
   z,v=row['box'];ax.add_patch(Rectangle((v[0],z[0]),v[1]-v[0],z[1]-z[0],facecolor=C[row['data_class']],edgecolor='#ffffff',lw=.35))
  ax.plot([1],[1],marker='*',color='#166358',markersize=13,label='Validated proxy point')
  ax.set(xlim=(.9,1.1),ylim=(.985856,1.014144),xlabel='Outer-layer multiplier v6',title=label);ax.ticklabel_format(axis='y',style='plain',useOffset=False)
  ax.text(.01,.97,f"OUT {r['counts']['OUT']} | IN {r['counts']['IN']} | UNKNOWN {r['counts']['UNKNOWN']}",transform=ax.transAxes,va='top',fontsize=9,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
 axes[0].set_ylabel('Shared latent thickness ratio z');handles=[Rectangle((0,0),1,1,color=C[c],label=c) for c in C];handles.append(Line2D([0],[0],marker='*',color='none',markerfacecolor='#166358',markersize=12,label='Proxy witness'))
 fig.legend(handles=handles,loc='lower center',ncol=4,bbox_to_anchor=(.5,.035));fig.suptitle('Unprocessed boxes remain in the cover',fontsize=19,weight='bold');fig.text(.5,.015,'Unequal budgets: this is not a matched information-gain benchmark. Depth-first ordering is visible.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.09,1,.93));save(fig,'02_budgeted_cover')
 r=runs[1];fig,axes=plt.subplots(1,2,figsize=(12,5.6),gridspec_kw={'width_ratios':[1.05,1]})
 xs=[.9+i*.2/400 for i in range(401)];ys=[((x-1.05)/.05)**2 for x in xs]
 axes[0].plot(xs,ys,color='#24465f',lw=2,label='Declared J(v)');axes[0].axhline(1,color='#16877b',ls='--',label='Verified proxy U ~ 1');axes[0].axhline(0,color='#efa544',ls=':',lw=3,label='Relaxation L = 0');axes[0].plot([1],[1],'*',color='#16877b',markersize=13)
 axes[0].set(xlabel='Outer-layer multiplier v6',ylabel='Dimensionless objective',title='UNKNOWN contributes to the lower bound',ylim=(-.35,9.4));axes[0].legend(loc='upper right',fontsize=9)
 ax=axes[1];ax.axis('off');ax.set(xlim=(0,1),ylim=(0,1));block(ax,.02,.67,.96,.27,'98 OUT leaves','Observation evidence excludes these boxes.', '#e4e9ee');block(ax,.02,.36,.96,.27,'32 UNKNOWN leaves','All 32 enter the relaxation lower bound.\n15 may be worse than the current witness.', '#ffe9c7');block(ax,.02,.05,.96,.27,'17 retained for optimum','Objective pruning leaves data_class intact.\nNo global optimum / source-realization claim.', '#dceee9');fig.suptitle('An objective bound is not a data-exclusion label',fontsize=18,weight='bold');fig.tight_layout(rect=(0,0,1,.92));save(fig,'03_objective_and_semantics')

def inline(s):
 s=html.escape(s)
 s=re.sub(r'\[(BS-S\d+)\]',r'<a href="#\1">[\1]</a>',s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 return s

def md(text):
 out=[];para=[];inlist=False
 def flush():
  if para:out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
 for line in text.splitlines()+['']:
  if line.startswith('#'):
   flush()
   if inlist:out.append('</ul>');inlist=False
   h=min(len(line)-len(line.lstrip('#')),4);out.append(f'<h{h}>'+inline(line.lstrip('# ').strip())+f'</h{h}>')
  elif line.startswith('- ') or re.match(r'^\d+\. ',line):
   flush()
   if not inlist:out.append('<ul>');inlist=True
   out.append('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',line))+'</li>')
  elif not line.strip():
   flush()
   if inlist:out.append('</ul>');inlist=False
  else:para.append(line)
 return '\n'.join(out)

def reader():
 reports=sorted((ROOT/'reports').glob('*.md'));sources=json.loads((ROOT/'sources/source_registry.json').read_text());toc=[];body=[]
 for i,p in enumerate(reports,1):
  anchor=f'chapter-{i}';title=p.read_text().splitlines()[0].lstrip('# ');toc.append(f'<a href="#{anchor}">{html.escape(title)}</a>');body.append(f'<section id="{anchor}">'+md(p.read_text())+f'<p class="download"><a href="reports/{p.name}">原始 Markdown</a></p></section>')
 figures=[('01_contract_and_implications','来源外包络的排除蕴含是单向的；IN/见证不证明联合来源可实现'),('02_budgeted_cover','原创二维覆盖图：灰=OUT、橙=UNKNOWN、星=代理见证；不同预算不能作等预算信息增益比较'),('03_objective_and_semantics','原创目标界与三分语义图：15个UNKNOWN仅作最优性剪枝，不能改写数据分类')]
 gallery=''.join(f'<figure><img src="figures/{n}.png" alt="{html.escape(cap)}"><figcaption>{html.escape(cap)} · <a href="figures/{n}.svg">SVG</a></figcaption></figure>' for n,cap in figures)
 sourcehtml=''.join(f'<li id="{q["id"]}"><b>{q["id"]}</b> · <a href="{html.escape(q["url"],quote=True)}">{html.escape(q["title"])}</a><br>{html.escape(q["read_extent"])}<br><small>{html.escape(q["used_for"])}</small></li>' for q in sources)
 evidence=['data/candidate_contract.json','data/frozen_dependencies.json','verification/tiny_final/summary.json','verification/unit_tests.txt','reviews/narrow_independent_check.md','verification/narrow_independent_check.json','T09_ROUND3_HANDOFF.md','models/reader.py','sources/RIGHTS_AND_ACCESS.md']
 evidencehtml=''.join(f'<li><a href="{p}">{p}</a></li>' for p in evidence)
 text='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T08 · 预算化候选集合</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f5f8;color:#203345;font:17px/1.85 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}header{padding:54px max(5vw,24px);background:#18384b;color:#fff}header h1{font-size:clamp(28px,5vw,48px);line-height:1.25;margin:8px 0 20px}.eyebrow{letter-spacing:2px;color:#a5d9d1;font-size:13px}main{max-width:1160px;margin:auto;padding:32px 24px}nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:9px;padding:24px;background:white;border-radius:14px}nav a{font-size:14px}section{background:white;padding:clamp(22px,5vw,55px);border-radius:16px;margin:28px 0}h1,h2,h3{line-height:1.4;color:#173c52}header h1{color:white}h1{font-size:29px}h2{font-size:22px;margin-top:30px}p{margin:14px 0}a{color:#087b77;overflow-wrap:anywhere}figure{margin:26px 0;background:white;padding:14px;border-radius:14px}img{width:100%;height:auto;display:block}figcaption{font-size:14px;color:#53697b;margin:10px}code{background:#edf3f6;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}.notice{background:#fff0cf;border-left:5px solid #d89127;padding:20px 25px;border-radius:8px;margin:24px 0}.stat{font-size:18px}.download,small{font-size:13px;color:#607382}li{margin:8px 0}footer{font-size:13px;color:#607382;margin:25px 0}@media print{body{background:white}header{background:white;color:black}header h1{color:black}section{padding:12px 0;break-inside:auto}nav{display:none}figure{break-inside:avoid}}
</style></head><body><header><div class="eyebrow">COATING RESEARCH · ROUND 3 · T08</div><h1>预算结束后，保留什么？</h1><p>二维候选集合 · 排除证据 · 未决盒 · 有限搜索失败</p><div class="stat">331节点 / 1166包含调用 · 30项窄测试 · 一次窄独核</div></header><main><div class="notice">合成六层膜系，冻结两通道。OUT只来自观测包含证据，UNKNOWN不因预算耗尽消失。IN/见证仍不证明真实来源实现。正式模型链pending；HTML布局unverified，PNG逐张检查。</div><nav>'''+''.join(toc)+'''<a href="#figures">原创图</a><a href="#sources">一手来源</a><a href="#evidence">复现与证据</a></nav><section id="figures"><h1>原创图与证据边界</h1>'''+gallery+'''</section>'''+''.join(body)+'''<section id="sources"><h1>一手来源与使用范围</h1><ul>'''+sourcehtml+'''</ul></section><section id="evidence"><h1>复现与证据</h1><ul>'''+evidencehtml+'''</ul><p>解压后运行 python models/reader.py --directory .；数值/验证只需Python标准库。没有外部图片、字体、脚本或网络运行依赖。</p></section><footer>Local freeze only · no upload / push / next-stage execution · 原文PDF不在本reader包内</footer></main></body></html>'''
 (ROOT/'reader.html').write_text(text,encoding='utf-8')
if __name__=='__main__':figures();reader()
