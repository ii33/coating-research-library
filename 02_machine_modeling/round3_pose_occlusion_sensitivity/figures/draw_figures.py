"""Three original explanatory figures from bounded analytic examples only."""
from pathlib import Path
import sys,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties, fontManager
font_path='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fontManager.addfont(font_path)
font=FontProperties(fname=font_path)
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'models'))
from event_reference import Scene,evaluate,shadow_limits
plt.rcParams.update({'font.family':font.get_name(),'svg.fonttype':'path','font.size':10,'axes.unicode_minus':False,'figure.dpi':140,'savefig.dpi':160})
colors=['#176878','#ed9239','#6d4fad']
def save(fig,name):
 fig.savefig(R/'figures'/f'{name}.png',bbox_inches='tight',facecolor='white');fig.savefig(R/'figures'/f'{name}.svg',bbox_inches='tight',facecolor='white');plt.close(fig)
sc=Scene();r=evaluate(0.,sc)
fig,ax=plt.subplots(figsize=(10,5.6));ax.add_patch(Rectangle((-.08,.4),.16,.2,facecolor='#34485e',alpha=.85));ax.axhline(1,color='#899aab',ls='--');ax.scatter([0],[0],c=colors[1],s=80,zorder=5)
for x,c in [(-.2,colors[0]),(.2,colors[0]),(-.1333333,'#aaaaaa'),(.1333333,'#aaaaaa')]:ax.plot([0,x],[0,1],color=c,lw=2 if c==colors[0] else 1,ls='-' if c==colors[0] else ':')
ax.plot([-.37,.43],[1,1],color=colors[2],lw=3);ax.annotate('',xy=(.43,1.02),xytext=(.23,1.02),arrowprops={'arrowstyle':'->','color':colors[2],'lw':2});ax.text(.27,1.075,'v = 0.4 m/s',color=colors[2]);ax.text(0,-.07,'点源 (0, 0)',ha='center');ax.text(.18,.49,'有限厚板\nz = 0.4…0.6 m');ax.text(-.2,.9,'影边 −0.2 m',ha='right',color=colors[0]);ax.text(.2,.9,'影边 +0.2 m',ha='left',color=colors[0]);ax.text(-.38,.14,'源在板跨度内：近源面控制两侧影边\n灰点线仅表示远面投影，不能取板中面代替',bbox={'facecolor':'#f2f5f7','edgecolor':'none','pad':8})
ax.set(xlim=(-.5,.5),ylim=(-.13,1.16),xlabel='实验室横坐标 x / m',ylabel='高度 z / m',title='解析几何：正厚矩形实体的遮挡投影（合成条件）');ax.grid(alpha=.15);save(fig,'01_slab_event_geometry')
fig,axes=plt.subplots(1,2,figsize=(11,4.8),gridspec_kw={'width_ratios':[1.1,1]});labels=['工件横移','源横移','板横移','高度'];ids=[0,1,4,6];pos=np.arange(4);w=.24
for k,key,label in [(0,'smooth_gradient','光滑项'),(1,'event_gradient','事件项'),(2,'gradient','总导数')]:axes[0].bar(pos+(k-1)*w,[r[key][i] for i in ids],width=w,label=label,color=colors[k])
axes[0].axhline(0,c='#455',lw=.8);axes[0].set_xticks(pos,labels);axes[0].set_ylabel('导数 / (s/m^3)');axes[0].legend(loc='lower left',fontsize=9);axes[0].set_title('位置导数须加上边界时移项');axes[0].grid(axis='y',alpha=.15)
axes[1].bar(['光滑项','事件项','总导数'],[r[k][0] for k in ('smooth_gradient','event_gradient','gradient')],color=colors)
for i,k in enumerate(('smooth_gradient','event_gradient','gradient')):val=r[k][0];axes[1].text(i,val+(.03 if val>=0 else -.08),f'{val:+.4f}',ha='center')
axes[1].axhline(0,c='#455',lw=.8);axes[1].set_ylim(-.61,.86);axes[1].set_ylabel('工件横移导数 / (s/m^3)');axes[1].set_title('仅光滑项会把方向判反');axes[1].grid(axis='y',alpha=.15)
fig.suptitle('同一固定厚板例：t进入 = 0.425 s，t离开 = 1.425 s',fontsize=13);fig.tight_layout();save(fig,'02_sensitivity_decomposition')
fig,axes=plt.subplots(1,2,figsize=(11,4.6));p=np.linspace(-.01,.01,301);tau=2*np.sqrt(np.maximum(p,0));axes[0].plot(p,tau,c=colors[0],lw=2);axes[0].scatter([0],[0],c=colors[1],s=60);axes[0].annotate('相切点：普通导数不存在',xy=(0,0),xytext=(-.009,.09),arrowprops={'arrowstyle':'->'},fontsize=9);axes[0].set(xlabel='参数 p（本地无量纲例）',ylabel='遮挡时长（标准化）',title='g = t² − p：事件对的生灭');axes[0].grid(alpha=.15)
d=json.loads((R/'data/algebraic_results.json').read_text());fd=d['naive_finite_difference_counterexample'];eps=[x['step'] for x in fd];der=[x['fixed_grid_derivative'] for x in fd];axes[1].semilogx(eps,der,'o-',c=colors[2],label='16点固定网格中心差分');axes[1].axhline(-1,c=colors[1],ls='--',label='解析导数 −1');axes[1].set(xlabel='差分步长 ε',ylabel='积分导数',title='ε减小不修复硬遮挡欠采样',ylim=(-1.15,.2));axes[1].legend(fontsize=9);axes[1].grid(alpha=.15)
fig.suptitle('两类失败不同：真实不可微，与数值伪零梯度',fontsize=13);fig.tight_layout();save(fig,'03_grazing_and_fd_failure')
print('rendered 3 PNG and 3 SVG; visual inspection is a separate step')
