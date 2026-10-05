"""Exact-area nearest-valid-node Voronoi control cells on the complete disk.

Supplemental postprocessing only: no invented off-aperture field values, no core
or original statistic changes. A polygon cell is clipped analytically to a circle.
"""
import math
import numpy as np
from scipy.spatial import Voronoi


def clip_halfplane(poly,normal,constant):
    if not len(poly):return poly
    out=[];a=poly[-1];fa=float(np.dot(normal,a)-constant)
    for b in poly:
        fb=float(np.dot(normal,b)-constant)
        ina,inb=fa<=1e-9,fb<=1e-9
        if ina!=inb:
            t=fa/(fa-fb);out.append(a+t*(b-a))
        if inb:out.append(b)
        a,fa=b,fb
    return np.asarray(out)


def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])


def disk_polygon_area(poly,radius):
    """Green-area contributions: triangles inside, circular sectors outside."""
    if len(poly)<3:return 0.
    total=0.;r2=radius*radius
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        v=b-a;A=float(np.dot(v,v))
        if A<1e-24:continue
        B=2*float(np.dot(a,v));C=float(np.dot(a,a))-r2;D=B*B-4*A*C
        cuts=[0.,1.]
        if D>=-1e-12*max(1.,B*B,abs(4*A*C)):
            sd=math.sqrt(max(0.,D))
            cuts.extend(t for t in ((-B-sd)/(2*A),(-B+sd)/(2*A)) if 0<t<1)
        cuts=sorted(cuts)
        for lo,hi in zip(cuts[:-1],cuts[1:]):
            p=a+lo*v;q=a+hi*v;mid=(p+q)/2
            if float(np.dot(mid,mid))<=r2*(1+1e-14):total+=cross(p,q)/2
            else:total+=r2*math.atan2(cross(p,q),float(np.dot(p,q)))/2
    return max(0.,total)


def full_disk_weights(axis,valid,radius):
    xx,yy=np.meshgrid(axis,axis);points=np.column_stack((xx[valid],yy[valid]))
    vor=Voronoi(points);neighbors=[set() for _ in points]
    for a,b in vor.ridge_points:neighbors[a].add(b);neighbors[b].add(a)
    areas=[]
    square=np.array([[-radius,-radius],[radius,-radius],[radius,radius],[-radius,radius]],dtype=float)
    for i,p in enumerate(points):
        poly=square.copy()
        for j in neighbors[i]:
            q=points[j];poly=clip_halfplane(poly,q-p,(float(np.dot(q,q))-float(np.dot(p,p)))/2)
        areas.append(disk_polygon_area(poly,radius))
    areas=np.array(areas);total=float(areas.sum());coverage=total/(math.pi*radius*radius)
    if abs(coverage-1)>1e-7:raise RuntimeError(f'Voronoi disk coverage failed: {coverage}')
    weights=np.zeros(valid.shape);weights[valid]=areas/total
    return weights,coverage


def aggregate(field,axis,radius):
    valid=np.isfinite(field);weights,coverage=full_disk_weights(axis,valid,radius)
    h=field[valid];w=weights[valid];mu=float(np.dot(w,h))
    cv=math.sqrt(float(np.dot(w,(h-mu)**2)))/mu*100.
    return {'controlled_full_disk_cv_percent':cv,'controlled_full_disk_mean_nm':mu,
        'physical_area_coverage':coverage,'method':'Nearest-valid-node Voronoi cells clipped to exact circle; field piecewise constant per cell. Supplemental statistic, not an accuracy bound.'}
