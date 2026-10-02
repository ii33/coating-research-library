#!/usr/bin/env python3
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/t08-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/t08-font-cache')
import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'data/benchmark_results.json').read_text());e=json.loads((ROOT/'data/extension_results.json').read_text())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','svg.fonttype':'none'})
colors={'accurate':'#006b8f','finite_difference':'#d57c22','quick':'#ad4d77','lbfgsb':'#459b79','coarse_then_polish':'#795dc0'}
def save(fig,name):
 fig.suptitle(fig._title+'\nSynthetic reference models; not measured or production qualified',fontsize=12)
 fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(ROOT/'figures'/f'{name}.svg');fig.savefig(ROOT/'reviews'/f'{name}_preview.png',dpi=110);plt.close(fig)
fig,ax=plt.subplots(1,3,figsize=(13,4));fig._title='T08: Budgeted optimization, accuracy and actual cost'
for i,(bid,b) in enumerate(r['cases'].items()):
 for name,z in b['runs'].items():
  x=z.get('seconds_total',z['seconds']);y=z['holdout']['cost'];ax[i].scatter(x,y,c=colors[name],s=55,label=name)
 ax[i].axhline(b['initial_holdout']['cost'],color='gray',ls='--',lw=1,label='initial');ax[i].set_title(f'{bid}: {b["seed"]}');ax[i].set_xlabel('Observed wall time (s)');ax[i].set_ylabel('Dense mixed-angle objective');ax[i].set_xscale('log');ax[i].set_yscale('log');ax[i].grid(alpha=.15)
ax[0].legend(fontsize=7);save(fig,'01_budget_accuracy')
fig,ax=plt.subplots(1,3,figsize=(13,4));fig._title='T08: Independent spectral audits (held-out mid angle, s polarization)'
for i,(bid,bname,ang,obs) in enumerate([('B01','AR','15','R'),('B02','HR','22.5','R'),('B03','pass','2.5','T')]):
 d=np.genfromtxt(ROOT/'data/spectra'/f'{bid}_{bname}.csv',names=True,delimiter=',')
 for name,c in [('initial','gray'),('accurate',colors['accurate']),('quick',colors['quick'])]:
  col=f'{name}_{ang}_s_{obs}'.replace('.','');ax[i].plot(d['wavelength_um'],d[col],label=name,color=c)
 ax[i].set_title(bid);ax[i].set_xlabel('Wavelength (um)');ax[i].set_ylabel(obs+' (fraction)');ax[i].grid(alpha=.15)
ax[0].legend();save(fig,'02_holdout_spectra')
fig,ax=plt.subplots(1,3,figsize=(13,4));fig._title='T08: Failure cases must survive the optimization workflow'
d=np.genfromtxt(ROOT/'data/spectra/undersampling.csv',names=True,delimiter=',');ax[0].plot(d['wavelength_um'],d['R']);ax[0].scatter([1,1.2],[0,0],color='red',label='training endpoints');ax[0].set(xlabel='Wavelength (um)',ylabel='R',title='Both endpoints miss a 72% reflection peak');ax[0].legend(fontsize=8)
z=r['extra']['surrogate']['trace'];xx=[v['iteration'] for v in z];ax[1].plot(xx,[v['predicted_reduction'] for v in z],label='predicted');ax[1].plot(xx,[v['actual_reduction'] for v in z],label='actual');ax[1].set_yscale('symlog',linthresh=1e-7);ax[1].set(xlabel='Trial',ylabel='Cost reduction',title='Actual-model checks reject harmful trials');ax[1].legend(fontsize=8)
for name,c in [('nominal','#006b8f'),('robust','#d57c22')]:
 zz=sorted(r['extra']['robustness']['comparison'][name]['all_scenario_costs']);ax[2].plot(zz,np.arange(1,len(zz)+1)/len(zz),label=name,color=c)
ax[2].set(xlabel='Scenario cost (64 synthetic samples)',ylabel='Empirical cumulative fraction',title='Robustness tradeoff, not measured yield');ax[2].legend(fontsize=8)
save(fig,'03_failures_and_robustness')
fig,ax=plt.subplots(1,3,figsize=(13,4));fig._title='T08: Derivative verification, scaling, and manufacturing tradeoff'
for bid in r['cases']:
 zz=[z for z in r['extra']['gradient_check'] if z['case']==bid];ax[0].loglog([z['step_scaled'] for z in zz],[z['relative_fro_error'] for z in zz],marker='o',label=bid)
ax[0].set(xlabel='Central difference h (scaled thickness)',ylabel='Relative Jacobian error');ax[0].legend(fontsize=8)
for name in ['prefix_suffix','forward_all_directions']:
 zz=[z for z in r['extra']['kernel_performance'] if z['mode']==name];ax[1].loglog([z['layers'] for z in zz],[z['median_seconds'] for z in zz],marker='o',label=name)
ax[1].set(xlabel='Layers',ylabel='Median seconds, 7 runs / 61 wavelengths');ax[1].legend(fontsize=7)
zz=r['extra']['thickness_tradeoff'];ax[2].plot([z['cap_um'] for z in zz],[z['holdout']['cost'] for z in zz],marker='o');ax[2].set(xlabel='Total physical thickness cap (um)',ylabel='Dense audit cost',title='B01 epsilon constraints')
save(fig,'04_gradients_and_constraints')
lines=['# 09a · 本机复算结果与测时（非材料实测）','', '这里“测时”指本机墙钟观测；全部光谱由冻结proxy计算。均值与最坏误差、不同角度集合不可互相替代。','', '| 问题/方法 |训练cost|审计cost|审计最坏/容差|秒|实际谱调用|solver成功|','|---|---:|---:|---:|---:|---:|---|']
for bid,b in r['cases'].items():
 for name,z in b['runs'].items():
  lines.append(f'|{bid}/{name}|{z["cost"]:.8g}|{z["holdout"]["cost"]:.8g}|{z["holdout"]["sample_worst_normalized_target_error"]:.5g}|{z.get("seconds_total",z["seconds"]):.4g}|{z.get("combined_spectrum_calls",z["budget"]["spectrum_calls"])}|{z["success"]}|')
lines+=['','最坏/容差>1表示至少某一教学目标未达；solver成功不改变这一结论。coarse_then_polish的时间/调用列包括两阶段。','', '## 追加精修（独立预算）','']
z=r['extra']['extended_precision_B03'];lines += [f'B03：{z["nfev_solver"]}主评估，{z["seconds"]:.4g}s，训练cost={z["cost"]:.8g}，1201点审计cost={z["holdout"]["cost"]:.8g}，最坏/容差={z["holdout"]["sample_worst_normalized_target_error"]:.5g}，optimality={z["optimality"]:.5g}；{z["message"]}。','', '## 有限全局参照','']
g=r['extra']['global_search'];lines += [f'六起点cost范围{min(z["cost"] for z in g["multistart"]):.9g}至{max(z["cost"] for z in g["multistart"]):.9g}；41×41枚举最小={g["grid"]["best_cost"]:.9g}；DE={g["DE"]["cost"]:.9g}，{g["DE"]["nfev"]}调用，success={g["DE"]["success"]}。这些不构成连续全局保证。','', '## 公差压力情景','', '|设计|64组均值cost|95%样本分位cost|最坏cost|','|---|---:|---:|---:|']
for name,z in r['extra']['robustness']['comparison'].items():lines.append(f'|{name}|{z["mean_cost"]:.7g}|{z["quantile95_cost"]:.7g}|{z["max_cost"]:.7g}|')
lines += ['','情景分布未测量，不得写成良率。','', '## 结构/最坏值/多目标','']
z=r['extra']['needle'];lines += [f'needle 原cost={z["base_cost"]:.8g}；最好的30nm有限候选={z["chosen"]["finite_30nm_cost"]:.8g}；约束精修={z["refined"]["cost"]:.8g}；accepted={z["accepted"]}。原值为81点，精修值31点；结构接受以相同601点审计比较。']
z=e['finite_minimax']['result'];lines += [f'有限minimax：t={z["t"]:.8g}，训练点数{z["points"]}，约束违例={z["constraint_violation"]:.3g}，独立审计最坏={z["holdout"]["sample_worst_normalized_target_error"]:.8g}；未证连续上界。','', '|吸收权重|平均R|平均A|平均T|','|---:|---:|---:|---:|']
for z in e['reflection_absorption_tradeoff']:lines.append(f'|{z["absorption_weight"]}|{z["audit_R_mean"]:.8g}|{z["audit_A_mean"]:.8g}|{z["audit_T_mean"]:.8g}|')
lines+=['','## 资源与复现','',f'主实验总墙钟{r["elapsed_seconds"]:.3f}s；Linux进程RSS峰值{r["peak_process_rss_kib_linux"]}KiB（含解释器/库/数据，不是单核独占内存）。核性能7次测时及Python跟踪分配峰值见JSON。环境NumPy{r["environment"]["numpy"]}、SciPy{r["environment"]["scipy"]}；CPU单进程线程设置见JSON。','', '完整层表、每band/AOI/p指标、所有预算和状态：[benchmark_results](../data/benchmark_results.json)；扩展：[extension_results](../data/extension_results.json)']
(ROOT/'reports/09a_generated_results.md').write_text('\n'.join(lines)+'\n')
print('4 SVGs + 4 PNG previews + generated results')
