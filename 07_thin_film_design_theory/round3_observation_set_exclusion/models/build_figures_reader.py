"""Original static figures and self-contained HTML; curves are illustrative only."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t07-r3-mpl')
from set_exclusion import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch,Patch
from html import escape
import re
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'t07-r3-original'})
C=['#176b9a','#c75026','#7961a8'];R=ROOT

def save(fig,name):
 fig.savefig(R/'figures'/f'{name}.svg',bbox_inches='tight');fig.savefig(R/'figures'/f'{name}.png',dpi=155,bbox_inches='tight');plt.close(fig)
def figures():
 c=load_case();r=json.loads((R/'verification/tiny_results.json').read_text());Z=z_domain(c).floats();zs=[Z[0]+(Z[1]-Z[0])*i/32 for i in range(33)];hyps=c['parameterization']['hypotheses'];chs=c['derived_observation_contract']['channels'];y=list(map(float,c['derived_observation_contract']['measurement_centers_R']));e=.001
 fig,ax=plt.subplots(1,2,figsize=(12.4,4.8));fig.suptitle('A new observation excludes one candidate, while a product alias remains',fontsize=15,y=1.02)
 for j,h in enumerate(hyps):
  m0=[scalar_observation(c,h,z,chs[0]) for z in zs];m1=[scalar_observation(c,h,z,chs[1]) for z in zs];style='--' if j==2 else '-'
  ax[0].plot(zs,m0,style,color=C[j],lw=2,label=h['id']);ax[1].plot(m0,m1,style,color=C[j],lw=2,label=h['id'])
 ax[0].axhspan(y[0]-e,y[0]+e,color='#239a82',alpha=.17,label='M0 data interval');ax[0].set(xlabel='shared latent z (dimensionless)',ylabel='M0: weighted power reflectance',title='Old M0 permits a compensating z')
 ax[0].legend(loc='upper left',fontsize=8)
 ax[1].add_patch(Rectangle((y[0]-e,y[1]-e),2*e,2*e,facecolor='#239a82',edgecolor='#146855',alpha=.4,label='joint data box'))
 ax[1].scatter([y[0]],[y[1]],c='black',s=23,zorder=4)
 ax[1].set(xlabel='M0: weighted power reflectance',ylabel='M1: R at 10 micrometers',title='Joint readout separates the outer-layer candidate');ax[1].legend(loc='upper right',fontsize=8)
 for a in ax:a.grid(alpha=.18)
 fig.text(.02,-.02,'33 scalar points per curve: illustration only. Exclusion uses exact interval leaves, not sampled curves.',fontsize=10,color='#555');fig.tight_layout();save(fig,'01_observation_geometry')
 fig,ax=plt.subplots(figsize=(12.2,5.0));palette={'OUT':'#d8e0e6','IN':'#218e78','UNKNOWN':'#d99626'}
 for j,run in enumerate(r['runs']):
  for leaf in run['leaves']:
   a,b=leaf['z'];ax.broken_barh([(a,b-a)],(5-j-.32,.64),facecolors=palette[leaf['class']],edgecolors='none')
  ax.text(Z[1]+.0007,5-j, f"OUT {run['counts']['OUT']}  IN {run['counts']['IN']}  ? {run['counts']['UNKNOWN']}",va='center',fontsize=9)
 labels=[q['hypothesis']+' | '+' + '.join(q['channels']) for q in r['runs']]
 ax.set_yticks(range(6));ax.set_yticklabels(list(reversed(labels)),fontsize=9);ax.set_xlim(Z[0]-.0005,Z[1]+.012);ax.set_ylim(-.65,5.8);ax.set_xlabel('shared latent z (dimensionless)');ax.set_title('All terminal boxes are retained: excluded, feasible, or unresolved')
 handles=[Patch(facecolor=palette[state],label={'OUT':'OUT: rejected','IN':'IN: whole box feasible','UNKNOWN':'UNKNOWN: unresolved boundary'}[state]) for state in ['OUT','IN','UNKNOWN']]
 ax.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,-.16),ncol=3,fontsize=9);ax.grid(axis='x',alpha=.18);fig.text(.01,-.025,'Inner/outer sets concern the relaxed synthetic z model. A feasible z need not be an attained upstream source realization.',fontsize=10,color='#555');fig.tight_layout();save(fig,'02_bounded_set_classification')
 fig,ax=plt.subplots(figsize=(12.5,6.6));ax.set_xlim(0,12.5);ax.set_ylim(0,6.6);ax.axis('off')
 def box(x,y,w,h,text,color='#eef3f7'):
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.10',facecolor=color,edgecolor='#60788c',lw=1));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11)
 def arrow(x,y,x2,y2):ax.annotate('',xy=(x2,y2),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#536c80','lw':1.6})
 box(.2,4.6,2.7,1.1,'Frozen finite Lambert\nsource + full response\nQ / density remain aliased');box(3.35,4.6,2.3,1.1,'Positive h enclosure\nz = h / h_ref\nnot a source witness');box(6.1,4.6,2.4,1.1,'One shared z\nall six layers\nsame specimen');box(9,4.6,3.1,1.1,'M0 unchanged: 3 nodes\nM1 derived: 10 um\nfixed synthetic n, k = 0')
 arrow(2.95,5.15,3.2,5.15);arrow(5.8,5.15,5.95,5.15);arrow(8.65,5.15,8.85,5.15)
 box(.2,2.5,5.0,1.25,'Fail closed: negative / crossing-zero / near-zero\ninsufficient inventory / unknown material state\nunsupported source or measurement operator','#fff2e6')
 box(5.75,2.5,6.35,1.25,'Cover Z by bounded subdivision\nOUT: any channel disjoint from readout\nIN: all enclosures inside | otherwise UNKNOWN','#e7f3ef');arrow(10.55,4.45,10.55,3.9)
 box(.2,.35,5.0,1.3,'Exact alias in the relaxed thickness model\nv = 501/500, z = 500/501 => v z = 1\nall layers identical to H0 at z = 1','#f1ebf7')
 box(5.75,.35,6.35,1.3,'Set exclusion is not parameter uniqueness\nOuter overlap is not a feasible intersection\nLocal slope is not a global certificate','#f0f3f5');arrow(8.8,2.35,8.8,1.8)
 ax.text(.2,6.18,'Contract chain and logical boundaries',fontsize=17,weight='bold');save(fig,'03_contract_and_alias')

def md(text):
 out=[];para=[];code=False;block=[]
 def inline(s):
  s=escape(s);s=re.sub(r'\[SE-S(\d+)\]',r'<a href="#SE-S\1">[SE-S\1]</a>',s);s=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s);return s
 def flush():
  if para:out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
 for line in text.splitlines():
  if line.startswith('```'):
   flush()
   if code:out.append('<pre>'+escape('\n'.join(block))+'</pre>');block=[]
   code=not code;continue
  if code:block.append(line);continue
  if line.startswith('#'):
   flush();num=len(line)-len(line.lstrip('#'));out.append(f'<h{min(num+1,5)}>'+inline(line.lstrip('#').strip())+f'</h{min(num+1,5)}>')
  elif not line.strip():flush()
  else:para.append(line)
 flush();return '\n'.join(out)
def reader():
 reports=sorted((R/'reports').glob('*.md'));sources=json.loads((R/'sources/source_registry.json').read_text());parts=[]
 for i,p in enumerate(reports):parts.append(f'<section id="r{i+1}">'+md(p.read_text())+'</section>')
 links=''.join(f'<li><a href="#r{i+1}">{escape(p.stem.replace("_"," "))}</a> · <a href="reports/{p.name}">Markdown</a></li>' for i,p in enumerate(reports))
 figs=''.join(f'<figure><img src="figures/{p.name}" alt="{escape(p.stem.replace("_"," "))}"><figcaption>{escape(p.stem.replace("_"," "))} · 原创图，曲线为示意，精确判定见JSON叶证书 · <a href="figures/{p.stem}.svg">SVG</a></figcaption></figure>' for p in sorted((R/'figures').glob('*.png')))
 src=''.join(f'<li id="{s["id"]}"><a href="{escape(s["url"])}">{escape(s["title"])}</a>：{escape(s["used_for"])}；{escape(s["access"])}</li>' for s in sources)
 files=['README.md','data/case.json','data/frozen_dependencies.json','verification/tiny_results.json','verification/unit_tests.txt','verification/batch_plan_receipt.json','reviews/narrow_optical_unit_check.md','models/set_exclusion.py','models/run_tiny.py','models/reader.py','models/validation_driver.py','tests/test_reference.py','T08_ROUND3_HANDOFF.md']
 fl=''.join(f'<li><a href="{p}">{p}</a></li>' for p in files)
 html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T07R3 · 有限观测集合排除</title><style>body{margin:0;background:#edf1f4;color:#193044;font:17px/1.8 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:42px 28px;background:white}h1,h2,h3{line-height:1.35;color:#123a57}h1{font-size:2.3em}h2{margin-top:2em}h3{margin-top:1.8em}p{max-width:90ch}a{color:#08688d;overflow-wrap:anywhere}nav,.notice{background:#eef6f7;padding:18px 24px;border-radius:8px}figure{margin:36px 0}img{display:block;max-width:100%;height:auto}figcaption{font-size:.86em;color:#536372}section{margin-top:50px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f8;padding:18px;font-size:14px}li{margin:.4em 0}.tag{color:#775017}@media(max-width:650px){main{padding:24px 16px}body{font-size:16px}h1{font-size:1.8em}}</style></head><body><main>'''
 html+='<h1>有限观测能排除哪些候选？</h1><p>T07 · 第三轮工程研究手册 · local freeze · 2026-10-02</p><div class="notice"><strong>主要结果：</strong>原M0可容纳“最外层+10%”；加入派生10 μm观测后整个先验z域排除该候选。全层×1.002仍与公共z构成精确乘积别名。<br>仅固定同状态合成模型。point12 partial；point2 conditional non-strict；正式模型链pending；heavy/device未执行。<br><span class="tag">PNG已查看；HTML静态链接已检，实际浏览器布局未验证。</span></div><nav><ol>'+links+'</ol><a href="#figures">原创图</a> · <a href="#sources">一手来源</a> · <a href="#files">离线复算文件</a></nav>'
 html+='<section id="figures"><h2>原创图</h2>'+figs+'</section>'+''.join(parts)+'<section id="sources"><h2>一手来源及使用边界</h2><ul>'+src+'</ul><p>原文单独本地保存，不入reader载荷。报告与图均为原创，来源不提供真实膜常数认证。</p></section><section id="files"><h2>离线复算文件</h2><ul>'+fl+'</ul></section></main></body></html>'
 (R/'reader.html').write_text(html)
if __name__=='__main__':figures();reader();print('three PNG/SVG figures and offline reader built; HTML layout unverified')
