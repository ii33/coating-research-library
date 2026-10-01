#!/usr/bin/env python3
"""Reproduce ideal planetary-coating kinematics; no coating simulation."""

from fractions import Fraction
import json
from math import gcd

ZS = 120
WC_RPM = Fraction(15)
SECONDS_PER_CARRIER_REV = Fraction(60, 15)


def compute(zp: int) -> dict:
    relative_rpm = Fraction(ZS, zp) * WC_RPM
    absolute_rpm = WC_RPM + relative_rpm
    planet_turns_per_carrier_turn = absolute_rpm / WC_RPM

    # The carrier returns after an integer number of revolutions. Find the
    # smallest such number that also returns the workpiece attitude mod 1 turn.
    carrier_revs_to_close = planet_turns_per_carrier_turn.denominator
    workpiece_turns_to_close = planet_turns_per_carrier_turn * carrier_revs_to_close
    closure_seconds = SECONDS_PER_CARRIER_REV * carrier_revs_to_close

    # Attitude increment observed at the same carrier azimuth each carrier turn,
    # reduced to a turn in [0, 1).
    phase_increment = planet_turns_per_carrier_turn % 1
    phase_count = phase_increment.denominator if phase_increment else 1

    return {
        "planet_teeth": zp,
        "sun_teeth": ZS,
        "carrier_rpm_ccw_positive": float(WC_RPM),
        "planet_relative_carrier_rpm_exact": f"{relative_rpm.numerator}/{relative_rpm.denominator}",
        "planet_relative_carrier_rpm": float(relative_rpm),
        "planet_absolute_rpm_exact": f"{absolute_rpm.numerator}/{absolute_rpm.denominator}",
        "planet_absolute_rpm": float(absolute_rpm),
        "planet_turns_per_carrier_turn_exact": (
            f"{planet_turns_per_carrier_turn.numerator}/{planet_turns_per_carrier_turn.denominator}"
        ),
        "carrier_orbit_seconds": float(SECONDS_PER_CARRIER_REV),
        "attitude_phase_increment_per_carrier_turn_exact": (
            f"{phase_increment.numerator}/{phase_increment.denominator}"
        ),
        "attitude_phase_increment_per_carrier_turn_degrees": float(phase_increment * 360),
        "distinct_attitude_phases_at_same_carrier_azimuth": phase_count,
        "full_pose_closure_carrier_revolutions": carrier_revs_to_close,
        "full_pose_closure_workpiece_revolutions": (
            f"{workpiece_turns_to_close.numerator}/{workpiece_turns_to_close.denominator}"
        ),
        "full_pose_closure_seconds": float(closure_seconds),
        "pitch_center_distance_in_modules": float(Fraction(ZS + zp, 2)),
    }


results = [compute(36), compute(37)]
assert results[0]["full_pose_closure_seconds"] == 12.0
assert results[1]["full_pose_closure_seconds"] == 148.0
assert gcd(9, 37) == 1
print(json.dumps({
    "model": "ideal rigid external spur gears; fixed sun, rotating carrier, planet shaft rigidly coupled to workpiece",
    "sign_convention": "top view, counterclockwise positive",
    "assumptions": [
        "sun gear fixed at 0 rpm",
        "carrier at +15 rpm",
        "direct external sun-planet mesh",
        "workpiece angular velocity equals planet gear absolute angular velocity",
        "no backlash, slip, compliance, deposition or coating simulation",
    ],
    "results": results,
    "relative_center_distance_change_37_vs_36_in_modules": 0.5,
}, indent=2))
