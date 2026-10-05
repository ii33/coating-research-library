"""Eligibility is separate from short-window numerical convergence and engineering."""
from pathlib import Path
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent
FIRST=HERE.parent


def screen(pairs):
    gaps=[b-a for a,b in pairs];threshold=.2*abs(gaps[-1])
    changes=[[abs(pairs[i][j]-pairs[i-1][j]) for i in (1,2)] for j in (0,1)]
    gchanges=[abs(gaps[i]-gaps[i-1]) for i in (1,2)]
    same_sign=all(gaps[i]*gaps[-1]>0 for i in (0,1))
    return {'passed':threshold>0 and same_sign and all(max(c)<threshold for c in changes) and max(gchanges)<threshold,
        'threshold_pp':threshold,'last_two_method_changes_pp':changes,'last_two_gap_changes_pp':gchanges,
        'stable_sign':same_sign,'gaps_pp':gaps,'interpretation':'Fixed-design short-window observed-change screen, not an error bound or engineering rank'}


def main():
    p=json.loads((HERE/'gate_results.json').read_text());first=json.loads((FIRST/'results/study_results.json').read_text())
    follow=json.loads((FIRST/'convergence_followup/followup_results.json').read_text())
    history=[]
    for stage,res in [('first-round training',first['config']['resolution']),('first-round refined holdout',first['config']['refined_resolution']),('first-round nominal refinement',first['config']['convergence_resolution'])]:
        history.append({'stage':stage,'duration_s':12.,'time_steps':res['time_steps'],'actual_dt_s':12./res['time_steps'],'time_step_eligible':12./res['time_steps']<=.05,'engineering_ranking_allowed':False})
    for key in follow['axis_keys']['time']:
        r=follow['levels'][key]['resolution'];history.append({'stage':'historical follow-up time ladder','duration_s':12.,'time_steps':r['time_steps'],'actual_dt_s':12./r['time_steps'],'time_step_eligible':12./r['time_steps']<=.05,'engineering_ranking_allowed':False})
    status={'user_time_step_ceiling_s':.05,'historical_time_steps':history,
        'new_time_step_gate_pass':True,'representative_full_process_gate_pass':False,
        'fair_fine_trained_optimization_comparison_pass':False,
        'joint_grid_source_convergence_pass':False,'calibrated_machine_validation_pass':False,
        'engineering_ranking_allowed':False,'short_window_screens':[]}
    for case in p['config']['cases']:
        rows=[next(c for c in l['cases'] if c['seed']==case['seed'] and c['level']==case['level']) for l in p['levels']]
        status['short_window_screens'].append({**case,**{domain:screen([(c['methods']['nominal'][metric],c['methods']['robust'][metric]) for c in rows])
            for domain,metric in [('full_disk','mean_cv_percent'),('interior90','mean_interior90_cv_percent')]}})
    (HERE/'gate_status.json').write_text(json.dumps(status,indent=2)+'\n')
    lines=['# 步长门禁：短窗诊断，不支持工程排名','',
        '2026-10-05 UTC。落实最新要求：用于工程参考的实际时间步长不得超过0.05秒。','',
        '## 结论','',
        '新检查实际步长0.05/0.025/0.0125秒全部通过门禁，原样cub核的批次进度确认分别完整处理240/480/960个节点，没有隐藏上限或尾批截断。门禁通过只说明时间步长符合要求。12秒合成窗、粗采样训练得到的固定设计、尚未收敛的空间/源采样和未校准模型仍阻止工程排名，不能据此宣布稳健算法更优或生产达标。','',
        '首轮训练0.125秒、加密留出0.0625秒都超过上限，保留为历史实现诊断，撤出工程比较依据。首轮61-grid名义核查0.03125秒及历史跟进384/768/1536节点满足时间门禁，但同样不代表完整工艺。','',
        '真实多层工艺的持续时间、膜层时长、跨层相位与速率变化没有在这个12秒窗中得到代表性验证。名义15rpm时12秒刚好是理想完整回归窗；扰动rpm时并非完整回归。这里一直使用原核的实际12秒积分，没有周期快算或把步长偷偷换成相位节点数。未来完整工艺/快算若获授权也必须分别记录实际积分窗与Δt，不能用节点数掩盖不合格步长。','',
        '## 历史时间步长重新分级','',
        '|记录|积分窗/秒|节点数|实际Δt/秒|仅时间门禁|工程排名|','|---|---:|---:|---:|---|---|']
    for h in history:lines.append(f"|{h['stage']}|12|{h['time_steps']}|{h['actual_dt_s']:.7f}|{'eligible' if h['time_step_eligible'] else 'excluded'}|blocked|")
    lines+=['','## 新的等步长检查','',
        '两个固定病例：1%/seed11、5%/seed29；两方法各用相同首轮前四个扰动，另存零扰动结果。没有重新训练、重选设计或挑新情景。grid41、5×5有限源不变，时间轴只改变Δt。以下为固定四情景均值诊断，不赋予工程排名；CV为%，差为百分点。','',
        '|实际Δt/秒|实际节点数|病例|原名义设计CV %|原稳健设计CV %|差/百分点|','|---|---:|---|---:|---:|---:|']
    csv=['actual_dt_s,actual_time_steps,level,seed,nominal_mean_cv_percent,robust_mean_cv_percent,gap_pp,engineering_ranking_allowed']
    for lev in p['levels']:
        for c in lev['cases']:
            a=c['methods']['nominal']['mean_cv_percent'];b=c['methods']['robust']['mean_cv_percent']
            lines.append(f"|{lev['actual_dt_s']:.4f}|{lev['actual_time_steps']}|{c['level']:.0%}/{c['seed']}|{a:.6f}|{b:.6f}|{b-a:+.6f}|")
            csv.append(','.join(map(str,[lev['actual_dt_s'],lev['actual_time_steps'],c['level'],c['seed'],a,b,b-a,False])))
    (HERE/'summary.csv').write_text('\n'.join(csv)+'\n')
    lines+=['','## 数值判据与继续边界','',
        '短窗数值判据只以当前合格步长的四情景方法差为尺度：最后两次两方法均值与方法差变化均小于当前差绝对值的20%，且三档差同号。旧0.0625秒留出结果不作为门禁后的数值阈值。相邻差仍非严格误差界。','']
    for s in status['short_window_screens']:
        lines.append(f"- {s['level']:.0%}/seed{s['seed']}：full-disk={'pass' if s['full_disk']['passed'] else 'unresolved'}；interior90={'pass' if s['interior90']['passed'] else 'unresolved'}。即使数值screen通过，工程排名仍blocked")
    lines+=['','设计曾在0.125秒的粗内核上训练，可能利用采样混叠。因此细步长重算只是已选候选诊断，不能冒充在合格步长公平训练的名义/稳健算法比较。后续真正性能比较须在代表完整工艺和合格步长上重新冻结训练/留出合同，分别收敛网格、时间和源，再用实测相关不确定度；本次不擅自扩成长工艺搜索。','',
        '## 历史审计补充','',
        'convergence_followup的phase pass是预先定义的“各方法均值极差+排名同号”，并没有对配对gap极差设硬门槛。5%/seed29、N768(0.015625秒)的gap原点极差0.00375454百分点超过full域阈值0.00303259；内部90mm也超过。这个额外更严格的gap诊断应记unresolved。N1536(0.0078125秒)的额外gap极差通过。历史数据和原预定pass不回写、不偷偷改变判据。','',
        '历史扩展到七项测试的普通导入失败：同名build_report.py被父目录模块遮蔽。原错误输出保留。此目录check_historical_math.py用显式文件定位与独立模块装载复算，七项数学/接线测试全通过，没有cub计算或历史文件修改。门禁另有五项单元检查，覆盖实际秒数、向上取整、非法步长拒绝、尾批完整性和不完整进度拒绝。','',
        '## 调用和完整性','',
        f"Pilot {p['pilot_actual_calls']} 次实际cub调用，主检查 {p['main_actual_calls']} 次，墙钟{p['wall_s']:.2f}秒；pilot外推{p['pilot_estimated_wall_s']:.2f}秒。每有效情景均有实际有板与无板参考两个调用，无缓存赠送。五个新单元检查和隔离历史数学复算只用注入场/数学，不额外执行cub。",'',
        '所有实际步数由原kernel进度回调验证；0.05秒档末尾16个节点、其他档32个节点完整计入。首轮、历史跟进与原产品Python SHA前后一致，全部新文件仅在engineeringgate。软件、原依赖、数据和GitHub未改变。','']
    (HERE/'RESULTS.md').write_text('\n'.join(lines))
    files={str(f.relative_to(HERE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(HERE.rglob('*')) if f.is_file() and f.name!='artifact_manifest.json' and '__pycache__' not in f.parts}
    (HERE/'artifact_manifest.json').write_text(json.dumps({'files':files,'count':len(files)},indent=2)+'\n')
    print(json.dumps({'new_time_step_gate_pass':True,'engineering_ranking_allowed':False,'short_window_screens':status['short_window_screens'],'files_hashed':len(files)},indent=2))


if __name__=='__main__':main()
