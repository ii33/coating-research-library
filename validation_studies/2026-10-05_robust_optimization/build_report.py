"""Render existing results, then freeze artifact hashes. No forward calls."""
from pathlib import Path
import hashlib
import html
import json
import math

from evaluator import masks_for_design
from run_study import summarize, paired_bootstrap
import numpy as np

HERE = Path(__file__).resolve().parent


def fmt(x):
    return f"{x:.5f}"


def interval(item):
    lo, hi = item["percentile_95_interval"]
    return f"{item['estimate']:+.5f} [{lo:+.5f}, {hi:+.5f}]"


def main():
    p = json.loads((HERE / "results/study_results.json").read_text())
    cfg = p["config"]
    optimizations, vals = p["optimizations"], p["validations"]
    training_calls = sum(o["counter"]["forward_calls"] for o in optimizations)
    validation_calls = sum(d["counter"]["forward_calls"] for v in vals for res in ("coarse", "refined") for d in v[res].values())
    convergence_calls = sum(c["counter"]["forward_calls"] for c in p["nominal_convergence"])
    failures = sum(o["counter"]["failed_forward_calls"] + o["counter"]["invalid_candidates"] for o in optimizations)
    failures += sum(d["counter"]["failed_forward_calls"] + d["counter"]["invalid_candidates"] for v in vals for res in ("coarse", "refined") for d in v[res].values())
    lines = ["# 结果：稳健优化工程优越性未建立", "", "2026-10-05 UTC · 实际 cub 正向内核 · 独立合成小研究", "",
        "## 结论先读", "",
        "实际内核接线、调用预算和可复现性已验证。稳健目标在这组人为不确定度与有限搜索下没有一致优于名义目标。5% 扰动时，64 情景粗分辨率留出中稳健均值 CV 在 3 次中的 2 次更差；加密配对的 16 情景中仍有一个明确负例，另两次小幅改善。1% 扰动中稳健留出 CV 较低，但方法差幅小于本次加密引起的数值变化。工程层面的稳健性能比较仍 unresolved。", "",
        "两方法在所有运行的留出情景中均零违例，不能据此宣称稳健方案提高了合格率。CV≤2%、η≥0.85 是本研究合成门槛，不是用户产品指标。", "",
        "## 冻结比较设计", "",
        "决策量是源 X 位置和两块连通矩形零厚度板的宽度；源为实际 30×10 mm 有限矩形源，n=2、15 rpm、12 s 积分。单位 mm/s/rpm，源/板机架固定，基片行星运动。名义最小面积加权 CV；稳健最小训练 E[CV]+1×SD[CV]，并对对应训练情景执行同一约束。", "",
        "每方法、每扰动级、每种子训练恰为 240 次实际正向调用：名义 120 个候选，稳健 30 个候选×4 情景。每情景都包含实际有板调用和同场景无板吞吐参考。未缓存、未赠送分母调用。真实调用公平并不等于候选数、信息量或墙钟相等。", "",
        "1%/5% 的位置标准差分别为 1/5 mm，基准是统一的 100 mm 参考尺度；A/n/rpm 标准差为各自名义值的 1%/5%。12 个潜变量独立，同一刚体内部位移完全相关。均为合成假设，不是实测公差。A 只改变原始均值，从相对 CV 和同情景 η 中抵消，不支持源强/绝对膜厚稳定性结论。", "",
        "稳健训练仅名义+3 个随机情景。种子 11/29/47；训练与留出用独立 RNG 流，最终双设计冻结后才生成留出。各级同潜变量抽样、两方法共同随机数。64 个基础留出，前 16 个用加密分辨率重算，完全不参与选择。", "",
        "## 每次运行的名义权衡与留出表现", "",
        "CV 单位为 %；CV 差的单位为百分点。η 为平均沉积保留比，不是整体设备利用率。每行两个名义 CV 都是选定设计在零扰动下重算。p95 为有限样本分位数。", "",
        "|扰动|种子|分辨率|方法|零扰动 CV %|留出平均 CV %|留出 p95 CV %|SD %|平均 η|违例/情景|", "|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for v in vals:
        for res in ("coarse", "refined"):
            for mode in ("nominal", "robust"):
                d = v[res][mode]; s = d["summary"]
                lines.append(f"|{v['level']:.0%}|{v['seed']}|{res}|{mode}|{fmt(d['nominal']['cv_percent'])}|{fmt(s['mean_cv_percent'])}|{fmt(s['p95_cv_percent'])}|{fmt(s['sd_cv_percent'])}|{fmt(s['mean_throughput'])}|{s['violation_count']}/{s['n']}|")
    lines += ["", "## 配对不确定度", "",
        "下列为 robust−nominal，负数有利于稳健；区间为 2000 次配对 bootstrap 百分位 95% 区间，只覆盖这组固定设计和合成分布的 Monte Carlo 误差。它不包括数值离散、模型误差、真实机器漂移或有限搜索误差。16 样本的 p95 尤其不稳定。", "",
        "|扰动|种子|分辨率|平均 CV 差百分点 [区间]|p95 CV 差百分点 [区间]|", "|---|---|---|---|---|"]
    for v in vals:
        for res in ("coarse", "refined"):
            b = v[f"paired_{res}"]
            lines.append(f"|{v['level']:.0%}|{v['seed']}|{res}|{interval(b['mean_cv_delta_pp'])}|{interval(b['p95_cv_delta_pp'])}|")
    lines += ["", "全部违例比例差都为 0，bootstrap 区间 [0,0] 只反映样本中无违例，并不是总体概率已知为零。在假设独立同分布且分布正确的前提下，零事件的精确单侧 95% 上界是 1−0.05^(1/n)：n=64 为 4.57%，n=16 为 17.07%。这仍不是现实过程可靠性。", "",
        "## 数值敏感性：未达到工程收敛", "",
        "coarse=21 网格/96 时间/3×3 源元，refined=41/192/5×5，核查=61/384/7×7。三轴同时变化，不能把差异归因到某一个轴；没有误差界，也没有连续空间精度保证。", "",
        "|扰动|预选种子|方法|21/96/9 名义 CV %|41/192/25 名义 CV %|61/384/49 名义 CV %|", "|---|---|---|---:|---:|---:|"]
    for c in p["nominal_convergence"]:
        v = next(v for v in vals if v["level"] == c["level"] and v["seed"] == c["seed"])
        mode = c["mode"]
        lines.append(f"|{c['level']:.0%}|{c['seed']}|{mode}|{fmt(v['coarse'][mode]['nominal']['cv_percent'])}|{fmt(v['refined'][mode]['nominal']['cv_percent'])}|{fmt(c['row']['cv_percent'])}|")
    lines += ["", "粗网格中名义目标确实得到更低的名义 CV，但 seed 11、1% 选定设计的名义排序在加密后反转。这说明优化器可能利用了有限采样特征。1% 例的改善差幅约 0.035–0.039 百分点，而完全相同的前 16 个留出情景中，同一设计 coarse→refined 的平均 CV 改变量约 0.1735–0.2354 百分点；加密→核查仍有约 0.05–0.06 百分点变化，不能称为已收敛。", "",
        "### 完全相同的 16 个留出情景，分辨率排名复查", "",
        "下面将粗结果也限制到相同前 16 个情景，避免把情景子样本差当作加密效果。所有设计固定，不再优化、不重选赢家。CV 差仍为 robust−nominal，单位百分点。", "",
        "|扰动|种子|coarse 前16 平均 CV 差|refined 同16 平均 CV 差|", "|---|---|---:|---:|"]
    matched = []
    for v in vals:
        coarse_rows = {m: v["coarse"][m]["rows"][:cfg["refined_holdout_scenarios"]] for m in ("nominal", "robust")}
        coarse_pair = paired_bootstrap(coarse_rows["nominal"], coarse_rows["robust"], cfg["constraints"], v["seed"], cfg["bootstrap"]["resamples"])
        delta_coarse = coarse_pair["mean_cv_delta_pp"]["estimate"]
        delta_refined = v["paired_refined"]["mean_cv_delta_pp"]["estimate"]
        lines.append(f"|{v['level']:.0%}|{v['seed']}|{delta_coarse:+.5f}|{delta_refined:+.5f}|")
        matched.append({"level": v["level"], "seed": v["seed"],
            "same_latent_scenario_count": cfg["refined_holdout_scenarios"],
            "coarse_first16": {m: summarize(coarse_rows[m], cfg["constraints"]) for m in coarse_rows},
            "paired_coarse_first16": coarse_pair, "paired_refined_same16": v["paired_refined"]})
    (HERE / "results/matched_resolution_holdout.json").write_text(json.dumps(matched, indent=2) + "\n")
    lines += ["", "5% seed 29 在完全相同的 16 个情景中，方法均值排序随分辨率反转（+0.00664→−0.01516 百分点）；这是实际采样设置敏感性的证据。三个加密轴同时改变，不能确定由哪个轴导致，也不能据此称更密设置为准确真值。", "",
        "面积权重是盘内节点 Voronoi 单元与圆盘交集。产品不输出盘外节点，边缘部分单元没有代表点，所以其覆盖率只有 97.5176%/98.6670%/99.0020%。这些结果是表示面域上的近似面积统计；没有对遗漏边缘造值，也不冒充整个连续圆盘保证。", "",
        "## 初值、无板与设计保存", "",
        "初值 (source_x=100 mm, width1=5 mm, width2=5 mm) 为合法连通矩形，基线薄板 Z=350/450 mm。3 个分辨率的初值/无板核查见 baseline_resolution_diagnostic.json。无板是真正的参考正向调用；板族不包含无板选项，任何实用建议都应保留无板回退。结果 JSON 的每个 optimization.design 保留最终变量，每条 history 保留完整训练场景和调用累计数。", "",
        "## 调用、耗时、失败与完整性", "",
        f"主 driver 共 {training_calls + validation_calls + convergence_calls} 次实际 cub 调用：训练 {training_calls}、基础/加密留出含零扰动 {validation_calls}、高密度名义核查 {convergence_calls}。总墙钟 {p['wall_s']:.2f} s，CPU 单进程；每方法的 kernel/墙钟耗时见 JSON，线程与版本见 baseline_manifest.json。没有 GPU 或加速比结论。", "",
        f"主比较输入/几何/正向失败合计 {failures}，全部已运行的留出行有效。18 项 unittest 全通过；故障注入、完全无通量、非法幅值/指数/板位和退化几何拒绝都保留为测试，不能当作实机通过。", "",
        "额外调用单独披露：运行设计前用 20 个源位/宽度组合做了 40 次粗核几何探针，检查双板是否保留正通量及成本，不列入任何方法获胜证据；事后初值分辨率诊断 6 次调用；初次小测试共 88 次真实 cub 调用，加 1 次模拟故障调用。测试/诊断复跑不属于训练预算，验证时应另计。没有把这些叫作正式预注册实验。", "",
        "主 driver 执行前后全产品 Python 文件 SHA-256 相同。只读源依赖与研究输出完整性均检查；迁移产品无 .git，所写 baseline commit 是既有 cub 部署记录，不是新远程 Git 审计。没有更改 canonical Python、产品 main/data、用户本地研究或 GitHub。", "",
        "## 论文来源与复用边界", "",
        "Ankit Shrivastava、Matias Kalaswad、Joyce O. Custer、David P. Adams、Habib N. Najm：Bayesian Optimization for Stable Properties Amid Processing Fluctuations in Sputter Deposition，arXiv:2405.03092v1，2024-05-06，§III.1，https://arxiv.org/html/2405.03092v1 ，读取 2026-10-05。仅借鉴性能、约束、扰动敏感性联合考虑的思路；mean+SD 是本研究约定，不是该文算法复刻。未迁移 Mo 应力/电阻门槛，未保存第三方全文。", "",
        "可复用成果：实际核适配器、计数器、退化拒绝、固定训练情景、独立配对留出、预算受限搜索、bootstrap 与源身份检查。下一步应由真实重复测量形成相关不确定度，分别进行时间/空间/源加密，并验证绝对厚度与有限板厚/支架/制造约束；本次不会自行扩展成长时间工程计算。", ""]
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    timings = [{"level": o["level"], "seed": o["seed"], "mode": o["mode"],
                "training_wall_s": o["wall_s"], "training_kernel_s": o["counter"]["elapsed_s"],
                "training_calls": o["counter"]["forward_calls"],
                "invalid_candidates": o["counter"]["invalid_candidates"],
                "failed_forward_calls": o["counter"]["failed_forward_calls"]} for o in optimizations]
    (HERE / "results/timings_and_failures.json").write_text(json.dumps(timings, indent=2) + "\n")
    designs = []
    for o in optimizations:
        masks = masks_for_design(o["design"], np.zeros(12))
        designs.append({"level": o["level"], "seed": o["seed"], "mode": o["mode"],
            "source_position_mm": [o["design"][0], 0., 0.],
            "masks": [{"z_mm": m["z_mm"], "outer": m["outer"].tolist(), "holes": []} for m in masks],
            "status": "synthetic_zero_thickness_geometry_only_not_manufacturing_release"})
    (HERE / "results/designs.json").write_text(json.dumps(designs, indent=2) + "\n")
    # A standalone static SVG, no internet or visualization dependencies.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="470" viewBox="0 0 900 470">',
        '<rect width="900" height="470" fill="#f5f8f7"/>',
        '<text x="40" y="38" font-family="sans-serif" font-size="22" fill="#173d46">Paired refined holdout: robust minus nominal CV</text>',
        '<text x="40" y="63" font-family="sans-serif" font-size="14" fill="#425d65">16 scenarios per repeat; 95% paired Monte Carlo bootstrap, numerical error excluded</text>']
    xlo, xhi, x0, xscale = -.08, .13, 320, 480 / .21
    def xx(x): return x0 + (x - xlo) * xscale
    svg.append(f'<line x1="{xx(0):.1f}" y1="85" x2="{xx(0):.1f}" y2="380" stroke="#8eabad" stroke-dasharray="4 4"/>')
    for i, v in enumerate(vals):
        d = v["paired_refined"]["mean_cv_delta_pp"]; lo, hi = d["percentile_95_interval"]
        y = 108 + i * 47; color = "#aa5834" if d["estimate"] > 0 else "#18796c"
        svg += [f'<text x="45" y="{y + 5}" font-family="sans-serif" font-size="16">{v["level"]:.0%}, seed {v["seed"]}</text>',
            f'<line x1="{xx(lo):.1f}" y1="{y}" x2="{xx(hi):.1f}" y2="{y}" stroke="{color}" stroke-width="4"/>',
            f'<circle cx="{xx(d["estimate"]):.1f}" cy="{y}" r="6" fill="{color}"/>',
            f'<text x="810" y="{y + 5}" font-family="sans-serif" font-size="14">{d["estimate"]:+.4f}</text>']
    svg += ['<text x="325" y="411" font-family="sans-serif" font-size="14">← favors robust</text>',
        '<text x="650" y="411" font-family="sans-serif" font-size="14">favors nominal →</text>',
        '<text x="40" y="448" font-family="sans-serif" font-size="14" fill="#aa5834">Engineering comparison unresolved: resolution shifts exceed the small 1% method differences</text>', '</svg>']
    (HERE / "results/paired_refined_mean_cv.svg").write_text("\n".join(svg))
    files = {str(f.relative_to(HERE)): hashlib.sha256(f.read_bytes()).hexdigest()
             for f in sorted(HERE.rglob("*")) if f.is_file() and f.name != "artifact_manifest.json" and "__pycache__" not in f.parts}
    (HERE / "results/artifact_manifest.json").write_text(json.dumps({"files": files, "count": len(files)}, indent=2) + "\n")
    print(f"Report rendered; {len(files)} persisted study files hashed; no forward calls")


if __name__ == "__main__":
    main()
