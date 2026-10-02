"""Original synthetic qualification arithmetic, not a standards implementation.
No equipment I/O. No real certification or process settings. Python stdlib only.
"""
import csv
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def finite(x, name):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f'{name} must be finite numeric')
    return float(x)

def paired_standard_uncertainty(u_before, u_after, correlation=0.0):
    a=finite(u_before,'u_before'); b=finite(u_after,'u_after'); r=finite(correlation,'correlation')
    if a<0 or b<0 or not -1<=r<=1:
        raise ValueError('standard uncertainties must be nonnegative; correlation in [-1,1]')
    return math.sqrt(max(0.0,a*a+b*b-2*r*a*b))

def interval_decision(y, expanded_u, lower=None, upper=None):
    """Closed specification interval; three-way rule selected ONLY for this demo."""
    y=finite(y,'y'); U=finite(expanded_u,'expanded_u')
    if U<0 or (lower is None and upper is None):
        raise ValueError('nonnegative U and at least one bound required')
    L=-math.inf if lower is None else finite(lower,'lower')
    H=math.inf if upper is None else finite(upper,'upper')
    if L>H: raise ValueError('lower exceeds upper')
    if y-U>=L and y+U<=H: return 'accept_under_demo_rule'
    if y+U<L or y-U>H: return 'reject_under_demo_rule'
    return 'indeterminate_under_demo_rule'

def zero_failure_upper(n, confidence=.95):
    """Exact one-sided binomial upper p with zero failures, iid assumption."""
    c=finite(confidence,'confidence')
    if isinstance(n,bool) or not isinstance(n,int) or n<=0 or not 0<c<1:
        raise ValueError('positive integer n and confidence in (0,1) required')
    return -math.expm1(math.log1p(-c)/n)

def minimum_zero_failure_n(target_p, confidence=.95):
    p=finite(target_p,'target_p'); c=finite(confidence,'confidence')
    if not 0<p<1 or not 0<c<1: raise ValueError('probabilities must be in (0,1)')
    n=math.ceil(math.log1p(-c)/math.log1p(-p))
    # Defend exact integer and float rounding boundaries.
    while zero_failure_upper(n,c)>p: n+=1
    while n>1 and zero_failure_upper(n-1,c)<=p: n-=1
    return n

def synthetic_transmittance(wavelength_nm):
    x=finite(wavelength_nm,'wavelength_nm')
    return .955-.027*math.exp(-.5*((x-1045.)/1.2)**2)

def plan_gaps(plan):
    """Structural gap checker only. Never authorizes experiments or release."""
    gaps=[]
    for key in ('product_id','contract_id','drawing_revision','lot_definition','laboratory_id','approval_record'):
        if not plan.get(key): gaps.append(f'plan.{key}')
    tests=plan.get('tests')
    if not isinstance(tests,list) or not tests: return gaps+['plan.tests']
    seen=set()
    for i,t in enumerate(tests):
        if not isinstance(t,dict): gaps.append(f'tests[{i}].object'); continue
        ident=t.get('test_id')
        if not ident or ident in seen: gaps.append(f'tests[{i}].unique_test_id')
        seen.add(ident)
        app=t.get('applicability')
        if app not in ('applicable','not_applicable'):
            gaps.append(f'{ident}.applicability'); continue
        if app=='not_applicable':
            if not t.get('exclusion_reason') or not t.get('exclusion_approval'):
                gaps.append(f'{ident}.approved_exclusion')
            continue
        for key in ('method_id','edition','controlled_text_id','clause','severity_or_method_conditions',
                    'sample_plan','pre_post_measurements','acceptance_source','acceptance_limits',
                    'decision_rule','uncertainty_budget_id','laboratory_capability_evidence',
                    'sequence_and_recovery','safety_review_id'):
            if t.get(key) in (None,'',[],{}): gaps.append(f'{ident}.{key}')
        if t.get('normative_procedure_verified') is not True:
            gaps.append(f'{ident}.normative_procedure_verified')
    return gaps

def build_results():
    rows=[]
    for label,pre,post in [('A',.956,.950),('B',.950,.942),('C',.949,.930)]:
        u=.002; U=2*u; delta=post-pre; ud=paired_standard_uncertainty(u,u,0)
        rows.append(dict(sample=f'SYNTH-{label}',before=pre,after=post,u_before=u,u_after=u,
                         k_demo=2,correlation_assumed=0,delta=delta,u_delta=ud,U_delta=2*ud,
                         post_rule=interval_decision(post,U,lower=.940),
                         change_rule=interval_decision(delta,2*ud,lower=-.010,upper=.010),
                         source='original_synthetic_not_standard_requirement'))
    coarse=[1000+10*i for i in range(11)]; fine=[1000+.1*i for i in range(1001)]
    cp=min((synthetic_transmittance(x),x) for x in coarse)
    fp=min((synthetic_transmittance(x),x) for x in fine)
    correlation=[dict(rho=r,u_delta=paired_standard_uncertainty(.002,.002,r)) for r in (0,.75,1,-1)]
    # Synthetic reference drift example: independent reference errors assumed.
    sample_delta=.942-.950; ref_delta=.988-.990
    corrected_delta=sample_delta-ref_delta
    corrected_u=math.sqrt(paired_standard_uncertainty(.002,.002)**2+paired_standard_uncertainty(.001,.001)**2)
    plan=json.loads((ROOT/'templates/qualification_plan.json').read_text())
    return dict(version='T09-r1-v0.1.0',data_class='synthetic_demonstration',real_compliance_statement=False,
                numerical_assumptions='All values/thresholds/example n are synthetic, not normative. iid binomial; closed interval demo; no covariance except stated.',
                samples=rows,correlation_demo=correlation,
                drift_demo=dict(sample_delta=sample_delta,reference_delta=ref_delta,corrected_delta=corrected_delta,u_corrected=corrected_u,correlations_between_sample_and_reference_assumed_zero=True),
                zero_failure=[dict(n=n,confidence=.95,upper_probability=zero_failure_upper(n)) for n in (10,30,100,299)],
                minimum_n_for_p01_at_conf95=minimum_zero_failure_n(.01),
                grid_demo=dict(lower_limit=.94,coarse_step_nm=10,fine_step_nm=.1,
                               coarse_min=cp[0],coarse_at_nm=cp[1],fine_min=fp[0],fine_at_nm=fp[1],
                               coarse_nominal_pass=cp[0]>=.94,fine_nominal_pass=fp[0]>=.94,
                               claim='illustrates missed narrow feature; no universal step prescription'),
                plan_template_gaps=plan_gaps(plan),execution_authorized=False)

def make_svg(results):
    # Native vector visualization of original data, no third-party image editing.
    pts=[]
    def xy(x,y): return (80+(x-1000)*7.2,315-(y-.92)*6000)
    for i in range(1001):
        x=1000+i*.1; X,Y=xy(x,synthetic_transmittance(x)); pts.append(f'{X:.2f},{Y:.2f}')
    elems=['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="430" viewBox="0 0 920 430">',
           '<rect width="920" height="430" fill="white"/>',
           '<g font-family="Arial, sans-serif" fill="#182b3a">',
           '<text x="45" y="35" font-size="20">Synthetic example: coarse sampling misses a narrow spectral dip</text>',
           '<text x="45" y="60" font-size="13">All data and limits are illustrative. This is not a standard requirement or product result.</text>']
    for y in (.92,.93,.94,.95,.96):
        _,Y=xy(1000,y); elems += [f'<line x1="80" y1="{Y}" x2="800" y2="{Y}" stroke="#dde3e8"/>',f'<text x="35" y="{Y+4}" font-size="12">{y:.2f}</text>']
    for x in range(1000,1101,20):
        X,_=xy(x,.92); elems.append(f'<text x="{X-15}" y="345" font-size="12">{x}</text>')
    _,Y=xy(1000,.94); elems.append(f'<line x1="80" y1="{Y}" x2="800" y2="{Y}" stroke="#b42318" stroke-dasharray="6 4"/>')
    elems.append('<polyline fill="none" stroke="#1b6ba8" stroke-width="2.5" points="'+' '.join(pts)+'"/>')
    for x in range(1000,1101,10):
        X,Y=xy(x,synthetic_transmittance(x)); elems.append(f'<circle cx="{X}" cy="{Y}" r="4" fill="#d08a00"/>')
    elems += ['<text transform="translate(16 285) rotate(-90)" font-size="12">Transmittance (fraction)</text>', '<text x="330" y="380" font-size="14">Wavelength (nm), synthetic coordinate</text>',
              '<text x="80" y="410" font-size="12">Blue: fine curve | Amber: coarse samples | Dashed red: example lower limit 0.94</text>',
              '</g></svg>']
    return '\n'.join(elems)

def main():
    r=build_results()
    (ROOT/'data/demo_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'data/synthetic_measurements.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r['samples'][0]));w.writeheader();w.writerows(r['samples'])
    (ROOT/'figures/synthetic_spectral_sampling.svg').write_text(make_svg(r))
    print(json.dumps(dict(data_class=r['data_class'],n_min=r['minimum_n_for_p01_at_conf95'],grid=r['grid_demo'],template_gap_count=len(r['plan_template_gaps']),real_compliance_statement=False),indent=2))
if __name__=='__main__': main()
