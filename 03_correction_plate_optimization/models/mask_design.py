#!/usr/bin/env python3
"""T03 research reference. SI inputs, nm ray weights, NumPy-only.
T02 is a read-only sibling dependency. No machine calibration or CAD release.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import numpy as np
sys.dont_write_bytecode = True
T02 = Path(__file__).resolve().parents[2] / '02_machine_modeling' / 'models'
sys.path.insert(0, str(T02))
from deposition_reference import (PlanetaryPose, disk_source, point_source,
    Source, disk_surface, transfer_kernel, time_quadrature, deposit, RectangleMask)
VERSION='T03-mask-0.1'

@dataclass(frozen=True)
class Config:
    orbit_m: float=.22
    height_m: float=.65
    radius_m: float=.12
    carrier_rpm: float=15.
    spin_ratio: float=3.7
    carrier_phase: float=.23
    relative_phase: float=.51
    duration_s: float=17.3
    source_x_m: float=.12
    source_y_m: float=0.
    source_radius_m: float=.015
    source_exponent: float=2.
    mask_z_m: float=.50
    mask_x_shift_m: float=0.
    mask_y_shift_m: float=0.
    mask_thickness_m: float=.001
    rate_kg_s: float=1e-6
    rate_ripple: float=.08
    density_kg_m3: float=3000.
    sticking: float=1.

# All invented geometry; no claimed vendor minimum. Width is a half-width.
XKNOTS=np.linspace(.02,.33,8)
BMIN=.002
BMAX=.10
MAX_SLOPE=.8
MAX_SECOND_DIFF=.028

@dataclass
class RayBundle:
    base_nm: np.ndarray
    area: np.ndarray
    rings: np.ndarray
    points_m: np.ndarray
    pid: np.ndarray
    x: np.ndarray
    y: np.ndarray
    dx_dz: np.ndarray
    dy_dz: np.ndarray
    weight_nm: np.ndarray
    config: Config
    numerics: dict

    def masked(self, widths, thickness_m=None):
        thick=self.config.mask_thickness_m if thickness_m is None else thickness_m
        if not np.isfinite(thick) or thick < 0 or thick > self.config.mask_thickness_m:
            raise ValueError('Thickness must lie in [0, cached config thickness]; rebuild for a thicker slab')
        blocked=band_blocked(self.x,self.y,self.dx_dz,self.dy_dz,widths,thick)
        loss=np.bincount(self.pid,weights=self.weight_nm*blocked,minlength=len(self.base_nm))
        return self.base_nm-loss


def case_parts(cfg, nr, na, source_nr, source_na, azimuth_offset=0.):
    if not all(np.isfinite(v) for v in asdict(cfg).values()):
        raise ValueError('All configuration values must be finite')
    if cfg.source_radius_m < 0 or cfg.mask_thickness_m < 0 or cfg.radius_m <= 0:
        raise ValueError('Invalid source, substrate or slab dimensions')
    if not (0 < cfg.mask_z_m-cfg.mask_thickness_m/2 and cfg.mask_z_m+cfg.mask_thickness_m/2 < cfg.height_m):
        raise ValueError('Mask slab must lie strictly between horizontal source and flat substrate')
    if cfg.duration_s<=0 or cfg.rate_kg_s<0 or abs(cfg.rate_ripple)>1 or cfg.density_kg_m3<=0 or not 0<=cfg.sticking<=1:
        raise ValueError('Invalid process inputs')
    p,n,area=disk_surface(cfg.radius_m,nr,na)
    if azimuth_offset:
        c,s=np.cos(azimuth_offset),np.sin(azimuth_offset)
        p[:,:2]=p[:,:2]@np.array([[c,s],[-s,c]])
    pose=PlanetaryPose(cfg.orbit_m,cfg.height_m,cfg.carrier_rpm,cfg.spin_ratio,cfg.carrier_phase,cfg.relative_phase)
    src=(disk_source(cfg.source_radius_m,source_nr,source_na,center=(cfg.source_x_m,cfg.source_y_m,0),exponent=cfg.source_exponent)
         if cfg.source_radius_m>0 else point_source((cfg.source_x_m,cfg.source_y_m,0),exponent=cfg.source_exponent))
    rate=lambda t:cfg.rate_kg_s*(1+cfg.rate_ripple*np.sin(2*np.pi*.27*np.asarray(t)+.31))
    return p,n,area,pose,src,rate


def build_bundle(cfg=Config(),nr=4,na=12,panels=384,source_nr=2,source_na=8,azimuth_offset=0.,time_order=1):
    """Cache only rays that can intersect any allowed graph mask; retain all base flux.
    Photon-like ballistic rays have nonnegative physical weights. Finite source
    weights are mass fractions, not equally weighted samples. Cached footprint
    includes the finite slab's possible lateral travel at maximum thickness.
    """
    p,n,area,pose,src,rate=case_parts(cfg,nr,na,source_nr,source_na,azimuth_offset)
    ts,tw=time_quadrature(0,cfg.duration_s,panels,time_order)
    base=np.zeros(len(p)); parts=[[] for _ in range(6)]
    for k in range(0,len(ts),32):
        t=ts[k:k+32]; x,norm=pose.evaluate(t,p,n)
        delta=x[:,:,None,:]-src.positions_m
        r2=np.sum(delta*delta,axis=-1); u=delta/np.sqrt(r2)[...,None]
        cs=np.sum(u*src.normals,axis=-1); ci=np.sum(-u*norm[:,:,None,:],axis=-1)
        kernel=np.where(cs>0,(src.exponent+1)/(2*np.pi)*np.maximum(cs,0)**src.exponent,0)*np.maximum(ci,0)/r2
        w=kernel*src.fractions*(tw[k:k+32]*rate(t))[:,None,None]*cfg.sticking/cfg.density_kg_m3*1e9
        base+=w.sum(axis=(0,2))
        f=(cfg.mask_z_m-src.positions_m[:,2])/delta[...,2]
        hit=src.positions_m+f[...,None]*delta
        xx=hit[...,0]-cfg.mask_x_shift_m; yy=hit[...,1]-cfg.mask_y_shift_m
        dx=delta[...,0]/delta[...,2]; dy=delta[...,1]/delta[...,2]
        margin=.02 # sufficient for slab thickness up to .01m in these bounded cases; enforce below
        if cfg.mask_thickness_m>.01 or np.max(np.abs(dx))*cfg.mask_thickness_m/2>margin or np.max(np.abs(dy))*cfg.mask_thickness_m/2>margin:
            raise ValueError('Cache bounding margin inadequate; rebuild with generalized bounds')
        keep=(xx>=XKNOTS[0]-margin)&(xx<=XKNOTS[-1]+margin)&(abs(yy)<=BMAX+margin)&(w>0)&(f>0)&(f<1)
        ids=np.broadcast_to(np.arange(len(p))[None,:,None],w.shape)
        for dest,arr in zip(parts,(ids,xx,yy,dx,dy,w)): dest.append(arr[keep])
    arrays=[np.concatenate(a) for a in parts]
    return RayBundle(base,area/area.sum(),np.repeat(np.arange(nr),na),p,*arrays,cfg,
                     dict(surface_nr=nr,surface_na=na,time_panels=panels,time_order=time_order,source_nr=source_nr,source_na=source_na,azimuth_offset=azimuth_offset,time_nodes=len(ts),source_nodes=len(src.fractions),cached_rays=len(arrays[0])))


def band_blocked(x,y,dx_dz,dy_dz,widths,thickness_m=0.):
    """Exact union of convex trapezoid prisms, slab centered at mask_z.
    x,y are midplane ray hits; dx/dz,dy/dz are ray slopes. For zero thickness,
    the closed opaque polygon is |y|<=piecewise-linear width(x).
    """
    b=np.asarray(widths,dtype=float)
    if b.shape!=XKNOTS.shape or np.any(~np.isfinite(b)) or np.any(b<0) or thickness_m<0:
        raise ValueError('Finite nonnegative widths and thickness required')
    x,y,dx_dz,dy_dz=np.broadcast_arrays(x,y,dx_dz,dy_dz)
    if thickness_m==0:
        return (x>=XKNOTS[0])&(x<=XKNOTS[-1])&(np.abs(y)<=np.interp(x,XKNOTS,b))
    # Slab-local z in [-t/2,t/2]; segment has been verified source-to-target.
    result=np.zeros(x.shape,dtype=bool)
    for j in range(len(b)-1):
        lo=np.full(x.shape,-thickness_m/2); hi=np.full(x.shape,thickness_m/2)
        m=(b[j+1]-b[j])/(XKNOTS[j+1]-XKNOTS[j]); c=b[j]-m*XKNOTS[j]
        valid=np.ones(x.shape,dtype=bool)
        # Each inequality A + B*z <= 0 describes one convex trapezoid wall.
        for A,B in ((XKNOTS[j]-x,-dx_dz),(x-XKNOTS[j+1],dx_dz),(y-m*x-c,dy_dz-m*dx_dz),(-y-m*x-c,-dy_dz-m*dx_dz)):
            par=np.abs(B)<1e-15
            valid &= ~(par&(A>0))
            crossing=np.divide(-A,B,out=np.zeros_like(A),where=~par)
            hi=np.where(B>1e-15,np.minimum(hi,crossing),hi)
            lo=np.where(B<-1e-15,np.maximum(lo,crossing),lo)
        result |= valid&(lo<=hi)
    return result


def influence_matrix(bundle,nx=12,ny=8):
    """Thin-plane opacity cells. A[p,j] [nm] is lost thickness at opacity=1.
    Outside cells is transparent; cells tile a rectangle. Not a shape Jacobian.
    """
    xe=np.linspace(XKNOTS[0],XKNOTS[-1],nx+1); ye=np.linspace(-BMAX,BMAX,ny+1)
    ix=np.searchsorted(xe,bundle.x,side='right')-1; iy=np.searchsorted(ye,bundle.y,side='right')-1
    valid=(ix>=0)&(ix<nx)&(iy>=0)&(iy<ny)
    cid=ix*ny+iy
    A=np.bincount(bundle.pid[valid]*(nx*ny)+cid[valid],weights=bundle.weight_nm[valid],minlength=len(bundle.base_nm)*nx*ny).reshape(len(bundle.base_nm),nx*ny)
    return A,xe,ye


def radial_projection(rings,weights):
    n=len(rings); P=np.zeros((n,n))
    for group in np.unique(rings):
        idx=np.flatnonzero(rings==group); P[np.ix_(idx,idx)]=weights[idx]/weights[idx].sum()
    return P


def metric(h,base,weights,rings):
    h=np.asarray(h); w=np.asarray(weights)/np.sum(weights); mu=w@h; mu0=w@base
    if mu<=0: raise ValueError('Nonpositive mean: relative uniformity undefined')
    ring=radial_projection(rings,w)@h
    return dict(mean_nm=float(mu),minimum_nm=float(h.min()),maximum_nm=float(h.max()),
                pv_over_mean=float(np.ptp(h)/mu),max_deviation_over_mean=float(np.max(abs(h-mu))/mu),
                cv=float(np.sqrt(w@((h-mu)**2))/mu),radial_cv=float(np.sqrt(w@((ring-mu)**2))/mu),
                angular_cv=float(np.sqrt(w@((h-ring)**2))/mu),throughput_ratio=float(mu/mu0),
                same_mean_time_multiplier_estimate=float(mu0/mu),max_pointwise_increase_nm=float(np.max(h-base)))


def objective_matrix(bundle,radial_weight=1.,angular_weight=1.,target_weight=.10):
    n=len(bundle.base_nm); w=bundle.area; P=radial_projection(bundle.rings,w); one=np.ones((n,1))@w[None,:]
    mu0=w@bundle.base_nm
    C=np.concatenate((np.sqrt(radial_weight*w)[:,None]*(P-one),np.sqrt(angular_weight*w)[:,None]*(np.eye(n)-P),np.sqrt(target_weight*w)[None,:]))/mu0
    # Last row is not sqrt(w) mean; replace by true weighted mean residual.
    C[-1]=np.sqrt(target_weight)*w/mu0
    return C


def project_box_throughput(v,a,cap):
    """Euclidean projection onto [0,1]^n intersect a@x<=cap; a>=0."""
    v=np.asarray(v,dtype=float);a=np.asarray(a,dtype=float)
    if v.shape != a.shape or v.ndim != 1 or not np.isfinite(cap) or np.any(~np.isfinite(v)) or np.any(~np.isfinite(a)) or cap<0 or np.any(a<0): raise ValueError('Finite matched vectors, nonnegative cap and attenuation required')
    x=np.clip(v,0,1)
    if a@x<=cap: return x
    lo=0.;hi=1.
    while a@np.clip(v-hi*a,0,1)>cap: hi*=2
    for _ in range(65):
        mid=(lo+hi)/2
        if a@np.clip(v-mid*a,0,1)>cap:lo=mid
        else:hi=mid
    return np.clip(v-hi*a,0,1)


def grid_difference(nx,ny):
    rows=[]
    for i in range(nx):
        for j in range(ny):
            a=i*ny+j
            for b in ([a+ny] if i+1<nx else [])+([a+1] if j+1<ny else []):
                row=np.zeros(nx*ny);row[a]=1;row[b]=-1;rows.append(row)
    return np.array(rows)


def optimize_relaxation(bundle,nx=12,ny=8,target_ratio=.90,min_throughput=.80,regularization=1e-5,max_iterations=5000,tolerance=1e-8):
    if regularization < 0 or not np.isfinite(regularization) or not 0 <= min_throughput <= 1 or not 0 <= target_ratio <= 1 or max_iterations < 1 or tolerance <= 0:
        raise ValueError('Require convex regularization, ratios in [0,1], positive iteration/tolerance budget')
    A,xe,ye=influence_matrix(bundle,nx,ny); base=bundle.base_nm; mu0=bundle.area@base
    if mu0 <= 0: raise ValueError('Positive unmasked mean required')
    C=objective_matrix(bundle); D=grid_difference(nx,ny)
    rhs=C@base;rhs[-1]-=np.sqrt(.10)*target_ratio
    B=C@A; Q=B.T@B+regularization*(D.T@D)/max(1,len(D)); g=-(B.T@rhs)
    lip=float(np.linalg.eigvalsh(Q)[-1]);lip=max(lip,1e-15)
    a=bundle.area@A/mu0; cap=1-min_throughput
    c=np.zeros(nx*ny); converged=False
    for iteration in range(1,max_iterations+1):
        new=project_box_throughput(c-(Q@c+g)/lip,a,cap)
        residual=float(np.linalg.norm(new-c,np.inf)*lip)
        c=new
        if residual<tolerance:converged=True;break
    return dict(opacity=c,matrix=A,x_edges=xe,y_edges=ye,iterations=iteration,converged=converged,projected_gradient_inf=residual,
                objective=float(.5*np.linalg.norm(C@(base-A@c)-np.r_[np.zeros(len(rhs)-1),np.sqrt(.10)*target_ratio])**2+.5*regularization*np.linalg.norm(D@c)**2/max(1,len(D))),
                throughput_violation=float(max(0,a@c-cap)),matrix_rank=int(np.linalg.matrix_rank(A)),singular_values=np.linalg.svd(A,compute_uv=False))


def manufacturing(widths):
    b=np.asarray(widths,dtype=float)
    if b.shape != XKNOTS.shape or np.any(~np.isfinite(b)):
        return dict(passed=False,checks={'valid_shape_and_finite':False},scope='2D polygon screen only')
    slopes=np.diff(b)/np.diff(XKNOTS)
    checks=dict(finite=bool(np.all(np.isfinite(b))),bounded=bool(np.all(b>=BMIN-1e-12)&np.all(b<=BMAX+1e-12)),
                min_horizontal_segment=bool(np.min(np.diff(XKNOTS))>=.015),connected=bool(np.all(b>0)),
                max_slope=bool(np.max(abs(slopes))<=MAX_SLOPE+1e-12),second_difference=bool(np.max(abs(np.diff(b,2)))<=MAX_SECOND_DIFF+1e-12))
    return dict(passed=all(checks.values()),checks=checks,minimum_full_width_m=float(2*b.min()),maximum_slope=float(max(abs(slopes))),maximum_second_difference_m=float(max(abs(np.diff(b,2)))),
                scope='2D polygon geometric screen only; no stress/thermal/fixture/edge-radius certification')


def shape_objective(bundles,widths,min_throughput=.80,target_ratio=.90,regularization=2e-3,thickness_m=0.):
    if not bundles or regularization < 0 or not np.isfinite(regularization):
        raise ValueError('Nonempty scenario list and nonnegative regularization required')
    if not manufacturing(widths)['passed']:return float('inf'),[]
    vals=[];metrics=[]
    for bundle in bundles:
        h=bundle.masked(widths,thickness_m); m=metric(h,bundle.base_nm,bundle.area,bundle.rings);metrics.append(m)
        if m['throughput_ratio']<min_throughput:return float('inf'),metrics
        mu0=bundle.area@bundle.base_nm;P=radial_projection(bundle.rings,bundle.area);mu=bundle.area@h
        val=bundle.area@((P@h-mu)**2+(h-P@h)**2)/mu0**2+.10*(mu/mu0-target_ratio)**2
        vals.append(val)
    # Finite scenarios, minimax. No probability/coverage guarantee.
    smooth=regularization*np.mean((np.diff(widths,2)/BMAX)**2)
    return float(max(vals)+smooth),metrics


def optimize_shape(bundles,initial,max_evaluations=480,min_throughput=.80,target_ratio=.90):
    """Deterministic feasible coordinate pattern search; thin-plane train model.
    No gradient or convex/global-optimality claim. Common evaluation budget.
    """
    b=np.asarray(initial).copy(); score,ms=shape_objective(bundles,b,min_throughput,target_ratio)
    if not np.isfinite(score): raise ValueError('Infeasible initial shape')
    count=1;trace=[dict(evaluations=count,objective=score,step_m=0.)]
    step=.012
    while count+2*len(b)<=max_evaluations and step>=.000375:
        changed=False
        for j in range(len(b)):
            best=score;candidate=b
            for sign in (-1,1):
                trial=b.copy();trial[j]+=sign*step
                value,_=shape_objective(bundles,trial,min_throughput,target_ratio);count+=1
                if value<best-1e-14:best=value;candidate=trial
            if best<score-1e-14:changed=True;score=best;b=candidate
        trace.append(dict(evaluations=count,objective=score,step_m=step))
        if not changed:step/=2
    return dict(widths_m=b,objective=score,evaluations=count,stopping_reason='budget' if count+2*len(b)>max_evaluations else 'step_floor',last_step_m=step,trace=trace,manufacturing=manufacturing(b))


def relaxation_to_band(result):
    c=result['opacity'].reshape(len(result['x_edges'])-1,len(result['y_edges'])-1)
    width=.5*np.sum(c*np.diff(result['y_edges'])[None,:],axis=1)
    x=.5*(result['x_edges'][:-1]+result['x_edges'][1:])
    b=np.interp(XKNOTS,x,width);b=np.clip(b,BMIN,BMAX)
    # Interpolate towards a feasible constant until slope/curvature screen passes.
    mean=np.full_like(b,np.clip(np.mean(b),BMIN,BMAX))
    for _ in range(60):
        if manufacturing(b)['passed']:return b
        b=(b+mean)/2
    return mean


def evaluate_streaming(cfg, widths, nr=6, na=24, panels=4096,
                       source_nr=3, source_na=16, azimuth_offset=.137,
                       thickness_m=None, probe_points_m=None, opacity_grid=None):
    """Uncached all-ray validation, bounded RAM. Area metrics exclude edge probes.
    Optional probe_points_m has no area interpretation and returns raw h only.
    The same validated physical kernel is used, but no footprint pruning occurs.
    """
    p,n,area,pose,src,rate=case_parts(cfg,nr,na,source_nr,source_na,azimuth_offset)
    if probe_points_m is not None:
        p=np.asarray(probe_points_m,dtype=float)
        n=np.broadcast_to([0.,0.,-1.],p.shape)
    thick=cfg.mask_thickness_m if thickness_m is None else thickness_m
    if opacity_grid is not None:
        if widths is not None or thick != 0:raise ValueError('Opacity validation requires widths=None and thickness_m=0')
        xe,ye,c=opacity_grid
        if np.any(np.diff(xe)<=0) or np.any(np.diff(ye)<=0) or np.asarray(c).size!=(len(xe)-1)*(len(ye)-1) or not np.all(np.isfinite(c)) or np.any(np.asarray(c)<0) or np.any(np.asarray(c)>1):
            raise ValueError('Invalid opacity grid')
    if thick < 0 or not np.isfinite(thick) or not (0 < cfg.mask_z_m-thick/2 and cfg.mask_z_m+thick/2 < cfg.height_m):
        raise ValueError('Validation slab lies outside source-to-substrate gap')
    ts,tw=time_quadrature(0,cfg.duration_s,panels,1)
    base=np.zeros(len(p));h=np.zeros(len(p))
    for k in range(0,len(ts),16):
        t=ts[k:k+16];x,norm=pose.evaluate(t,p,n)
        d=x[:,:,None,:]-src.positions_m;r2=np.sum(d*d,axis=-1);u=d/np.sqrt(r2)[...,None]
        cs=np.sum(u*src.normals,axis=-1);ci=np.sum(-u*norm[:,:,None,:],axis=-1)
        kernel=np.where(cs>0,(src.exponent+1)/(2*np.pi)*np.maximum(cs,0)**src.exponent,0)*np.maximum(ci,0)/r2
        w=kernel*src.fractions*(tw[k:k+16]*rate(t))[:,None,None]*cfg.sticking/cfg.density_kg_m3*1e9
        base+=w.sum(axis=(0,2))
        if widths is None and opacity_grid is None:
            h+=w.sum(axis=(0,2));continue
        f=(cfg.mask_z_m-src.positions_m[:,2])/d[...,2];hit=src.positions_m+f[...,None]*d
        xx=hit[...,0]-cfg.mask_x_shift_m;yy=hit[...,1]-cfg.mask_y_shift_m
        if opacity_grid is not None:
            xe,ye,c=opacity_grid;nx=len(xe)-1;ny=len(ye)-1
            ix=np.searchsorted(xe,xx,side='right')-1;iy=np.searchsorted(ye,yy,side='right')-1
            valid=(ix>=0)&(ix<nx)&(iy>=0)&(iy<ny)
            atten=np.zeros_like(xx);atten[valid]=np.asarray(c).reshape(nx,ny)[ix[valid],iy[valid]]
            h+=(w*(1-atten)).sum(axis=(0,2))
        else:
            blocked=band_blocked(xx,yy,d[...,0]/d[...,2],d[...,1]/d[...,2],widths,thick)
            h+=(w*(~blocked)).sum(axis=(0,2))
    out=dict(thickness_nm=h,base_nm=base,points_m=p,numerics=dict(surface_nr=nr,surface_na=na,time_panels=panels,source_nr=source_nr,source_na=source_na,azimuth_offset=azimuth_offset,thickness_m=thick,probe_points=probe_points_m is not None))
    if probe_points_m is None:
        out['metrics']=metric(h,base,area,np.repeat(np.arange(nr),na)) if area@h > 0 else None
        out['baseline_metrics']=metric(base,base,area,np.repeat(np.arange(nr),na))
    return out


def export_polygon(widths):
    """Closed ordered vertices [m], synthetic geometry, not a machining release."""
    b=np.asarray(widths)
    if not manufacturing(b)['passed']:raise ValueError('Shape fails geometric screen')
    return np.vstack((np.column_stack((XKNOTS,b)),np.column_stack((XKNOTS[::-1],-b[::-1])),[XKNOTS[0],b[0]]))
