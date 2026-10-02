"""Original schematics and data figures. No imported third-party artwork."""
from pathlib import Path
import sys,csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'models'))
import dual_coverage as m
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
COL={'fixed':'#7b8594','drive':'#2675ad','output':'#c44d35','carrier':'#38826b'}

def save(fig,name):
    fig.savefig(P/'diagrams'/f'{name}.png',dpi=170,bbox_inches='tight')
    fig.savefig(P/'diagrams'/f'{name}.svg',bbox_inches='tight');plt.close(fig)

def circle(ax,xy,r,c,label=None,style='-'):
    ax.add_patch(Circle(xy,r,fill=False,color=c,lw=2,ls=style))
    if label: ax.text(*xy,label,ha='center',va='center',fontsize=9)

def arrows(ax,fromxy,toxy,c): ax.annotate('',toxy,fromxy,arrowprops={'arrowstyle':'->','color':c,'lw':2})

fig,axs=plt.subplots(1,3,figsize=(15,5.2))
ax=axs[0];circle(ax,(0,0),.24,COL['fixed'],'S fixed\n120')
circle(ax,(.312,0),.072,COL['output'],'P / W\n36');circle(ax,(0,0),.312,COL['carrier'],style=':')
ax.plot([0,.312],[0,0],c=COL['carrier'],lw=3,zorder=0);ax.text(.12,-.09,'Carrier C driven',c=COL['carrier'])
arrows(ax,(.38,.08),(.312,.12),COL['output']);ax.text(-.24,-.37,'External mesh: 120(S-C)+36(W-C)=0\nW/C = 13/3; pose period = 12 s',fontsize=9)
ax.set_title('D | Fixed sun, direct external mesh\nInherited conditional baseline')
ax=axs[1];ring=.64;B=np.array([.3397948717948718,.382992748153301]);W=np.array([.312,0.])
circle(ax,(0,0),ring,COL['fixed'],'')
circle(ax,(0,0),.352,COL['drive'],'Input 88\nupper plane',style='--')
circle(ax,B,.16,COL['drive'],style='--');circle(ax,B,.128,COL['carrier'],'A/B\n40/32')
circle(ax,W,.256,COL['output'],'Output W\n64')
ax.plot([0,B[0],W[0]],[0,B[1],W[1]],color=COL['carrier'],alpha=.7)
ax.text(-.65,-.78,'Ring 160 fixed | A and B share a shaft\nSolid: lower plane; dashed: upper plane\nW/C = 7/2; pose 8 s, modeled train 88 s',fontsize=9)
ax.set_title('C | Fixed ring + compound shaft\nText-grounded; source figure unverified',color='#795b22')
ax=axs[2];circle(ax,(0,0),.312,COL['carrier'],style=':');circle(ax,(.312,0),.06,COL['output'],'W')
ax.plot([0,.312],[0,0],color=COL['carrier'],lw=3);ax.scatter([0],[0],c=COL['drive'],s=50)
ax.annotate('independent carrier output\nphi(t)',xy=(0,0),xytext=(-.38,.2),arrowprops={'arrowstyle':'->'},fontsize=9)
ax.annotate('independent spindle output\npsi(t), absolute in L',xy=(.312,0),xytext=(-.15,-.18),arrowprops={'arrowstyle':'->'},fontsize=9)
ax.text(-.4,-.37,'Internal reduction: unknown, not invented\nC = 1/4 rps; W = -7/20 rps; pose 20 s',fontsize=9)
ax.set_title('I | Independent drive outputs\nText-grounded; source figure unverified',color='#795b22')
for j,ax in enumerate(axs):
    ax.set_aspect('equal');ax.set_xlabel('x in L [m]');ax.set_ylabel('y in L [m]');ax.grid(alpha=.15)
    lim=.86 if j==1 else .46;ax.set_xlim(-lim,lim);ax.set_ylim(-lim,lim)
fig.suptitle('ORIGINAL SYNTHETIC SCHEMATICS | Pitch circles, not tooth or manufacturing drawings',y=1.04,weight='bold')
fig.tight_layout();save(fig,'01_topology_schematics')

fig,(ax,timeline)=plt.subplots(2,1,figsize=(12,7),gridspec_kw={'height_ratios':[4,1]})
sv=np.array([.2,0]);work=np.array([.28,.6]);ion_entry=work-np.array([.8,.6])*1
ax.plot([sv[0],work[0]],[sv[1],work[1]],color='#c87921',lw=2,label='vapor ray (point source)')
ax.plot([ion_entry[0],work[0]],[ion_entry[1],work[1]],color='#6a5ca8',lw=2,label='ion ray (parallel beam)')
ax.plot([.175,.245],[.2,.2],lw=8,color='#c87921',label='V plate, chamber-fixed')
ax.plot([-.49,-.37],[.1,.1],lw=8,color='#6a5ca8',label='I plate, chamber-fixed')
ax.plot([.22,.34],[.6,.6],lw=5,color=COL['output']);arrows(ax,(.28,.59),(.28,.49),COL['output'])
ax.scatter([sv[0],-.62],[0,0],s=90,c=['#c87921','#6a5ca8']);arrows(ax,(.2,.01),(.2,.1),'#c87921');arrows(ax,(-.62,0),(-.5,.09),'#6a5ca8')
ax.text(.34,.57,'W: outward normal n = -z\nRay endpoint shown at x=.28 m',fontsize=9)
ax.text(-.65,.46,'All source / plate / probe frames -> L\nIndependent visibility for each channel\nOrdinary opaque plates; selectivity by path\ny positions/widths remain in JSON',bbox={'facecolor':'white','alpha':.85,'edgecolor':'#bbb'})
ax.scatter([.25,.18],[.64,.66],marker='D',s=45,c='#555');ax.text(.01,.73,'QCM_A and cup_B: fixed diagnostic poses\n(symbols offset vertically for readability; actual z=.60 m)',fontsize=9)
ax.set_xlim(-.72,.76);ax.set_ylim(-.05,.86);ax.set_xlabel('x in L [m]');ax.set_ylabel('z in L [m]');ax.grid(alpha=.15);ax.legend(loc='lower right',fontsize=9)
ax.set_title('Original common-frame schematic | V and I plates are separate test cases, not a fabrication layout',weight='bold')
timeline.broken_barh([(.55,6.)],(1,0.6),facecolors='#c87921');timeline.broken_barh([(0,7.3)],(0,.6),facecolors='#6a5ca8')
timeline.set_xlim(0,7.3);timeline.set_yticks([.3,1.3],['Ion on','Vapor on']);timeline.set_xlabel('Common synthetic time [s]');timeline.set_xticks([0,.55,1.3,6.55,7.3]);timeline.grid(axis='x',alpha=.2)
fig.tight_layout();save(fig,'02_frames_and_clock')

rows=list(csv.DictReader((P/'data/map_D.csv').open()))
fig,axs=plt.subplots(3,3,figsize=(11,10));summary=json.loads((P/'data/main_summary.json').read_text())['D']
for a,case in enumerate(['none','vapor_only','ion_only']):
    r=[x for x in rows if x['case']==case and float(x['area_weight'])>0]
    for b,(key,label) in enumerate([('h_nm','Thickness'),('ion_fluence_m2','Ion fluence'),('ion_to_net_atom_ratio','Ion / net-atom ratio')]):
        ax=axs[a,b];z=np.array([float(x[key]) for x in r])/summary[case][key]['mean']
        im=ax.scatter([float(x['u_m'])*1e3 for x in r],[float(x['v_m'])*1e3 for x in r],c=z,s=11,cmap='coolwarm',vmin=.8,vmax=1.2)
        ax.set_aspect('equal');ax.set_xlim(-63,63);ax.set_ylim(-63,63);ax.set_xlabel('u [mm]');ax.set_ylabel('v [mm]')
        ax.set_title(f"{case} | {label}\nCV = {summary[case][key]['cv']*100:.3f}%",fontsize=10)
fig.subplots_adjust(top=.86,hspace=.6,wspace=.5,right=.87);cax=fig.add_axes([.91,.25,.017,.5]);fig.colorbar(im,cax=cax,label='Local value / own area mean',extend='both')
fig.suptitle('D | Separate thickness, ion fluence and ratio maps\nSynthetic 7.3 s layer; normalized maps do not compare absolute dose',weight='bold');save(fig,'03_dual_coverage_maps')

s=json.loads((P/'data/main_summary.json').read_text());fig,ax=plt.subplots(figsize=(9,4.5));x=np.arange(3);width=.23
for j,(key,label,color) in enumerate([('h_nm','Thickness CV','#c87921'),('ion_fluence_m2','Ion fluence CV','#6a5ca8'),('ion_to_net_atom_ratio','Ion/net-atom ratio CV','#368877')]):
    bars=ax.bar(x+(j-1)*width,[s[t]['none'][key]['cv']*100 for t in ['D','C','I']],width,label=label,color=color)
    ax.bar_label(bars,fmt='%.3f',padding=3,fontsize=9)
ax.set_xticks(x,['D: direct mesh','C: conditional compound','I: conditional independent']);ax.set_ylabel('Area coefficient of variation [%]');ax.set_ylim(0,5.7);ax.legend(ncol=3,loc='upper center');ax.grid(axis='y',alpha=.15)
ax.set_title('Same sources, layer window and geometry; only motion changes\nI -> D: thickness CV improves, ion fluence CV worsens',weight='bold');fig.tight_layout();save(fig,'04_non_equivalence')
