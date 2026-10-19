"""Standalone, standard-library-only audit of the two archived prescriptions.

No coat_sim, unpublished v3 code, NumPy, SciPy, network, or installation required.
Positive n+i*k, normal incidence, air -> coating -> ZnS half-space.
"""
import argparse
import bisect
import cmath
import csv
import hashlib
import json
import math
from pathlib import Path


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class Material:
    def __init__(self, path):
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.waves = [float(row["wavelength_nm"]) for row in rows]
        self.values = [complex(float(row["n"]), float(row["k"])) for row in rows]
        if len(self.waves) < 2 or any(b <= a for a, b in zip(self.waves, self.waves[1:])):
            raise ValueError("Source wavelengths must strictly increase")
        if any(z.real <= 0 or z.imag < 0 for z in self.values):
            raise ValueError("Require passive, positive-index explicit n/k")

    def sample(self, wavelength):
        if not self.waves[0] <= wavelength <= self.waves[-1]:
            raise ValueError("Wavelength is outside the actual source n/k domain")
        j = bisect.bisect_right(self.waves, wavelength)
        if j == len(self.waves):
            return self.values[-1]
        i = max(0, j - 1)
        t = (wavelength - self.waves[i]) / (self.waves[j] - self.waves[i])
        return self.values[i] + t * (self.values[j] - self.values[i])


def response(wavelength, prescription, materials):
    # Characteristic matrices map the exit fields to incident fields.
    a, b, c, d = 1 + 0j, 0j, 0j, 1 + 0j
    for layer in reversed(prescription["layers"]):
        n = materials[layer["material"]].sample(wavelength)
        delta = 2 * math.pi * n * layer["thickness_nm"] / wavelength
        co, si = cmath.cos(delta), -1j * cmath.sin(delta)
        a, b, c, d = a * co + b * n * si, a * si / n + b * co, c * co + d * n * si, c * si / n + d * co
    ns = materials["ZnS"].sample(wavelength)
    denominator = a + b * ns + c + d * ns
    r = (a + b * ns - c - d * ns) / denominator
    t = 2 / denominator
    reflected = abs(r) ** 2
    transmitted = ns.real * abs(t) ** 2
    absorption = 1 - reflected - transmitted
    if not all(math.isfinite(x) for x in (reflected, transmitted, absorption)):
        raise ArithmeticError("Nonfinite optical response")
    return reflected, transmitted, absorption


def bounded_minimum(function, tolerance=1e-12, maximum=500):
    # Golden-section minimization in dimensionless t in [0,1].
    lo, hi = 0.0, 1.0
    factor = (math.sqrt(5) - 1) / 2
    x1, x2 = hi - factor * (hi - lo), lo + factor * (hi - lo)
    f1, f2 = function(x1), function(x2)
    for _ in range(maximum):
        if hi - lo <= tolerance:
            break
        if f1 < f2:
            hi, x2, f2 = x2, x1, f1
            x1 = hi - factor * (hi - lo)
            f1 = function(x1)
        else:
            lo, x1, f1 = x1, x2, f2
            x2 = lo + factor * (hi - lo)
            f2 = function(x2)
    candidates = [(x1, f1), (x2, f2), (0.0, function(0.0)), (1.0, function(1.0))]
    return min(candidates, key=lambda pair: pair[1])


def audit(package, route, materials, targets, samples):
    prescription = load_json(package / "prescriptions" / (route + ".json"))
    expected = load_json(package / "results" / "final_metrics.json")[route]
    windows, calls = [], 0

    def evaluate(wavelength):
        nonlocal calls
        calls += 1
        return response(wavelength, prescription, materials)

    for lo, hi in targets["windows_nm"]:
        dense = [lo + (hi - lo) * i / (samples - 1) for i in range(samples)]
        shifted = [(a + b) / 2 for a, b in zip(dense, dense[1:])]
        knots = [w for material in materials.values() for w in material.waves if lo <= w <= hi]
        wavelengths = sorted(set(dense + shifted + knots))
        values = [evaluate(w) for w in wavelengths]
        row = {"window_nm": [lo, hi], "grid_points": len(wavelengths)}
        brackets = 0
        for label, column, sign in (("Rmax", 0, -1), ("Tmin", 1, 1), ("Amax", 2, -1)):
            j = min(range(len(values)), key=lambda i: sign * values[i][column])
            worst, wavelength = values[j][column], wavelengths[j]
            for i in range(1, len(values) - 1):
                if sign * values[i][column] < sign * values[i - 1][column] and sign * values[i][column] <= sign * values[i + 1][column]:
                    left, right = wavelengths[i - 1], wavelengths[i + 1]
                    brackets += 1

                    def function(t):
                        return sign * evaluate(left + (right - left) * t)[column]

                    t, value = bounded_minimum(function)
                    value *= sign
                    if sign * value < sign * worst:
                        worst, wavelength = value, left + (right - left) * t
            row[label], row[label + "_nm"] = worst, wavelength
        row["local_extremum_brackets"] = brackets
        windows.append(row)
    guard, tolerance = targets["research_guard"], targets["acceptable_normalized_error"]
    targets_met = all(row["Rmax"] <= guard["R_upper"] + tolerance and row["Tmin"] >= guard["T_lower"] - tolerance for row in windows)
    metric_difference = max(abs(row[metric] - old[metric]) for row, old in zip(windows, expected["windows"]) for metric in ("Rmax", "Tmin", "Amax"))
    return {"route": route, "windows": windows, "targets_met": targets_met, "max_metric_difference_from_original_audit": metric_difference, "original_metrics_match": metric_difference <= 2e-9, "scalar_physical_evaluations": calls, "continuous_certificate": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--samples", type=int, default=10001)
    parser.add_argument("--route", choices=("A", "B", "both"), default="both")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.samples < 3:
        parser.error("--samples must be at least3")
    targets = load_json(args.package / "targets.json")
    metadata = load_json(args.package / "materials" / "sources.json")
    materials = {}
    for row in metadata["materials"]:
        path = args.package / row["data_file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["packaged_data_sha256"]:
            raise ValueError("Packaged optical data checksum mismatch: " + row["id"])
        materials[row["id"]] = Material(path)
    routes = ("A", "B") if args.route == "both" else (args.route,)
    result = {"kernel": "standalone characteristic matrix and raw-table linear interpolation", "dependencies": "Python standard library only", "normal_incidence_only": True, "transmission_definition": "power flux entering ZnS half-space", "dense_points_per_window": args.samples, "shifted_points_per_window": args.samples - 1, "source_knots_included": True, "dimensionless_extremum_tolerance": 1e-12, "routes": {route: audit(args.package, route, materials, targets, args.samples) for route in routes}}
    passed = all(row["targets_met"] and row["original_metrics_match"] for row in result["routes"].values())
    result["verification_passed"] = passed
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
