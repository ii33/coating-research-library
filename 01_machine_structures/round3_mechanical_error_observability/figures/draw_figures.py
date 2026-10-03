"""Original diagrams from this package's equations and synthetic algebra."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
import numpy as np
R=Path(__file__).resolve().parents[1]
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':10,'svg.fonttype':'path'})

def save(fig,name):
    fig.savefig(R/'figures'/f'{name}.png',dpi=160,bbox_inches='tight')
    fig.savefig(R/'figures'/f'{name}.svg',bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(12,5));ax.set(xlim=(0,12),ylim=(0,5));ax.axis('off')
boxes=[(0.2,3.2,'理想机械链\n拓扑、齿比、参考轴'),(3.3,3.2,'误差位姿\n平移＋倾斜＋自转'),(6.4,3.2,'真实工件状态\nx(t,u) 与 n(t,u)'),(9.5,3.2,'沉积响应\n源、遮挡、层时序'),(6.4,.5,'测量算子\n编码器、图像、位移'),(9.5,.5,'观测数据\n角度、像素、厚度')]
for x,y,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),2.15,1.1,boxstyle='round,pad=.08',facecolor='#edf3f8',edgecolor='#34506a'))
    ax.text(x+1.075,y+.55,label,ha='center',va='center',fontproperties=font,fontsize=12)
for start,end in [((2.43,3.75),(3.2,3.75)),((5.53,3.75),(6.3,3.75)),((8.63,3.75),(9.4,3.75)),((7.45,3.1),(7.45,1.75)),((8.63,1.05),(9.4,1.05)),((10.55,3.1),(10.55,1.75))]:
    ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':'#34506a','lw':1.5})
ax.text(.2,2.15,'不能用传感器读数\n直接替代真实位姿',fontproperties=font,fontsize=12,color='#93431c')
ax.text(.2,.55,'独立误差入口：\n时钟、标尺、零点、目标形状',fontproperties=font,fontsize=12)
ax.set_title('图1 机械状态与仪器观测分层  原创结构示意',fontproperties=font,fontsize=16,pad=12)
save(fig,'01_state_and_observation')

r=json.loads((R/'data/algebraic_results.json').read_text())['results']
keys=['height_source_only','height_plus_probe','clock_constant','clock_varying','axial_collinear','axial_noncollinear']
labels=['厚度＋自由源幅度','加独立高度读数','恒速角度与时钟','已知变速的条件例','共线三高度点','非共线三高度点']
fig,ax=plt.subplots(figsize=(11,5));y=np.arange(6);pars=[r[k]['parameters'] for k in keys];ranks=[r[k]['rank'] for k in keys]
ax.barh(y,pars,color='#e0e7ee',label='机械参数列数');ax.barh(y,ranks,color='#397b98',label='去干扰后数值秩')
ax.set_yticks(y,labels,fontproperties=font);ax.invert_yaxis();ax.set_xticks(range(4));ax.set_xlim(0,3.65)
for i,(a,b) in enumerate(zip(ranks,pars)):ax.text(b+.07,i,f'{a}/{b}',va='center')
ax.set_xlabel('指定局部合成模型的秩；不表示实机精度',fontproperties=font);ax.set_title('图2 增加独立信息才解除混淆',fontproperties=font,fontsize=16);ax.legend(prop=font,loc='upper left',bbox_to_anchor=(0,-.18),ncol=2);ax.spines[['top','right']].set_visible(False)
save(fig,'02_conditional_ranks')

fig,axs=plt.subplots(1,2,figsize=(11,4.7));b=r['backlash'];x=b['input_rad'];y=b['output_rad'];axs[0].plot(x,y,'o-',color='#397b98',label='有记忆的输出');axs[0].plot([0,.4],[0,.4],'--',color='#888',label='无隙参考')
for i,(xx,yy) in enumerate(zip(x,y)):axs[0].annotate(str(i),(xx,yy),xytext=(5,4),textcoords='offset points')
axs[0].set(xlabel='理想输出角 rad',ylabel='实际play输出角 rad',title='合成半宽 b=0.1 rad；序号是时间顺序');axs[0].legend(prop=font);axs[0].grid(alpha=.2)
vals=[r['independent_noise_mean']['noise_conditional_covariance'][0][0],r['common_noise_mean']['noise_conditional_covariance'][0][0]]
axs[1].bar(['独立噪声','共同相关 ρ=0.8'],vals,color=['#397b98','#b16941']);axs[1].set_ylim(0,1);axs[1].set_ylabel('均值方差 / 单次观测方差',fontproperties=font);axs[1].set_title('四次观测；共同误差不会按1/N消失',fontproperties=font)
for i,v in enumerate(vals):axs[1].text(i,v+.02,f'{v:.2f}',ha='center')
for ax in axs:
    for t in [ax.xaxis.label,ax.yaxis.label,ax.title,*ax.get_xticklabels()]:t.set_fontproperties(font)
    ax.spines[['top','right']].set_visible(False)
fig.suptitle('图3 记忆与相关性不能当独立随机扰动  纯合成反例',fontproperties=font,fontsize=15);fig.tight_layout();save(fig,'03_memory_and_correlation')
