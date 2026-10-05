"""Complete-input result, raw-layer audit, measured blocker and read-only freeze."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent


def layer_audit(direct,periodic):
    out=[]
    for d,p in zip(direct['step_results'],periodic['step_results']):
        out.append({'layer':d['step_index'],'physical_duration_s':d['duration_s'],
            'direct_mean_raw':d['mean_raw'],'periodic_mean_raw':p['mean_raw'],
            'mean_raw_relative_difference_percent':abs(p['mean_raw']/d['mean_raw']-1)*100,
            'direct_scale_nm':d['scale_nm'],'periodic_scale_nm':p['scale_nm'],
            'scale_relative_difference_percent':abs(p['scale_nm']/d['scale_nm']-1)*100,
            'unweighted_layer_cv_change_pp':abs(p['cv_percent']-d['cv_percent']),
            'direct_initial_phases_deg':[d['effective_settings']['carrier_phase_deg'],d['effective_settings']['planet_phase_deg']],
            'periodic_layer_initial_phases_deg':[p['effective_settings']['carrier_phase_deg'],p['effective_settings']['planet_phase_deg']],
            'physical_duration_preserved':p['duration_s']==d['duration_s'],
            'finite_periodic':p['finite_periodic_integration']})
    return out


def main():
    p=json.loads((HERE/'convergence_results.json').read_text());selected=json.loads((HERE/'selected_input_manifest.json').read_text())
    repeated=json.loads((HERE/'pilot_repeat_accounting.json').read_text())
    effects=p['checks']['effect_probe'];tau=p['checks']['tolerance_pp'];cv_tau=.1*effects['cv_change_pp']
    pairs=[('direct_0025_g21','periodic_0025_g21'),('direct_0025_g21_probe','periodic_0025_g21_probe'),
           ('direct_00125_g21','periodic_00125_g21'),('direct_00125_g21_probe','periodic_00125_g21_probe')]
    raw={a+'__'+b:layer_audit(p['results'][a],p['results'][b]) for a,b in pairs if a in p['results'] and b in p['results']}
    (HERE/'layer_raw_and_scale_audit.json').write_text(json.dumps(raw,indent=2)+'\n')
    supplement={'shape_tolerance_pp':tau,'cv_effect_pp':effects['cv_change_pp'],'additional_cv_sensitivity_tolerance_pp':cv_tau,
        'shape_tolerance_does_not_resolve_cv_objective_gap':True,
        'combined_resolution_direct_agreement_screen':'not_run_and_unresolved',
        'grid_source_agreement_cannot_transfer_from_grid21':'Not authorized for certification without explicit combined-resolution verification',
        'fresh_optimization_allowed':False,'engineering_ranking_allowed':False,
        'direct_time_cv_secondary_checks':{k:{'change_pp':p['checks'][k]['cv_change_pp'],
            'additional_cv_sensitivity_pass':p['checks'][k]['cv_change_pp']<cv_tau}
            for k in ('time_direct_0025_to_00125','time_direct_0025_to_00125_probe')},
        'status':'bounded_complete_process_numeric_blocker'}
    (HERE/'review_gate_supplement.json').write_text(json.dumps(supplement,indent=2)+'\n')
    fine=p['results']['direct_00125_g21']['wall_s']
    costs=[{'setting':'grid21,direct,dt=.00625s','per_case_estimated_s':fine*2,'two_case_estimated_s':fine*4,'actual_dt_s':.00625,'status':'not_run'},
           {'setting':'grid61,direct,dt=.0125s,unchanged source sampling','per_case_estimated_s':fine*(61/21)**2,'two_case_estimated_s':fine*(61/21)**2*2,'actual_dt_s':.0125,'status':'not_run'},
           {'setting':'native grid300,direct,dt=.0125s,unchanged source sampling','per_case_estimated_s':fine*(300/21)**2,'two_case_estimated_s':fine*(300/21)**2*2,'actual_dt_s':.0125,'status':'not_run'}]
    (HERE/'next_measured_costs.json').write_text(json.dumps({'costs':costs,'remaining_stage_allowance_s':p['config']['main_soft_wall_allowance_s']-p['wall_s'],
        'basis':'Complete-process measured .0125 grid21; linear-time/square-grid planning extrapolation only, not benchmark or permission to execute'},indent=2)+'\n')
    lines=['# 完整工艺数值检查：小效应分辨率尚未建立','',
        '2026-10-05 UTC · 原始恢复队列输入 · 全部膜层完整运行 · 不做工程排名','',
        '## 结论','',
        '完成了原输入全部10888.888889秒、两层7000 nm工艺的直接CPU积分，没有抽取12秒片段、缩短层时长或丢弃尾段。实际步长全部≤0.05秒，但细化到约0.0125秒后，完整厚度图变化仍大于预设效应尺度。既有保留尾段的finite-periodic积分也未通过与完整直接积分的地图一致性判据，因此不能靠其速度开启空间/源认证或新名义/稳健搜索。','',
        f"固定10-mm源位探针的归一厚度图效应为{effects['normalized_field_rms_pp']:.8f}百分点RMS，预设形状容差为其10%：{tau:.9f}百分点。直接0.025→0.0125秒，基线/探针图差为0.02774553/0.02734417百分点RMS；finite-periodic在0.0125秒与直接图差为0.00764377/0.00790871，均超过形状容差。",'',
        '这是严格的小效应可分辨性筛查，绝不是已批准的生产公差或实际生产不合格判断。没有新优化、没有选出工程赢家；产品、本地稳定性任务和历史研究文件均未修改。','',
        '## 所选完整输入与依赖闭合','',
        f"恢复文件：{selected['recovered_file']}",
        f"文件SHA-256：{selected['recovered_file_sha256']}",
        f"工艺canonical SHA-256：{selected['process_canonical_sha256']}",
        '7条依赖记录全部经原runtime_from_snapshot校验canonical_json_bytes SHA，并按原顺序解析机器、基片、两源和两板；原目录btbf文件缺失的板2不靠临时猜板补齐，而用已恢复的原队列完整图。','',
        '|层|目标nm|速率nm/s|完整时长s|源|板位|','|---|---:|---:|---:|---|---|',
        '|1|3500|0.5|7000|1|0|','|2|3500|0.9|3888.888888889|2|1|',
        '|合计|7000|按层原速率|10888.888888889|原顺序|原选择|','',
        '机器R_orbit312 mm、H1000 mm、120:36齿数、15 rpm、初相位0°，平面圆基片半径150 mm。源1=(200,−90,0) mm，半径20-mm圆盘、n=0、12旧环节点；源2=(−200,−90,0) mm，50×70-mm矩形、n=1、16节点。两个原5顶点板在800 mm，逐层各选一个。层2从真实已过7000秒的相位开始：载盘0°、行星约120°。','',
        '这是实际恢复的队列配置，不等于经过仪器校准或生产资格审查。其源数据仍含默认演示/未校准说明。完整示例、软件回归和60层文件另列inventory，未冒充本次实机或替换此长工艺。','',
        '自由文本元数据有历史滞后：机器description写48/48齿、240-mm轨道且notes写无板，但validated numeric fields实际为120/36、312 mm、原mask0/mask1。本研究执行numeric/canonical输入，不用描述文字覆盖它们；源description仍有“演示点源”等旧标签，实际源kind是disk/rectangle。这些文字一并保留，不当作经过测量的设备参数。','',
        '## 实际秒数和节点核验','',
        '|请求上限s|总节点数|层1实际Δt s|层2实际Δt s|','|---|---:|---:|---:|']
    for dt,plan in selected['sampling_plans'].items():
        lines.append(f"|{dt}|{plan['time_steps']}|{plan['step_time_step_s'][0]:.12f}|{plan['step_time_step_s'][1]:.12f}|")
    lines+=['','0.0125请求下原全局分配会让层2略超过0.0125秒，本驱动只向上增加总节点到871113，逐层实际步长均不过请求上限；不以全局平均掩盖层内超限。所有原CPU核批次进度与完整节点序列核对，没有尾批截断或隐藏采样上限。原恢复任务435558节点作为历史设置保留；本研究按新请求重新计算435556等采样总数，不改原任务。','',
        '## 原样正向与周期语义','',
        '完整process_simulator、归一化到原目标的位置定义、层间真实相位、source_samples、遮挡与CPU核原样复用。只在研究进程内把会写backend-memory的公共simulate依赖替换为同一CPU积分核加审计，结束即恢复模块引用；没有产品源文件或设置写入。','',
        '采用现有finite_periodic，绝不采用忽略残余的fast_cycle近似。12秒回归周期下，层1=583×12+4秒，层2=324×12+0.888888889秒；raw积分先加whole cycles和真实相位tail，再按每层原目标缩放。缓存只活在单次完整评价，源/板/速率身份和尾相位仍分开。','',
        '分段周期求积的节点网格不同于完整直接中点网格，特别是层2起始相位及非整数周期时长。因此物理分解保留时长，不等于离散结果自动等价。即使CV很接近，地图RMS仍可不合格，不能拿小标量差当作周期替代的数值证明。','',
        '应分开理解三件事：时间步长加密稳定性；正确whole-period+actual-tail的物理分解；已批准的工程容差。正确保留尾段时层数多不必然导致分解误差；duration小于一个回归周期时现实现直接回退完整积分，采样相同即没有周期替代误差。这里比较到的是不同求积网格的离散差，不把它报警为生产失效。','',
        f"在7000-nm参考标度上，0.00764377–0.00790871百分点的归一形状RMS约等效0.535–0.554 nm；形状筛查{tau:.9f}百分点约等效{tau*7000/100:.3f}nm。这是同一参考厚度上的相对形状尺度转换，不是经仪器测得的绝对膜厚误差；允许生产偏差目前unknown。",'',
        '## 所有实际完整评价','',
        '|评价|模式|实际完整时长s|请求Δt s|面积CV %|内部135-mm CV %|core调用|墙钟s|','|---|---|---:|---:|---:|---:|---:|---:|']
    pilot=json.loads((HERE/'pilot_direct_005_g21.json').read_text())
    allrows={'pilot_direct_005_g21':pilot,**p['results']}
    csv=['name,mode,duration_s,requested_dt_s,grid,probe,cv_percent,interior135_cv_percent,core_calls,wall_s,engineering_rank_allowed']
    for name,r in allrows.items():
        lines.append(f"|{name}|{r['mode']}|{r['total_duration_s']:.9f}|{r['requested_dt_s']}|{r['metrics']['cv_percent']:.8f}|{r['metrics']['interior135_cv_percent']:.8f}|{r['core_calls']}|{r['wall_s']:.3f}|")
        csv.append(','.join(map(str,[name,r['mode'],r['total_duration_s'],r['requested_dt_s'],r['grid'],r['probe'],r['metrics']['cv_percent'],r['metrics']['interior135_cv_percent'],r['core_calls'],r['wall_s'],False])))
    (HERE/'summary.csv').write_text('\n'.join(csv)+'\n')
    lines+=['','## 分层raw和缩放审计','',
        'layer_raw_and_scale_audit.json另列各层mean_raw、scale_nm、层CV与起始相位直接/周期差。原mean目标会强制各层网格算术均值为3500 nm；单看总厚度7000 nm或归一总图可能藏住raw错误，故不把目标归一当成物理正确性的证据。raw相对差很小仍不替代地图RMS门槛。','',
        '|对照|层|raw均值相对差 %|scale相对差 %|层CV差百分点|','|---|---|---:|---:|---:|']
    for pair,rows in raw.items():
        for row in rows:lines.append(f"|{pair}|{row['layer']}|{row['mean_raw_relative_difference_percent']:.9f}|{row['scale_relative_difference_percent']:.9f}|{row['unweighted_layer_cv_change_pp']:.9f}|")
    lines+=['','## 门槛的适用对象与未运行项','',
        f"形状门槛{tau:.9f}百分点是10%地图RMS效应；源位探针本身的CV差只有{effects['cv_change_pp']:.9f}百分点，不能拿较大的形状门槛宣称CV敏感性已解决。额外、更严格的CV敏感性诊断门槛为{cv_tau:.9f}百分点，直接0.025→0.0125的基线/探针CV变化也未过它。这一补充不偷偷修改原预设形状判据。未来名义/稳健排名须针对真实待比较目标差重新建立误差分辨率。",'',
        '时间screen：failed；周期/直接地图一致性：failed。空间和有限源独立加密：not_run，因为周期加速替代尚未放行。最大grid/source/time组合与完整直接的一致性：not_run，不从grid21旧12/16节点经验外推。135-mm内部ROI覆盖约100%，完整盘内中心单元覆盖97.52%；内部图差也超限，所以问题不只是边缘面积缺失。','',
        '## 实测资源阻断与下一步','',
        f"主阶段{p['main_actual_core_calls']}次实际CPU核调用，{p['wall_s']:.2f}秒；两个完整pilot都计费，合计{repeated['total_actual_pilot_core_calls']}调用、{repeated['first_complete_wall_s']+repeated['second_complete_wall_s']:.2f}秒。总研究实际调用32次，未把缓存/周期分段调用藏成单个评价。6项小合同测试只注入恒定场，共10个模拟核调用，未执行新物理benchmark。",'',
        f"阶段600秒余量约{p['config']['main_soft_wall_allowance_s']-p['wall_s']:.1f}秒。按完整0.0125基线{fine:.2f}秒测得的工作量，下一档不是免费："]
    for c in costs:lines.append(f"- {c['setting']}：每例约{c['per_case_estimated_s']:.1f}秒，两例约{c['two_case_estimated_s']:.1f}秒，not_run")
    lines+=['','进一步完整0.00625两例约509秒，超过第一检查点的规划余量；这不是用户禁止继续或必须重取授权。已依照后续明确继续指令，在continued_00625新阶段完整运行同一两例，保留本检查点。grid61直接每例约1074秒是实测外推的时间成本，仍不得通过截短工艺或加粗时间来替代。上述不声称真实设备加速比；在数值证据出现前不自动转为工程搜索。','',
        '所有旧研究文件、恢复输入文件及103份canonical Python前后哈希一致。新文件只在full_process_followup。没有访问/修改用户本地任务，没有GitHub动作，没有改变产品算法预算、默认上限、层数、真实时长或几何。','']
    (HERE/'RESULTS.md').write_text('\n'.join(lines))
    files={str(f.relative_to(HERE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(HERE.rglob('*')) if f.is_file() and f.name!='artifact_manifest.json' and '__pycache__' not in f.parts and (len(f.relative_to(HERE).parts)==1 or f.relative_to(HERE).parts[0]=='docs') and f.suffix!='.zip'}
    (HERE/'artifact_manifest.json').write_text(json.dumps({'files':files,'count':len(files)},indent=2)+'\n')
    print(json.dumps({'status':p['status'],'fresh_optimization_allowed':False,'engineering_ranking_allowed':False,
        'main_actual_calls':p['main_actual_core_calls'],'pilot_actual_calls':repeated['total_actual_pilot_core_calls'],'files_hashed':len(files)},indent=2))


if __name__=='__main__':main()
