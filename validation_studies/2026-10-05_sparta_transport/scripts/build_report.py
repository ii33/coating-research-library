#!/usr/bin/env python3
"""Build an offline engineering report directly from frozen read-back data."""
from pathlib import Path
import html, io, json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import study

R=study.ROOT
s=json.loads((R/'results/validation_summary.json').read_text());p=json.loads((R/'provenance/source_build.json').read_text())
r=s['case_results'];inj=r['injection'];base=r['geometry_base'];fine=r['geometry_weight_quarter'];thermal=r['bath_thermal'];rep=s['replication_uncertainty']
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
tau=np.linspace(0,3.1,300);axes[0].plot(tau,np.exp(-tau),color='#323d56',label='Analytic exp(-tau)')
for t,key in [(.01,'bath_static_tau001'),(.1,'bath_static_tau01'),(1,'bath_static_tau1'),(3,'bath_static_tau3')]:
    q=r[key];lo,hi=q['confidence_interval_95'];axes[0].errorbar([t],[q['uncollided_fraction']],yerr=[[q['uncollided_fraction']-lo],[hi-q['uncollided_fraction']]],fmt='o',color='#19726b',capsize=4)
axes[0].set(xlabel='Synthetic cold-target optical depth',ylabel='Never-collided tracer fraction',title='Real SPARTA histories and analytic survival');axes[0].legend()
names=['geometry_base','geometry_dt_half','geometry_dt_quarter','geometry_weight_half','geometry_weight_quarter','geometry_surface2','geometry_surface4'];labels=['Base','dt / 2','dt / 4','weight / 2','weight / 4','surface x2','surface x4']
for i,key in enumerate(names):
    q=r[key];lo,hi=q['confidence_interval_95'];axes[1].errorbar([i],[q['capture_fraction']],yerr=[[q['capture_fraction']-lo],[hi-q['capture_fraction']]],fmt='o',color='#19726b',capsize=4)
axes[1].axhline(base['reference_capture_fraction'],color='#323d56',linestyle='--',label='Finite-square deterministic reference');axes[1].set(xticks=range(len(labels)),xticklabels=labels,ylabel='Receiver capture / emitted',title='Finite thermal source geometry checks');axes[1].tick_params(axis='x',rotation=25);axes[1].legend(fontsize=8)
out=io.StringIO();fig.savefig(out,format='svg');fig.savefig(R/'docs'/'numerical_checks.png',dpi=150);svg=out.getvalue()[out.getvalue().find('<svg'):];plt.close(fig)
rows=''
for label,key in [('自然通量发射及捕获','geometry_physical_flux'),('几何基线','geometry_base'),('几何粒子权重四分之一','geometry_weight_quarter'),('静止极限 τ=0.01','bath_static_tau001'),('静止极限 τ=0.1','bath_static_tau01'),('静止极限 τ=1','bath_static_tau1'),('静止极限 τ=3','bath_static_tau3'),('热背景 相对速度','bath_thermal')]:
    q=r[key];v=q.get('capture_fraction',q.get('uncollided_fraction'));expected=q.get('reference_capture_fraction',q.get('expected_fraction'));ci=q['confidence_interval_95']
    rows+=f'<tr><td>{label}</td><td>{v:.6f}</td><td>{expected:.6f}</td><td>{ci[0]:.6f} 至 {ci[1]:.6f}</td><td>{q["z_error"]:.2f}</td></tr>'
conv=''
for c in s['convergence']:
    diffs=c['two_refinements'];conv+=f'<tr><td>{c["group"]}</td><td>{diffs[0]["difference_absolute_fraction"]:.6f}</td><td>{diffs[1]["difference_absolute_fraction"]:.6f}</td><td>统计分辨率内一致</td></tr>'
links=''.join(f'<li><a href="{html.escape(u)}">{html.escape(u.split("/")[-1])}</a></li>' for u in p['documentation_URLs'])
diagram='''<svg viewBox="0 0 860 240" role="img" aria-label="Parallel source and receiver with side escape and inventory">
<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#19726b"/></marker></defs>
<line x1="70" y1="196" x2="770" y2="196" stroke="#7d8595" stroke-width="3"/><line x1="70" y1="40" x2="770" y2="40" stroke="#7d8595" stroke-width="3"/>
<line x1="386" y1="196" x2="454" y2="196" stroke="#19726b" stroke-width="9"/><line x1="280" y1="40" x2="560" y2="40" stroke="#19726b" stroke-width="9"/>
<path d="M420,190 L455,48 M420,190 L610,48 M420,190 L773,122" stroke="#19726b" fill="none" stroke-width="2" marker-end="url(#arrow)"/>
<line x1="135" y1="192" x2="135" y2="44" stroke="#323d56" stroke-width="2"/><text x="77" y="121" font-size="17">H=0.1 m</text><text x="355" y="227" font-size="17">source 0.02 x 0.02 m</text><text x="335" y="26" font-size="17">receiver 0.1 x 0.1 m</text><text x="595" y="66" font-size="15">top outside receiver = loss</text><text x="620" y="147" font-size="15">side open exit</text><text x="276" y="125" font-size="17">inventory</text><text x="70" y="227" font-size="15">x limits +/-0.2 m</text>
</svg>'''
body=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SPARTA 输运数值验证 2026 10 05</title>
<style>body{{font:17px/1.65 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif;color:#17212e;max-width:1100px;margin:48px auto;padding:0 26px;background:#fff}}h1{{font-size:34px;line-height:1.2;color:#000}}h2{{font-size:24px;margin-top:42px;color:#000}}h3{{font-size:19px;margin-top:25px;color:#000}}p,li{{max-width:1000px}}table{{border-collapse:collapse;width:100%;font-size:15px;margin:20px 0}}th,td{{border:1px solid #d9d9d9;padding:10px 13px;text-align:left;vertical-align:middle}}th{{background:#e8edf3}}tr:nth-child(even){{background:#f8fafb}}a{{color:#176b73}}code,pre{{font:14px/1.6 ui-monospace,monospace}}pre{{white-space:pre-wrap;background:#f5f7f9;padding:18px;overflow-wrap:anywhere}}svg{{max-width:100%;height:auto}}.meta{{color:#546070;font-size:15px}}.formula{{font-family:ui-monospace,monospace;background:#f5f7f9;padding:16px;overflow-wrap:anywhere}}@media(max-width:700px){{body{{margin:25px auto}}table{{font-size:12px}}td,th{{padding:7px}}h1{{font-size:27px}}}}</style>
<h1>SPARTA 输运数值验证</h1><p class="meta">2026年10月5日 UTC · 真实 SPARTA 串行 CPU · 合成方法验证 · 官方提交 {p['pinned_commit'][:12]}</p>
<p><strong>结论：</strong>实际构建并运行官方 SPARTA，完成 {s['case_count']} 个有界案例。热表面注入、自由分子有限源几何、恒密度背景中的零碰撞生存比例均与相应参考在本次蒙特卡洛分辨率内一致。所有几何案例的粒子账严格闭合。没有验证真实设备散射沉积、双修正板或行星运动，也没有可靠真实材料与背景气碰撞截面。</p>
<p>现有 cub415635 内核与本地用户工程只读。Python 负责生成输入、确定性求积和结果检查；所有粒子轨迹及碰撞均来自未经修改的官方 SPARTA，不含自行实现后冒称 SPARTA 的蒙特卡洛输运器。</p>
<h2>实际结果</h2><table><thead><tr><th>检查</th><th>实测比例</th><th>参考比例</th><th>单次 95% 区间</th><th>标准误差倍数</th></tr></thead><tbody>{rows}</tbody></table>
<p>几何粒子采用精确二项区间；DSMC 生存比例的单次二项区间只是在近似独立历史假设下的统计摘要。共享背景和重复碰撞可能带来相关性，因此另外运行了五个独立种子，不能把单次区间当作严格 DSMC 误差保证。</p>
<p>静止背景五次均值 {rep['static']['mean_uncollided_fraction']:.5f}，基于独立运行均值的 Student t 95% 区间 [{rep['static']['student_t_95_interval'][0]:.5f}, {rep['static']['student_t_95_interval'][1]:.5f}]，解析值 0.904837。热背景五次均值 {rep['thermal']['mean_uncollided_fraction']:.5f}，区间 [{rep['thermal']['student_t_95_interval'][0]:.5f}, {rep['thermal']['student_t_95_interval'][1]:.5f}]，参考值 0.831185。五次重复仍不足以精确确定方差。</p>
{svg}
<h2>热表面注入的独立验证</h2><p>合成惰性原子质量 m=6.63×10⁻²⁶ kg，温度 T=300 K，漂移速度为零。只发射一个时间步 dt=10⁻¹² s，在任何可见逃逸前读取全部 50,000 个粒子，避免驻留时间与接收方向的选择偏差。</p>
<div class="formula">c=√(2kBT/m)<br>p(vx,vy,vz)=2vz/(πc⁴) exp[−(vx²+vy²+vz²)/c²], vz&gt;0<br>p(μ)=2μ，μ=cosθ；CDF(μ)=μ²；E[μ]=2/3<br>q=mv²/(2kBT) 服从 Gamma(shape=2,scale=1)，E[q]=2</div>
<p>当前冻结输出：平均 μ={inj['mu_mean']:.6f}；角度 KS p={inj['mu_ks_p']:.4f}；平均 E/kT={inj['energy_over_kT_mean']:.6f}；能量 KS p={inj['energy_ks_p']:.4f}；方位角 KS p={inj['azimuth_ks_p']:.4f}；方向与能量相关系数 {inj['energy_mu_correlation']:.5f}。注入粒子数与最终库存均为 50,000，逃逸为零。</p>
<p>这是零漂移热发射的 Lambert 极限，不能任意指定 cosⁿ 指数。核查上游源码发现法向采样的无量纲热偏差限于 3，对零漂移省略约 exp(−9)=0.0001234 的理想法向尾部；其比例小于本次统计分辨率，仍作为已知采样近似保留。</p>
<p>另外运行没有 n 调试覆盖的自然通量模式：nrho=5×10¹⁸ m⁻³，J=nrho√(kBT/(2πm))。500 步理论模拟粒子数 99,713.8696，实际 99,717；自然通量模式也通过捕获比例及粒子平衡检查。</p>
<h2>自由分子有限源几何</h2>{diagram}
<p>全部长度为 m，坐标系为笛卡尔：均匀方形源位于 z=0，x,y∈[−0.01,0.01]，外法向 +z；接收方形位于 z=0.1，x,y∈[−0.05,0.05]，法向 −z。侧边 x,y=±0.2 为开放出口；上表面接收区域之外视为损失。源和上平面使用共享边的三角片，维持精确边界。</p>
<div class="formula">F=H²/(πAs) ∫As∫Ar [H²+(xr−xs)²+(yr−ys)²]⁻² dAr dAs<br>F_reference=0.2376441865228383<br>N_emit=N_receiver+N_other_surface+N_open_exit+ΔN_inventory</div>
<p>参考是确定性四维 Gauss–Legendre 求积，不是随机射线。12、24、40阶结果一致到约 2×10⁻¹⁵；独立二维卷积形式也得到同一数值。该核已含源余弦与接收投影，不能再重复乘源余弦。平面网格本身几何精确，表面细化检验的是离散执行的一致性。</p>
<p>基线发射 {base['emitted']:,}，接收 {base['capture']:,}，其他表面损失 {base['other_surface_loss']:,}，开放出口 {base['open_boundary_escape']:,}，剩余库存 {base['inventory_final']}。所有 12 个几何案例账差均为零。四分之一粒子权重使用 400,000 个发射粒子，捕获比例 {fine['capture_fraction']:.5f}，相对确定性参考误差 {fine['relative_error']*100:.4f}%。</p>
<h2>合成均匀背景与真实碰撞历史</h2><p>周期盒 0.01×0.002×0.002 m，背景数密度约 10²⁰ m⁻³，固定总数与体积，不使用漏空的开放气库。t=0 创建 5,000 个近单速示踪粒子，之后不再出生、不反应、不克隆。所有时间步均输出 gas/collision/tally，初始示踪 ID 唯一，末态 ID 集完全相同，事件中的示踪 ID 是初始集合的子集，事件总数与全局碰撞计数一致。</p>
<p>VSS 参数 ω=0.5、α=1 给出硬球极限。异种截面逐对显式指定 σ=τ/(nrhoL)，τ取 0.01、0.1、1、3。两个同种直径取 10⁻²⁵ m 以使同种碰撞可以忽略；这些数字只是合成算例，并无材料证据。</p>
<div class="formula">静止均匀背景：P0(t)=exp(−nrho σ v t)，t=L/v，故 P0=exp(−τ)<br>热背景：cg=√(2kBTg/mg)，s=v/cg<br>⟨g⟩=cg{{exp(−s²)/√π+[s+1/(2s)]erf(s)}}<br>P0=exp[−nrho σ ⟨g⟩ t]</div>
<p>静止目标用非常重且冷的背景极限：mg=6.63×10⁻²⁰ kg，Tg=10⁻¹⁰ K，v=1,000 m/s。背景温度因受碰撞而略增，但最终速度仍远小于示踪速度；这不宣称数学上精确 T=0。热背景使用同样重的合成靶、Tg=3×10⁸ K，使热速度尺度等于普通质量在300K时的尺度，并将反馈降到微小量。这种“热且重”的合成设置不是实际设备温度。</p>
<p>热背景示踪速度 250 m/s，相对速度因子 ⟨g⟩/v={thermal['relative_speed_factor']:.6f}，所以参考为 {thermal['expected_fraction']:.6f}，不能套静止靶 exp(−0.1)=0.904837。背景总粒子数前后严格相同；热背景温度相对变化小于 10⁻⁶。碰撞混合物 4,800 K 只用于初始化足够大的 Vremax majorant，不代表实际创建的背景或示踪温度。</p>
<p>输出按粒子累计 0、1、2、… 次碰撞的直方图。τ=3 案例真实记录 {r['bath_static_tau3']['collisions_total']:,} 次碰撞。这里的指标是固定时间的未碰撞生存比例；它不是有限接收面的直达沉积，也不是总散射沉积。有限接收面需要按每条实际路径长 R 加权 exp(−nrhoσR)，不能只用垂直距离 H。</p>
<h2>有界细化与验收边界</h2><table><thead><tr><th>细化项</th><th>第一级比例变化</th><th>第二级比例变化</th><th>本轮结论</th></tr></thead><tbody>{conv}</tbody></table>
<p>几何网格为10×10×5、20×20×10、40×40×20；dt为10、5、2.5 µs；粒子权重为10¹⁰、5×10⁹、2.5×10⁹；每个基础三角区域作1、2、4倍边细分。背景网格x为10、20、40，y,z各2；dt为100、50、25 ns；粒子权重为10⁸、5×10⁷、2.5×10⁷，分别约40k、80k、160k背景粒子。</p>
<p>本次方法检查约定：注入 KS p&gt;0.001；几何误差在1%相对参考或4倍近似统计标准误差的较宽者以内；逐账严格相等；生存误差在4倍近似标准误差以内；两个连续细化级差还应分别低于几何0.01、背景0.02的绝对比例预算且在4倍合并标准误差以内。这些是公开的本次方法测试约定，不是用户认可的工艺验收标准。它证明统计分辨率内的细化一致性，不证明所有输出已达到确定性的1%准确度。</p>
<h2>失败证据与修正</h2><ol><li>emit/surf 配合 surf/collision/tally 覆盖发射面，会向 tally 传递空的入射指针，而该上游 tally 会解引用它。第一次真实运行段错误。后续把发射面排除。</li><li>vanish 的上游实现未设置 reaction 标志，而且 collision/tally 的 id/type 分支访问已经消失的 ip。初次到达事件数不完整，不能据此计算沉积。最终改用官方 specular 加 surf_react global 1 0，再用 surf/reaction/tally 完整统计删除事件；这只是完美吸收边界，不代表真实化学。上游源码始终未改。</li><li>初始 majorant 太低时，细网格背景案例零碰撞比例超出4σ，保留未通过结果。将碰撞混合物初始化温度设为4,800K后重新执行全部背景组，实际创建的粒子温度仍由各自 mixture 决定。</li><li>最初普通质量热浴被示踪脉冲加热，不能冒称受维持的热背景；该结果保留，改为重靶合成极限并重新执行。所有失败尝试位于 results/failed_attempts，不混入通过摘要。</li></ol>
<h2>版本与复现</h2><p>官方版本 {html.escape(p['version_header'])}；提交 <a href="{p['pinned_commit_URL']}">{p['pinned_commit']}</a>；GNU GPL v2许可文本已保留。编译器 {html.escape(p['compiler'])}，Python {p['python']}，NumPy {p['numpy']}，SciPy {p['scipy']}。串行 make 使用自带 MPI STUBS，没有 GPU、外部 MPI 或 CMake，没有全局安装或安全设置更改。最终38个案例实际求解 wall time合计约 {s['total_final_case_CPU_wall_seconds']:.2f} s；不包括编译、输出后处理和失败尝试。</p>
<pre>git clone https://github.com/sparta/sparta.git vendor/sparta
git -C vendor/sparta checkout {p['pinned_commit']}
make -C vendor/sparta/src -j2 serial
python3 scripts/study.py --stage all
python3 scripts/check_results.py
python3 scripts/build_report.py</pre>
<p>每个 results/案例目录包含输入、合同、实际命令、退出状态、原始 SPARTA日志、逐事件输出和复核结果。汇总为 results/validation_summary.json，结果表为 results/comparison.csv。小型复现包保留输入、脚本、摘要和运行日志；体积较大的原始逐粒子输出与官方源码保存在完整研究目录。未在小包中分发 SPARTA 二进制。离线HTML完成结构校验与图表像素检查；完整浏览器预览因运行环境的socket权限被阻止，未宣称完成浏览器视觉验收。</p>
<h2>继续进入实际镀膜设备所需证据</h2><ul><li>真实蒸气物种、背景气体组成、能量域内的总截面与角散射数据及出处</li><li>实际有限源、双板和行星位姿的单位与坐标映射</li><li>壁面捕获、反射、再蒸发规则，以及真实稳态气体维持边界</li><li>已知坐标的QCM与基片观测，对直达和总沉积分别验证</li></ul><p>这些阶段尚未运行，本包不会替换现有快核，也不会生成加工或生产合格保证。</p>
<h2>官方参考</h2><ul>{links}</ul><p>几何参考与误差界为本研究独立推导；SPARTA 指令语义以以上官方文档和固定提交源码为依据。</p></html>'''
(R/'docs'/'transport_validation.html').write_text(body)
(R/'README.md').write_text(f'''# SPARTA 输运验证 2026-10-05

真实官方 SPARTA 27 Aug 2026 已构建并执行，38 个有界方法案例通过本次检查。
这是合成方法验证，不是实机散射、双板/行星几何或真实材料预测。

先打开 `docs/transport_validation.html`：离线单文件，含公式、坐标图、曲线、全部限制与官方来源。

## 主要结果

- 有限方形源几何参考 0.2376441865；SPARTA 400k发射时为0.23743
- 12个几何案例的发射、接收、表面损失、出口与库存账差均为零
- 热表面源角/能量/方位分布单独验证；自然nrho通量发射实际99717，理论99713.8696
- 恒密度周期背景中读取每步真实碰撞历史，校验示踪ID唯一/守恒/集合成员与全局事件数
- 静止τ=.1五次均值0.90676；解析0.904837；热相对速度五次均值0.83272；解析0.831185
- 网格、时间步、权重均检查两个细化级；统计分辨率限制仍明确保留

## 复现

官方固定提交：{p['pinned_commit']}。
`vendor/sparta/src/spa_serial` 为本目录内部编译，无全局安装。

```sh
make -C vendor/sparta/src -j2 serial
python3 scripts/study.py --stage all
python3 scripts/check_results.py
python3 scripts/build_report.py
```

## 证据入口

- `results/validation_summary.json`：冻结结果和状态
- `results/comparison.csv`：可排序的全部案例指标
- `results/*/input_contract.json`、`in.sparta`、`execution.json`：输入与真实执行
- `results/*/log.sparta`、`*.tally`、`pulse.dump`：原始读回
- `results/failed_attempts/`：上游tally/majorant/热浴反馈失败，不作成功结果
- `provenance/source_build.json`：版本、依赖、来源、命令与二进制hash
- `provenance/SPARTA_LICENSE.txt`：GPL v2许可

本研究仅写本目录；cub与本地工程不修改、没有提交或push。
''')
print(R/'docs'/'transport_validation.html')
