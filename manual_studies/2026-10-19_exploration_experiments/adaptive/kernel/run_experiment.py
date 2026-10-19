#!/usr/bin/env python3
"""Reproducible, deliberately idealized thin-film search benchmark.

Synthetic constant n,k, normal incidence, coherent isotropic planar films;
not a real-material IR coating design or production simulator.
Only numpy/scipy are required; matplotlib is optional for the final chart.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import differential_evolution, least_squares
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parent
N0 = 1.0
NS = 3.42
LAYER_N = np.array([1.45, 2.35] * 3, dtype=float)
LOWER = 0.005  # um; ideal numerical bound, not a process qualification
UPPER = 2.5    # um per layer
TARGET_R = 0.01
TRAIN_POINTS = 81
VALID_POINTS = 4097
AUDIT_POINTS = 16385
SEEDS = (11, 29, 47)
TOTAL_BUDGET = 6000
POPULATION = 48
HYBRID_DE_BUDGET = 4800
CASES = {
    "single_ar_3_5": [(3.0, 5.0)],
    "dual_window_ar_3_5_8_12": [(3.0, 5.0), (8.0, 12.0)],
}


def tmm_normal(wavelength_um, thickness_um, layer_n, n0=N0, ns=NS):
    """Characteristic E,H matrices; exp(-i wt), forward exp(+i kz).

    n may be complex with Im(n)>=0. Exterior media must be real positive.
    This intentionally excludes oblique incidence, absorbing exterior media,
    incoherent substrates, roughness, anisotropy, and severe-opacity stability.
    Returns power R,T for illumination from n0 toward ns.
    """
    wl = np.atleast_1d(np.asarray(wavelength_um, dtype=float))
    ds = np.asarray(thickness_um, dtype=float)
    ns_layers = np.asarray(layer_n, dtype=complex)
    if len(ds) != len(ns_layers):
        raise ValueError("thickness and layer_n length differ")
    if np.any(wl <= 0) or np.any(ds < 0):
        raise ValueError("wavelength must be positive, thickness nonnegative")
    if np.imag(n0) != 0 or np.imag(ns) != 0 or np.real(n0) <= 0 or np.real(ns) <= 0:
        raise ValueError("exterior media must be real positive")
    a = np.ones(wl.shape, dtype=complex)
    b = np.zeros(wl.shape, dtype=complex)
    c = np.zeros(wl.shape, dtype=complex)
    d = np.ones(wl.shape, dtype=complex)
    for nj, dj in zip(ns_layers, ds):
        phase = 2 * np.pi * nj * dj / wl
        co, si = np.cos(phase), np.sin(phase)
        m01, m10 = -1j * si / nj, -1j * nj * si
        a, b, c, d = (a * co + b * m10, a * m01 + b * co,
                      c * co + d * m10, c * m01 + d * co)
    den = n0 * (a + b * ns) + c + d * ns
    r = (n0 * (a + b * ns) - c - d * ns) / den
    t = 2 * n0 / den
    return np.abs(r) ** 2, (np.real(ns) / np.real(n0)) * np.abs(t) ** 2


def reflection_recursion(wavelength_um, thickness_um, layer_n, n0=N0, ns=NS):
    """Independent scalar Fresnel recursion, not the matrix implementation."""
    wl = np.atleast_1d(np.asarray(wavelength_um, dtype=float))
    media = np.array([n0, *layer_n, ns], dtype=complex)
    if not len(thickness_um):
        return np.full(wl.shape, abs((n0 - ns) / (n0 + ns)) ** 2)
    rr = np.full(wl.shape, (media[-2] - media[-1]) / (media[-2] + media[-1]), dtype=complex)
    for j in range(len(thickness_um) - 1, -1, -1):
        rj = (media[j] - media[j + 1]) / (media[j] + media[j + 1])
        phase = np.exp(4j * np.pi * media[j + 1] * thickness_um[j] / wl)
        rr = (rj + rr * phase) / (1 + rj * rr * phase)
    return np.abs(rr) ** 2


def validate_physics():
    wl = np.linspace(0.5, 14.0, 301)
    r, t = tmm_normal(wl, [], [])
    bare = ((N0 - NS) / (N0 + NS)) ** 2
    fresnel_error = float(np.max(np.abs(r - bare)))
    n_ar = math.sqrt(N0 * NS)
    r_ar, t_ar = tmm_normal([4.0], [4.0 / (4 * n_ar)], [n_ar])
    rng = np.random.default_rng(20261019)
    conservation_error, recursion_error, zero_layer_error = 0.0, 0.0, 0.0
    absorbing_A_min, absorbing_A_max = 1.0, 0.0
    for _ in range(100):
        count = int(rng.integers(1, 13))
        ds = rng.uniform(0.0, 2.5, count)
        nn = rng.uniform(1.2, 3.5, count)
        r, t = tmm_normal(wl, ds, nn)
        conservation_error = max(conservation_error, float(np.max(np.abs(r + t - 1))))
        recursion_error = max(recursion_error, float(np.max(np.abs(r - reflection_recursion(wl, ds, nn)))))
        rz, tz = tmm_normal(wl, np.zeros(count), nn)
        zero_layer_error = max(zero_layer_error, float(np.max(np.abs(rz - bare))))
        nn_abs = nn + 1j * rng.uniform(0.001, 0.10, count)
        ra, ta = tmm_normal(wl, ds, nn_abs)
        aa = 1 - ra - ta
        absorbing_A_min = min(absorbing_A_min, float(aa.min()))
        absorbing_A_max = max(absorbing_A_max, float(aa.max()))
        recursion_error = max(recursion_error, float(np.max(np.abs(ra - reflection_recursion(wl, ds, nn_abs)))))
    # Same index in every layer cannot introduce reflection in matched exteriors.
    r_match, t_match = tmm_normal(wl, [.13, .57, 1.2], [1.7] * 3, 1.7, 1.7)
    result = {
        "bare_fresnel_R": bare,
        "fresnel_max_abs_error": fresnel_error,
        "ideal_single_quarterwave_R_at_4um": float(r_ar[0]),
        "ideal_single_quarterwave_T_at_4um": float(t_ar[0]),
        "random_lossless_energy_max_abs_error_100_stacks": conservation_error,
        "matrix_vs_independent_recursion_R_max_abs_error": recursion_error,
        "zero_thickness_reduces_to_fresnel_error": zero_layer_error,
        "matched_media_max_R": float(r_match.max()),
        "matched_media_max_T_error": float(np.max(np.abs(t_match - 1))),
        "random_passive_absorption_min": absorbing_A_min,
        "random_passive_absorption_max": absorbing_A_max,
        "scope": "normal incidence only; semi-infinite real exterior media; random tests are sanity checks, not full software certification",
    }
    assert fresnel_error < 1e-12
    assert r_ar[0] < 1e-24
    assert conservation_error < 1e-11
    assert recursion_error < 1e-11
    assert zero_layer_error < 1e-12
    assert r_match.max() < 1e-24
    assert absorbing_A_min > -1e-12
    assert absorbing_A_max <= 1 + 1e-12
    result["all_checks_passed"] = True
    return result


def grids(windows, points):
    return [np.linspace(lo, hi, points) for lo, hi in windows]


def classical_templates(windows):
    """Heuristic thickness seeds; material order stays LHLHLH throughout.

    Embedded 2-layer quarter-wave matching seeds and alternating quarter-
    wave/chirped seeds. Alternating QW is also a reflector template and is
    included as a deliberately checkable baseline, not presumed good AR.
    """
    c1 = math.sqrt(windows[0][0] * windows[0][1])
    c2 = math.sqrt(windows[-1][0] * windows[-1][1])
    cm = math.sqrt(c1 * c2)
    out = []
    for label, center in (("pair_short_qw", c1), ("pair_long_qw", c2), ("pair_geomean_qw", cm)):
        ds = np.full(6, LOWER)
        ds[:2] = center / (4 * LAYER_N[:2])
        out.append((label, np.clip(ds, LOWER, UPPER)))
    out.append(("alternating_qw", np.clip(cm / (4 * LAYER_N), LOWER, UPPER)))
    out.append(("chirped_qw", np.clip(np.geomspace(c1, c2, 6) / (4 * LAYER_N), LOWER, UPPER)))
    # A half-wave correction pair may leave center-frequency matching intact
    # while changing off-center response; it is only a starting template.
    ds = np.full(6, LOWER)
    ds[:2] = cm / (4 * LAYER_N[:2])
    ds[2:4] = cm / (2 * LAYER_N[2:4])
    out.append(("pair_plus_halfwave", np.clip(ds, LOWER, UPPER)))
    return out


class BudgetExhausted(Exception):
    pass


class Objective:
    """Count EVERY spectral stack evaluation, including finite differences."""
    def __init__(self, windows, budget):
        self.wavelengths = grids(windows, TRAIN_POINTS)
        self.all_wl = np.concatenate(self.wavelengths)
        self.budget = int(budget)
        self.calls = 0
        self.best_loss = math.inf
        self.best_x = None

    def residual(self, x):
        if self.calls >= self.budget:
            raise BudgetExhausted()
        self.calls += 1
        rr, _ = tmm_normal(self.all_wl, x, LAYER_N)
        # Equal weight per window, NOT per um of wavelength range.
        # Squared hinge residual -> fourth-power violation objective;
        # weak R^2 tie-breaker still rewards below-target improvement.
        scale = math.sqrt(len(self.wavelengths) * TRAIN_POINTS)
        v = np.maximum(rr / TARGET_R - 1.0, 0.0)
        residual = np.concatenate((v ** 2 / scale, 0.01 * rr / TARGET_R / scale))
        loss = float(residual @ residual)
        if loss < self.best_loss:
            self.best_loss, self.best_x = loss, np.array(x, copy=True)
        return residual

    def scalar(self, x):
        r = self.residual(x)
        return float(r @ r)


def run_local(obj, start, calls_allowed):
    old_budget = obj.budget
    obj.budget = min(old_budget, obj.calls + int(calls_allowed))
    status = "unknown"
    solver_nfev = None
    try:
        fit = least_squares(obj.residual, np.clip(start, LOWER, UPPER), bounds=(LOWER, UPPER),
                            jac="2-point", max_nfev=max(2, int(calls_allowed)),
                            ftol=1e-11, xtol=1e-11, gtol=1e-11, x_scale="jac")
        status, solver_nfev = str(fit.message), int(fit.nfev)
    except BudgetExhausted:
        status = "actual spectral evaluation budget exhausted"
    finally:
        obj.budget = old_budget
    return {"status": status, "solver_reported_nfev_excludes_some_fd_calls": solver_nfev}


def population(windows, seed):
    pop = qmc.LatinHypercube(d=6, seed=seed).random(POPULATION)
    pop = qmc.scale(pop, np.full(6, LOWER), np.full(6, UPPER))
    for i, (_, ds) in enumerate(classical_templates(windows)):
        pop[i] = ds
    return pop


def run_de(obj, windows, seed, budget):
    assert budget % POPULATION == 0
    old_budget = obj.budget
    obj.budget = min(old_budget, obj.calls + budget)
    info = {}
    try:
        fit = differential_evolution(obj.scalar, [(LOWER, UPPER)] * 6,
                    init=population(windows, seed), rng=np.random.default_rng(seed),
                    maxiter=budget // POPULATION - 1, tol=0, atol=0,
                    strategy="best1bin", mutation=(0.5, 1.0), recombination=0.7,
                    polish=False, updating="immediate", workers=1)
        info = {"status": str(fit.message), "solver_nfev": int(fit.nfev), "generations": int(fit.nit)}
    except BudgetExhausted:
        info = {"status": "actual spectral evaluation budget exhausted"}
    finally:
        obj.budget = old_budget
    return info


def metrics(x, windows, points):
    out = []
    for (lo, hi), wl in zip(windows, grids(windows, points)):
        rr, tt = tmm_normal(wl, x, LAYER_N)
        idx = int(np.argmax(rr))
        out.append({
            "window_um": [lo, hi], "points": points,
            "max_R": float(rr[idx]), "min_T": float(tt.min()),
            "mean_R_sampled": float(rr.mean()),
            "worst_R_wavelength_um": float(wl[idx]),
            "worst_violation_absolute": max(float(rr[idx]) - TARGET_R, 0.0),
            "fraction_grid_points_meeting_target": float(np.mean(rr <= TARGET_R)),
            "max_energy_error": float(np.max(np.abs(rr + tt - 1))),
        })
    return out


def run_one(case, windows, method, seed):
    obj = Objective(windows, TOTAL_BUDGET)
    started = time.perf_counter()
    info = {}
    if method == "classic_local":
        templates = classical_templates(windows)
        rng = np.random.default_rng(seed)
        stages = []
        for i, (label, ds) in enumerate(templates):
            # Keep one exact template; the other templates get a reproducible
            # mild perturbation to measure local-basin sensitivity.
            start = ds if i == 0 else np.clip(ds * rng.uniform(.90, 1.10, len(ds)), LOWER, UPPER)
            allowance = (TOTAL_BUDGET - obj.calls) // (len(templates) - i)
            before = obj.calls
            stages.append({"template": label, **run_local(obj, start, allowance), "actual_calls": obj.calls - before})
        info["local_stages"] = stages
    elif method == "classic_de":
        info["de"] = run_de(obj, windows, seed, TOTAL_BUDGET)
    elif method == "de_local":
        info["de"] = run_de(obj, windows, seed, HYBRID_DE_BUDGET)
        info["de_best_loss_before_local"] = obj.best_loss
        info["de_actual_calls"] = obj.calls
        info["de_before_local_dense_metrics"] = metrics(obj.best_x, windows, VALID_POINTS)
        before = obj.calls
        info["local"] = run_local(obj, obj.best_x, TOTAL_BUDGET - obj.calls)
        info["local_actual_calls"] = obj.calls - before
    else:
        raise ValueError(method)
    elapsed = time.perf_counter() - started
    result = {
        "case": case, "method": method, "seed": seed,
        "actual_stack_evaluations_including_fd": obj.calls,
        "training_spectral_points_per_evaluation": len(windows) * TRAIN_POINTS,
        "actual_wavelength_layer_updates": obj.calls * len(windows) * TRAIN_POINTS * len(LAYER_N),
        "optimization_wall_seconds": elapsed,
        "thickness_um_from_air_to_substrate": obj.best_x.tolist(),
        "total_thickness_um": float(obj.best_x.sum()),
        "training_objective": obj.best_loss,
        "train_metrics": metrics(obj.best_x, windows, TRAIN_POINTS),
        "independent_dense_metrics": metrics(obj.best_x, windows, VALID_POINTS),
        "higher_density_audit_metrics": metrics(obj.best_x, windows, AUDIT_POINTS),
        "solver_details": info,
    }
    result["all_windows_pass_dense"] = all(m["max_R"] <= TARGET_R for m in result["higher_density_audit_metrics"])
    return result


def write_outputs(data, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = []
    for result in data["runs"]:
        for m in result["higher_density_audit_metrics"]:
            rows.append({"case": result["case"], "method": result["method"], "seed": result["seed"],
                "window_um": "-".join(map(str, m["window_um"])),
                "max_R_percent": 100*m["max_R"], "min_T_percent": 100*m["min_T"],
                "mean_R_percent": 100*m["mean_R_sampled"],
                "worst_violation_percentage_points": 100*m["worst_violation_absolute"],
                "worst_wavelength_um": m["worst_R_wavelength_um"],
                "grid_pass_fraction": m["fraction_grid_points_meeting_target"],
                "actual_stack_evaluations": result["actual_stack_evaluations_including_fd"],
                "training_spectral_points": result["training_spectral_points_per_evaluation"],
                "wall_seconds": result["optimization_wall_seconds"],
                "total_thickness_um": result["total_thickness_um"],
                "all_windows_pass_dense": result["all_windows_pass_dense"]})
    if rows:
        with (output / "results.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    summary = []
    for case in CASES:
        for method in ("classic_local", "classic_de", "de_local"):
            group = [r for r in data["runs"] if r["case"] == case and r["method"] == method]
            if not group:
                continue
            worst = np.array([max(m["max_R"] for m in r["higher_density_audit_metrics"]) for r in group])
            summary.append({"case": case, "method": method, "seeds": [r["seed"] for r in group],
                "best_worst_R_percent": float(100*worst.min()),
                "median_worst_R_percent": float(100*np.median(worst)),
                "worst_worst_R_percent": float(100*worst.max()),
                "dense_success_count": sum(r["all_windows_pass_dense"] for r in group),
                "run_count": len(group),
                "median_actual_stack_evaluations": float(np.median([r["actual_stack_evaluations_including_fd"] for r in group])),
                "median_wall_seconds": float(np.median([r["optimization_wall_seconds"] for r in group]))})
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if summary:
        with (output / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)


def plot_results(data, output):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/coating-experiment-mpl")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/coating-experiment-cache")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
    colors = {"classic_local": "#225ea8", "classic_de": "#d95f0e", "de_local": "#238b45"}
    for ax, case in zip(axes, CASES):
        wl = np.linspace(2.5, 13, 5001)
        for method in colors:
            group = [r for r in data["runs"] if r["case"] == case and r["method"] == method]
            if not group:
                continue
            # Display the run closest to that method's median worst-window R.
            group = sorted(group, key=lambda r: max(m["max_R"] for m in r["higher_density_audit_metrics"]))
            rep = group[len(group)//2]
            rr, _ = tmm_normal(wl, rep["thickness_um_from_air_to_substrate"], LAYER_N)
            ax.plot(wl, rr*100, color=colors[method], label=f"{method}; seed={rep['seed']}")
        for lo, hi in CASES[case]:
            ax.axvspan(lo, hi, color="#bdd7e7", alpha=.30)
            ax.hlines(TARGET_R*100, lo, hi, color="black", linestyle="--", linewidth=1)
        ax.set(title=case, ylabel="Reflectance (%)", ylim=(0, 40), xlim=(2.5, 13))
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=.2)
    axes[-1].set_xlabel("Vacuum wavelength (um); shaded intervals are AR targets")
    fig.suptitle("SYNTHETIC constant n,k; normal incidence; no claim for real IR materials", fontsize=11)
    fig.savefig(output / "spectra.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), constrained_layout=True, sharey=True)
    panels = [("single_ar_3_5", (3.0, 5.0)),
              ("dual_window_ar_3_5_8_12", (3.0, 5.0)),
              ("dual_window_ar_3_5_8_12", (8.0, 12.0))]
    for ax, (case, (lo, hi)) in zip(axes, panels):
        wl = np.linspace(lo, hi, 3001)
        for method in colors:
            group = sorted([r for r in data["runs"] if r["case"] == case and r["method"] == method],
                           key=lambda r: max(m["max_R"] for m in r["higher_density_audit_metrics"]))
            if not group:
                continue
            rep = group[len(group)//2]
            rr, _ = tmm_normal(wl, rep["thickness_um_from_air_to_substrate"], LAYER_N)
            ax.plot(wl, rr*100, color=colors[method], label=method)
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1, label="R target 1%")
        ax.set(title=("Single AR" if case == "single_ar_3_5" else "Dual-window AR")+f"; {lo:g}-{hi:g} um",
               xlabel="Vacuum wavelength (um)", ylim=(0, 4), xlim=(lo, hi))
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Reflectance (%)")
    axes[0].legend(fontsize=8, loc="upper center")
    fig.suptitle("Target-window zoom; median-ranked seed per method; SYNTHETIC n,k only", fontsize=11)
    fig.savefig(output / "spectra_target_zoom.png", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    parser.add_argument("--physics-only", action="store_true")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    data = {"environment": {"python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__, "platform": platform.platform()},
        "configuration": {"materials": "SYNTHETIC constant n,k; not measured IR data",
            "incident_n": N0, "substrate_n": NS, "layer_n_from_air": LAYER_N.tolist(), "all_k": 0,
            "incidence_degrees": 0, "substrate": "semi-infinite; back surface excluded", "thickness_bounds_um": [LOWER, UPPER],
            "target_max_R": TARGET_R, "windows_um": CASES, "train_points_per_window": TRAIN_POINTS,
            "independent_validation_points_per_window": VALID_POINTS, "audit_points_per_window": AUDIT_POINTS,
            "validation_grid_note": "Validation grids are fixed independently of optimization, not disjoint holdouts: each 81/4097 grid pair shares 17 wavelengths per window, and the 4097-point grid is nested in the 16385-point grid. See independent_review_audit.json for a disjoint-interior midpoint cross-check.",
            "seeds": args.seeds, "max_actual_stack_evaluations_per_run": TOTAL_BUDGET,
            "de_population": POPULATION, "hybrid_de_budget": HYBRID_DE_BUDGET,
            "objective": "equal-window mean(max(R/0.01-1,0)^4) + 1e-4*equal-window mean((R/0.01)^2)",
            "budget_note": "Actual calls include finite-difference Jacobian calls. All methods share a 6000-call ceiling; local convergence can stop sooner. DE+local uses 4800 DE plus at most 1200 local calls. All validation excluded from the objective-call budget. Final validation and plots excluded from timing; the hybrid pre-local 4097-point diagnostic is included in recorded timing."},
        "physics_validation": validate_physics(), "classical_baselines": [], "runs": []}
    print(json.dumps(data["physics_validation"], indent=2), flush=True)
    for case, windows in CASES.items():
        for label, ds in classical_templates(windows):
            data["classical_baselines"].append({"case": case, "template": label, "thickness_um": ds.tolist(),
                    "dense_metrics": metrics(ds, windows, AUDIT_POINTS)})
    if not args.physics_only:
        for case, windows in CASES.items():
            for seed in args.seeds:
                for method in ("classic_local", "classic_de", "de_local"):
                    result = run_one(case, windows, method, seed)
                    data["runs"].append(result)
                    write_outputs(data, args.output)
                    print(f"{case:30} {method:14} seed={seed:2d} calls={result['actual_stack_evaluations_including_fd']:4d} "
                          f"time={result['optimization_wall_seconds']:.2f}s "
                          f"maxR={[round(100*m['max_R'],5) for m in result['higher_density_audit_metrics']]}% "
                          f"pass={result['all_windows_pass_dense']}", flush=True)
    write_outputs(data, args.output)
    if data["runs"] and not args.no_plot:
        plot_results(data, args.output)
    print("Outputs:", args.output, flush=True)


if __name__ == "__main__":
    main()
