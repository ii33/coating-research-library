"""Freeze the completed numerical checkpoint; no forward evaluation or upload."""
from pathlib import Path
import hashlib
import json
import zipfile

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    initial = read("convergence_results.json")
    stage = read("continued_00625/stage_results.json")
    finer = read("continued_00625/periodic_finer/finer_results.json")
    mechanism = read("continued_00625/mechanism_results.json")
    branch = read("fast_cycle_branch_check/branch_results.json")
    spatial = read("spatial_source_diagnostics/diagnostic_results.json")
    aggregate = read("spatial_source_diagnostics/controlled_aggregate_results.json")
    pilot = read("spatial_source_diagnostics/pilot_plan.json")
    repeated = read("pilot_repeat_accounting.json")
    selected = read("selected_input_manifest.json")
    tau = stage["checks"]["retained_shape_tolerance_pp"]
    cv_tau = stage["checks"]["additional_cv_sensitivity_tolerance_pp"]
    time_checks = {k: v for k, v in stage["checks"].items() if k.startswith("time_")}
    periodic_checks = {k: v for k, v in stage["checks"].items() if k.startswith("periodic_")}
    shape_pass = lambda rows: all(max(r["normalized_field_rms_pp"], r["interior135_field_rms_pp"]) <= tau for r in rows.values())
    cv_pass = lambda rows: all(max(r["cv_change_pp"], r["interior135_cv_change_pp"]) <= cv_tau for r in rows.values())
    stages = [
        ("initial complete-process pilots, including repeated pilot", repeated["total_actual_pilot_core_calls"], repeated["first_complete_wall_s"] + repeated["second_complete_wall_s"]),
        ("initial convergence stage", initial["main_actual_core_calls"], initial["wall_s"]),
        ("complete direct .00625 and same-step finite-periodic", stage["actual_core_calls"], stage["wall_s"]),
        ("separate synthetic period/tail mechanism fixtures", mechanism["actual_core_calls"], mechanism["wall_s"]),
        ("finer finite-periodic checks", finer["actual_core_calls"], finer["wall_s"]),
        ("native fast-cycle-mean branch check", branch["actual_core_calls"], branch["wall_s"]),
        ("spatial/source complete-process pilot", pilot["pilot_actual_calls"], pilot["pilot_complete_wall_s"]),
        ("spatial/source diagnostics including saved-field resume", spatial["actual_core_calls"], spatial["wall_s"]),
    ]
    counts = [{"stage": n, "actual_core_calls": c, "wall_s": w} for n, c, w in stages]
    status = {
        "status": "bounded_checkpoint_frozen_no_further_precision_escalation",
        "complete_original_recipe_duration_s": selected["total_duration_s"],
        "layer_durations_s": selected["layer_durations_s"],
        "total_target_nm": 7000,
        "fixed_cases": ["original baseline", "source1 X+10 mm synthetic diagnostic probe"],
        "retained_shape_screen_pp": tau,
        "retained_shape_screen_equivalent_nm_at_7000": tau * 70,
        "supplemental_cv_sensitivity_screen_pp": cv_tau,
        "production_tolerance": "not specified; no production pass/fail inference",
        "time_stability_at_grid21_legacy_source": {"direct_refinement_s": [.0125, .00625], "shape_pass": shape_pass(time_checks), "cv_observed_change_pass": cv_pass(time_checks), "checks": time_checks},
        "same_step_finite_periodic_direct_agreement": {"requested_dt_s": .00625, "shape_pass": shape_pass(periodic_checks), "cv_observed_change_pass": cv_pass(periodic_checks), "checks": periodic_checks},
        "finer_periodic_reference": {"accepted_requested_dt_s": finer["accepted_periodic_dt_s_for_fixed_grid21_cases"], "screen_pass": finer["levels"][-1]["passed_fixed_grid21_screen"], "scope": "grid21, unchanged legacy12/16 source nodes, these two fixed cases only; mismatch plus observed direct-refinement change is an empirical screen, not a rigorous error bound"},
        "grid_aggregate_cv_screen_pass": False,
        "source_aggregate_cv_screen_pass": False,
        "joint_final_resolution_direct_agreement": "not run",
        "fresh_fine_trained_optimization": "not run",
        "engineering_ranking_allowed": False,
        "resource_accounting": {"stages": counts, "actual_core_calls": sum(x["actual_core_calls"] for x in counts), "stage_wall_s_sum": sum(x["wall_s"] for x in counts), "unit_tests_and_postprocessing_core_calls": 0},
        "failures": ["one spatial postprocessing error: grid41 and61 were incorrectly assumed nested; corrected to exact common gcd grid21 and reused saved fields without repeating forward calls", "historical follow-up test import shadowing is preserved; isolated7-test loader passed"],
        "stop_reason": "Requested checkpoint and handoff; engineering resolution target pending. No multi-hour joint run or additional quadrature ladder.",
    }
    write("CURRENT_STATUS.json", status)
    identity = {
        "product_commit": "415635cf3ec3ba6e65cfabbb90bef1e9940245fb",
        "recovered_file_sha256": selected["recovered_file_sha256"],
        "canonical_record_hashes": selected["snapshot_files"],
        "matching_uploaded_asset_graph": "All7 records semantically exact after restoring renamed internal references; independent graph inspection, not a new compute run",
        "numeric_geometry": {"substrate": "flat circular R150 mm at z1000 mm", "orbit_mm": 312, "sun_planet_teeth": [120, 36], "gear_module_mm": 4, "carrier_rpm": 15, "tilt_deg": 0, "initial_phases_deg": [0, 0], "sources": [{"xyz_mm": [200, -90, 0], "shape": "disk", "radius_mm": 20, "exponent": 0, "legacy_nodes": 12}, {"xyz_mm": [-200, -90, 0], "shape": "rectangle", "size_mm": [50, 70], "exponent": 1, "legacy_nodes": 16}], "masks": "two original pentagons at z800 mm, no holes; canonical hashes identify the exact vertices"},
        "complete_layers": [{"target_mean_nm": 3500, "rate_nm_s": .5, "duration_s": 7000, "source_slot": 1, "mask_slot": 0}, {"target_mean_nm": 3500, "rate_nm_s": .9, "duration_s": 3500/.9, "source_slot": 2, "mask_slot": 1}],
        "stale_free_text": "Machine description/notes mention48/48,240mm and no masks; validated numeric120/36,312mm and two masks were executed. Source labels also retain uncalibrated demonstration notes.",
        "separate_stored_result_lineages": [{"record": "new uploaded coatasset", "grid": 181, "samples_per_cycle_layer": 241, "global_time_steps": 217779, "stored_gpu_cv_percent": .54949347}, {"record": "new user PDF", "grid": 300, "samples_per_cycle_layer": 481, "global_time_steps": 435556, "stored_dml_cv_percent": .542, "stored_wall_s": 320.902969}, {"record": "recovered JSON historical CPU", "grid": 300, "samples_per_cycle_layer": 481, "global_time_steps": 435558, "stored_cpu_cv_percent": .54234660}],
        "pdf_branch": {"algorithm": "fast_cycle mean", "finite_periodic_integration": False, "physical_layer_durations_preserved_in_metadata": True, "integrated_seconds_per_layer": 12, "samples_per_layer": 481, "actual_dt_s": 12/481, "residual_s": [4, 8/9], "residual_fraction": [4/7000, (8/9)/(3500/.9)], "tails_integrated": False},
        "historical_identity": selected["historical_identity"],
        "product_python_identity": selected["product_python_identity"],
        "original_assets_in_bundle": False,
    }
    write("NUMERIC_IDENTITY.json", identity)
    lines = ["# 完整工艺当前检查点", "", "2026-10-05 UTC · 请优先读取本文件；RESULTS.md保留较早的0.0125秒检查点", "", "## 结论", "",
        "完整原配方两层7000/3888.888889秒、合计10888.888889秒和7000 nm均已评估。完整直接积分0.0125→0.00625秒的时间稳定性已通过本研究固定案例筛查。既有保留实际尾段的finite-periodic在0.0015625秒也通过grid21、原12/16源节点、基线与固定10-mm源位探针的限定参考筛查。空间/源的CV分辨率和最终联合分辨率direct一致性仍未建立，没有新优化或工程排名。", "",
        "这是一项小效应分辨率研究。源与设备未实测校准，允许生产偏差尚未指定；下列严格门槛不能当成产品不合格或制造精度声明。用户已决定先推进下一项工作，此处停止继续加密。", "",
        "## 秒数、形状与CV必须分开", "",
        f"固定探针归一形状RMS效应0.03420735149百分点，保留10%形状筛查为{tau:.9f}百分点，按7000-nm参考等效{tau*70:.6f} nm。CV效应0.002868730509百分点，另列10% CV观测变化诊断{cv_tau:.9f}百分点。后一项不替换原形状判据；未来优化排名仍需针对实际目标差建立数值分辨率。", "",
        "|检查|基线/探针全图RMS差（百分点）|结论|", "|---|---:|---|",
        "|direct .0125→.00625|0.000840902 / 0.000841957|时间稳定性观测screen通过；内部135-mm及CV也通过|",
        "|finite-periodic .00625 vs direct .00625|0.004460569 / 0.004148855|形状screen未过；CV变化screen通过|",
        "|finite-periodic .0015625 vs direct .00625|0.001396775 / 0.001531923|加direct最后一次变化后0.002237677 / 0.002373879，通过固定grid21参考screen|", "",
        "上述最后一行是经验性变化量合计，并非误差上界或时间收敛阶证明，不可外推到grid61或新增源节点。direct .00625基线/探针耗时259.539/259.082秒，完整1742224节点；两层实际步长0.006249994420/0.006249992188秒。所有核批次进度校验完整，无截断。周期.0015625实际核段步长最大.0015625秒，whole cycles与4/.888888889秒实际尾段都保留。", "",
        "## 用户fast_cycle与本次finite_periodic", "",
        "PDF采用fast_cycle周期均值，finite_periodic_integration=false：每层481点积分12秒，实际Δt=0.024948024948秒，再按目标均值缩放，未积分打印出的残余。它与本研究保留尾段的finite_periodic是两个原有分支。新coatasset/grid181/241点、PDF/grid300/481点和恢复CPU/grid300/481点有相同7记录几何图，但分别为217779/435556/435558全局节点的不同结果记录。", "",
        "厚层残余分数仅0.000571429/0.000228571。在grid21、两分支周期采样同为1921点时，fast_cycle均值与保留尾段图差0.000273611百分点RMS，按7000-nm参考约0.019153 nm；对应CV差0.000029113百分点。完整direct差约0.312438 nm主要还含不同时间求积网格，不能将其全归于残余近似。0.025秒分支周期节点481/480不同，故该对照不用于隔离残余效应。", "",
        "固定短层机制测试说明：低于回归周期的层会回退完整积分；周期和尾段网格对齐时差接近舍入误差，非对齐时可出现求积差。正确保留尾段不因层数多必然失效；纯周期均值分支在短于几个周期、残余比例较大的层则需要另外检查。这些fixture没有替换主配方。", "",
        "## 空间面积与有限源诊断", "",
        "grid21/41/61的原有效中心单元覆盖约97.52/98.67/99.00%完整盘。原地图比较除以各自全域均值，所以内部135-mm RMS仍混有全域归一化与覆盖差。改用相同物理135-mm ROI均值归一，grid41→61共点形状差仅约0.000001012/0.000001741百分点。41与61不互为嵌套，比较取gcd网格21，不插值。", "",
        "额外用所有有效中心的Voronoi单元与精确圆盘相交，完整物理盘面积分割100%，没有凭空补外点。它是分片恒定统计近似，不能称作连续场精确积分，也不替代原判据。完整盘CV从grid41→61仍改变0.000421729/0.000564726百分点，大于严格CV诊断0.000286873；所以不能将剩余差全归于边缘遗漏。", "",
        "source5→7通过观测screen，7→9源加密仍有探针CV小幅超限：原指标0.000312624，完整盘补充指标0.000302305百分点。圆盘笛卡尔中心入选采样的二阶矩误差非单调：q5 +3.619%、q7 −4.688%、q9 +7.640%，说明边界节点入选存在alias；q11/q13只有节点矩分析，没有新forward评估。暂不盲目扩大采样阶数。", "",
        "这些grid/source结果使用周期参考作为有条件诊断。最大grid/source/time组合与完整direct一致性未测，不能将grid21参考资格自动迁移。", "",
        "## 资源、测试与可恢复失败", "",
        "|阶段|实际CPU核调用|墙钟秒|", "|---|---:|---:|"]
    lines += [f"|{x['stage']}|{x['actual_core_calls']}|{x['wall_s']:.3f}|" for x in counts]
    lines += ["", f"合计{status['resource_accounting']['actual_core_calls']}次真实CPU核调用，阶段墙钟合计{status['resource_accounting']['stage_wall_s_sum']:.3f}秒。后处理、二阶矩分析和单元测试没有增加真实核调用。重复pilot完整计入；一次共点后处理错误保留记录后修复，复用了已完成字段，没有重复forward。", "",
        "完整配方合同6项测试及完整圆盘控制单元5项测试通过。历史follow-up模块同名导致的import失败保留，隔离加载7项测试通过。初始研究/两项历史跟进56个记录和103份canonical Python哈希保持一致。", "",
        "## 后续成本与适用边界", "",
        "最终joint direct仍未执行。按实测完整direct与源节点工作量外推：grid41/source9/.00625约1.5小时/例，配对约3小时；grid61/source9约3.3小时/例。grid41/source5桥接约29分钟/例但不能认证source9。这些是计划估计，不是已执行数据。当前没有多小时任务运行。", "",
        "需要先明确工程上希望分辨的膜厚/均匀性变化尺度，再选择有理由的联合direct对照和统计判据；不能把本次约0.239-nm探针相对筛查暗中变成生产公差。要比较名义/稳健算法，还必须在符合步长、完整过程和数值资格的前向上重新训练，使用相同真实调用预算和独立配对holdout。旧12秒、粗步长训练候选只保留为诊断史料。", "",
        "初始robust研究仍是负面/不确定结果：5%扰动粗分辨率稳健方案在2/3重复中均值更差，数值细化会改变排名；没有证明稳健收益或可靠性提升。没有达到约束失败概率的统计认证。", "",
        "输入描述存在旧文字48/48、240mm、无板；实际validated numeric为120/36、312mm和两块原板。源模型未校准。详见NUMERIC_IDENTITY.json的图身份与三条结果谱系；紧凑包不包含原始coatasset、PDF、恢复snapshot或设计原文件。", "",
        "## 文件入口", "",
        "- CURRENT_STATUS.json：分离时间、周期、空间、源和联合门禁，实际调用账", "- NUMERIC_IDENTITY.json：7条canonical记录哈希、模型单位和结果谱系", "- continued_00625/、periodic_finer/：完整直接与廉价周期参考证据", "- fast_cycle_branch_check/：用户所选周期均值分支的独立对照", "- spatial_source_diagnostics/：所有字段、面积统计、源矩alias和失败记录", "- docs/algorithms.html：可离线算法图解", "- handoff_manifest.json、verify_handoff.py：纯文件完整性核验", "", "本检查点只写授权研究目录，canonical产品和此前历史保留。没有新优化、产品改写、GitHub、本地任务或Library上传。"]
    (HERE / "CURRENT_STATUS.md").write_text("\n".join(lines) + "\n")
    (HERE / "README.md").write_text("""# 完整原队列工艺：当前检查点

请先读[CURRENT_STATUS.md](CURRENT_STATUS.md)和[分离门禁JSON](CURRENT_STATUS.json)。完整10888.888889秒配方的direct .0125→.00625秒时间稳定性通过；finite-periodic .0015625秒仅建立grid21/原12与16源节点、基线和固定探针的限定参考。空间/源CV分辨率及最终联合direct资格未建立，没有工程排名或新优化。RESULTS.md和convergence_results.json保留较早检查点，其旧time=false不是最新结论。

- [numeric identity与三条stored run谱系](NUMERIC_IDENTITY.json)
- [完整.00625与周期/尾段机制](continued_00625/stage_results.json)、[限定周期参考](continued_00625/periodic_finer/finer_results.json)
- [用户fast_cycle mean分支对照](fast_cycle_branch_check/branch_results.json)
- [grid/source诊断](spatial_source_diagnostics/diagnostic_results.json)、[固定完整圆盘面积补充](spatial_source_diagnostics/controlled_aggregate_results.json)、[源采样alias](spatial_source_diagnostics/source_moment_alias.json)
- [算法、单位与图解](docs/algorithms.html)
- [初始完整输入身份](selected_input_manifest.json)、[原snapshot](input_snapshot.json)，均只保留在研究工作区，紧凑包排除这些原文件

严格screen不是批准的生产公差；模型未实测校准。周期资格不自动迁移到更高grid/source，完整盘分片恒定统计也不是连续场精确积分。当前按指示停止加密，没有多小时任务运行。

文件审计不执行物理核：

    python -B verify_handoff.py
    python -B verify_handoff.py --workspace

紧凑包用于离线读结果、字段和代码审计。verify_handoff.py可在解压后核验包内文件；研究驱动仍依赖原工作区研究helpers、对应cub代码和用户原始输入，包不含产品源码或输入原件，不是独立安装器。不应直接重跑driver覆盖冻结结果。

单元测试（原工作区，无真实forward调用）：

    OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_full_process.py
    cd spatial_source_diagnostics && OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v test_cells.py

当前checkpoint合计130次真实CPU核调用，含重复pilot、周期片段和独立机制fixture。没有原配方截断、产品写入、GitHub动作或Library上传。
""")
    # Freeze each completed child stage independently; no physics is repeated.
    for name in ("continued_00625", "fast_cycle_branch_check", "spatial_source_diagnostics"):
        root = HERE / name
        files = {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob("*")) if p.is_file() and p.name != "stage_manifest.json" and "__pycache__" not in p.parts}
        (root / "stage_manifest.json").write_text(json.dumps({"files": files, "count": len(files)}, indent=2) + "\n")
    # Audit package excludes all original input records. Result arrays are small
    # derived evidence; retaining them permits later comparisons without a rerun.
    excluded = {"input_snapshot.json", "selected_input_manifest.json", "input_inventory.json", "artifact_manifest.json", "handoff_manifest.json", "bundle_receipt.json", "handoff_verification.json"}
    files = {str(p.relative_to(HERE)): digest(p) for p in sorted(HERE.rglob("*")) if p.is_file() and p.name not in excluded and "__pycache__" not in p.parts and p.suffix != ".zip"}
    write("handoff_manifest.json", {"files": files, "count": len(files), "excludes_original_assets": True, "scope": "Completed bounded full-process numerical research checkpoint, not product certification"})
    zip_path = HERE / "full_process_numerical_checkpoint_2026-10-05.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in [*files, "handoff_manifest.json"]:
            info = zipfile.ZipInfo(name, (2026, 10, 5, 15, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (HERE / name).read_bytes())
    write("bundle_receipt.json", {"file": zip_path.name, "bytes": zip_path.stat().st_size, "sha256": digest(zip_path), "entries": len(files)+1, "original_input_records_included": False, "library_upload_performed": False})
    print(json.dumps({"actual_calls": status["resource_accounting"]["actual_core_calls"], "stage_wall_s_sum": status["resource_accounting"]["stage_wall_s_sum"], "bundle": read("bundle_receipt.json")}, indent=2))


if __name__ == "__main__":
    main()
