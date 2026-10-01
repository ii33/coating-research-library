"""Original explanatory diagrams. Not a vendor drawing or dimensioned CAD."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t01_mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
from pathlib import Path
from math import sin,cos,pi
B=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
BLUE='#17628b';RED='#b94832';GRAY='#616b72'
def arc_arrow(ax,c,r,a0,a1,col=BLUE):
 pts=[a0+(a1-a0)*i/90 for i in range(91)]
 xs=[c[0]+r*cos(x*pi/180) for x in pts];ys=[c[1]+r*sin(x*pi/180) for x in pts]
 ax.plot(xs,ys,c=col,lw=1.8)
 ax.annotate('',xy=(xs[-1],ys[-1]),xytext=(xs[-5],ys[-5]),arrowprops={'arrowstyle':'->','color':col,'lw':1.8})
def save(fig,name):
 fig.savefig(B/(name+'.svg'),bbox_inches='tight',facecolor='white')
 fig.savefig(B/(name+'.png'),bbox_inches='tight',facecolor='white',dpi=180)
 plt.close(fig)
fig,ax=plt.subplots(figsize=(9,7));ax.set_aspect('equal');ax.axis('off');ax.set_xlim(-1.65,2.05);ax.set_ylim(-1.65,1.5)
ax.set_title('A  Direct external sun-planet mesh',loc='left',fontweight='bold',pad=20)
a=35*pi/180;P=(cos(a),sin(a));rs=.75;rp=.25
ax.add_patch(Circle((0,0),1,fill=False,ls='--',lw=1,color='#afbdc6'))
ax.add_patch(Circle((0,0),rs,facecolor='#eef0f2',edgecolor=GRAY,lw=2))
ax.add_patch(Circle(P,rp,facecolor='#d7eaf5',edgecolor=BLUE,lw=2))
ax.plot([0,P[0]],[0,P[1]],color=BLUE,lw=4,zorder=1)
ax.plot([0,P[0]],[0,P[1]],'o',c=BLUE,ms=5)
ax.annotate('',xy=(1.62,0),xytext=(0,0),arrowprops={'arrowstyle':'->','color':'black'})
ax.annotate('',xy=(0,1.25),xytext=(0,0),arrowprops={'arrowstyle':'->','color':'black'})
ax.text(1.66,0,'+x',va='center');ax.text(0,1.32,'+y',ha='center');ax.text(-.12,-.13,'O',ha='right')
ax.text(-.42,.22,'S fixed\nexternal sun',ha='center',fontsize=10)
ax.text(P[0]+.34,P[1]+.15,'P planet gear\nworkpiece rigidly coupled',va='center')
ax.annotate('C carrier / R',xy=(.61,.427),xytext=(1.2,-.5),color=BLUE,arrowprops={'arrowstyle':'->','color':BLUE},ha='center')
arc_arrow(ax,P,.15,10,300);ax.text(P[0]+.36,P[1]-.32,'+spin\n(absolute)',color=BLUE,ha='left')
arc_arrow(ax,(0,0),1.29,165,265);ax.text(-1.16,-1.18,'+revolution',color=BLUE)
arc_arrow(ax,(0,0),.37,0,35,'black');ax.text(.41,.06,'theta_c',fontsize=9)
ax.text(-1.5,-1.5,'View from +z toward -z. CCW is positive.\nCircles are pitch circles, not tooth profiles. No ring gear in this topology.',fontsize=10)
save(fig,'A_direct_mesh_coordinates')
fig,ax=plt.subplots(figsize=(9,7));ax.set_aspect('equal');ax.axis('off');ax.set_xlim(-2.1,2.3);ax.set_ylim(-.35,3.5)
ax.set_title('B  Source-mask-workpiece path',loc='left',fontweight='bold',pad=18)
ax.add_patch(Rectangle((-1.85,0),3.7,3.1,fill=False,lw=2,ec=GRAY))
ax.plot([0,0],[2.65,3.3],lw=5,c=GRAY);ax.plot([-.7,1.25],[2.68,2.68],lw=6,c=BLUE)
ax.plot([.7,.7],[2.3,2.68],lw=4,c=BLUE)
ax.plot([.15,1.3],[2.3,2.3],lw=7,c=BLUE)
ax.text(.1,3.18,'C carrier shaft',va='center');ax.text(.95,2.8,'C carrier',color=BLUE)
ax.text(1.45,2.33,'W workpiece',va='center',color=BLUE)
ax.annotate('',xy=(.73,1.95),xytext=(.73,2.28),arrowprops={'arrowstyle':'->','color':BLUE,'lw':1.8});ax.text(.82,2.02,'n_w',color=BLUE)
ax.add_patch(Rectangle((-.99,.35),.42,.22,facecolor=RED,edgecolor=RED));ax.text(-1.06,.23,'E evaporating surface',ha='center',color=RED)
ax.annotate('',xy=(-.78,1.0),xytext=(-.78,.58),arrowprops={'arrowstyle':'->','color':RED,'lw':1.8});ax.text(-.7,.83,'n_s',color=RED)
ax.plot([-1.45,-.35],[1.48,1.48],lw=6,c=GRAY);ax.plot([.55,1.55],[1.48,1.48],lw=6,c=GRAY)
ax.text(.82,1.3,'M mask / fixed in chamber',ha='center',color=GRAY)
ax.plot([-.78,.95],[.58,2.3],color=RED,lw=1.8);ax.text(-.22,1.95,'material path',rotation=46,color=RED,fontsize=9)
ax.annotate('',xy=(1.67,2.3),xytext=(1.67,.58),arrowprops={'arrowstyle':'<->','color':'black'})
ax.text(1.73,.93,'H = z_w - z_s',rotation=90)
ax.annotate('',xy=(-1.66,1.12),xytext=(-1.66,.08),arrowprops={'arrowstyle':'->','color':'black'});ax.text(-1.63,1.16,'+z')
ax.annotate('',xy=(-.65,.08),xytext=(-1.66,.08),arrowprops={'arrowstyle':'->','color':'black'});ax.text(-.62,.07,'+x',va='center')
ax.text(-1.82,-.28,'Generic section, not to scale. Actual source shutter, ion source and monitors omitted.\nA fixed source-to-moving-planet offset is generally time dependent.',fontsize=9)
save(fig,'B_source_mask_workpiece')
print('Rendered A and B as SVG and PNG')
