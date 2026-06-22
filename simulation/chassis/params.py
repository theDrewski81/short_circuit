"""Simulation parameter bridge for the Johnny 5 tread chassis.

The mechanical build (mechanical/freecad/params.csv) is the single source of
truth for geometry. This module re-derives only the quantities the MuJoCo
model needs, in SI units (metres, kilograms, newton-metres), so the sim never
drifts from the CAD. Anything not traceable to params.csv -- the lumped-mass
split, motor torque limit, friction -- is declared here with a stated basis so
it is reviewable in one place. Values to confirm on the bench are listed in
TUNING.md.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
# mechanical/freecad/params.csv relative to simulation/chassis/. The
# J5_PARAMS_CSV env var overrides this (used by CI / sandboxed runs where the
# repo layout is mounted at a different absolute path).
_CSV = os.environ.get(
    "J5_PARAMS_CSV",
    os.path.normpath(os.path.join(_HERE, "..", "..", "mechanical", "freecad", "params.csv")),
)


def _load_csv(path: str = _CSV) -> dict[str, float]:
    out: dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            if not name or name.startswith("#"):
                continue
            out[name] = float(row["value"])
    return out


# ---------------------------------------------------------------------------
# Non-CAD modelling constants. Each carries its basis so a reviewer can audit
# it without leaving this file. Tunable values are surfaced again in TUNING.md;
# this is the authoritative default.
# ---------------------------------------------------------------------------

# Pololu 150:1 micro metal gearmotor HPCB 12V: ~0.41 N*m (59 oz*in) stall at
# 12 V. Run battery-direct on a 2S pack at ~7.4 V nominal, torque scales ~linearly
# with voltage -> ~0.25 N*m per motor at the output shaft. Confirm against a
# measured stall test on the bench (Phase 02 Task 6) and update TUNING.md.
MOTOR_STALL_TORQUE_NM = 0.25

# Pololu 150:1 HPCB free-run ~200 rpm at 12 V -> ~123 rpm at 7.4 V
# = ~12.9 rad/s no-load wheel speed (-> ~0.30 m/s surface). Sets the actuator
# torque-speed droop (back-EMF proxy) and the encoder-velocity normalisation.
MOTOR_NO_LOAD_SPEED_RAD_S = 12.9

# Ground friction. Hardwood/tile default per the phase brief. MuJoCo geom
# friction triple (slide, torsional, rolling). Contacts use condim=3 (slide
# only), so the slide term dominates; torsional/rolling terms are carried for a
# future condim bump. Skid-steer turn resistance therefore comes from the
# lateral slide of four wheels spread over the wheelbase -- realistic for a track.
GROUND_FRICTION = (1.0, 0.01, 0.0001)
WHEEL_FRICTION = (1.2, 0.02, 0.0001)  # TPU lugged band grips harder than the floor

# Mass split (kg). From mechanical/preview/components.csv:
#   assembled 6-servo + caster build ~1.311 kg; rolling elements
#   (2 tracks + 2 sprockets + 2 idlers + 4 road wheels) ~0.114 kg.
# The trunk carries everything else (~1.197 kg) and rides on the treads.
TRUNK_MASS_KG = 1.197
ROLLING_MASS_KG = 0.114
WHEEL_MASS_KG = ROLLING_MASS_KG / 2.0  # split across the two driven-wheel bodies

# Trunk centre-of-mass height above ground (m). The robot is tall (head at
# ~0.370 m) but mass is bottom-heavy: battery (130 g) and chassis shell sit low,
# torso/head/arms (~0.37 kg) sit high. A mass-weighted estimate lands near the
# top of the tub. Held as an explicit, tunable figure because the roll/pitch
# reward and tip stability are sensitive to it. Refine from the FreeCAD CoM
# report or a measured balance test; track drift in TUNING.md.
COM_HEIGHT_M = 0.110


@dataclass(frozen=True)
class ChassisParams:
    # --- geometry (m) ---
    wheel_radius: float          # sprocket pitch radius + track band thickness
    axle_z: float                # axle line height above ground
    track_cc: float              # left/right drive-wheel centre-to-centre
    track_width: float           # TPU band width (drive-wheel geom half-length)
    wheelbase: float             # sprocket centre to idler centre (footprint span)
    footprint_len: float         # ground-contact length
    tub_w: float                 # trunk box width
    tub_l: float                 # trunk box length
    tub_h: float                 # trunk box height (tub + deck)
    ground_clearance: float
    com_height: float            # trunk CoM above ground
    caster_wheel_radius: float
    caster_trail: float          # behind rear track edge
    # --- mass (kg) ---
    trunk_mass: float
    wheel_mass: float
    caster_mass: float
    # --- actuation ---
    motor_stall_torque: float    # N*m per side (one physical motor)
    motor_no_load_speed: float   # rad/s
    # --- contact ---
    ground_friction: tuple[float, float, float]
    wheel_friction: tuple[float, float, float]


def get() -> ChassisParams:
    """Load params.csv and return SI-unit chassis parameters for the MJCF."""
    p = _load_csv()
    mm = 1e-3

    sprocket_pitch_dia = p["sprocket_pitch_dia"] * mm
    track_thickness = p["track_thickness"] * mm
    wheel_radius = sprocket_pitch_dia / 2.0 + track_thickness  # = axle_z derived below

    return ChassisParams(
        wheel_radius=wheel_radius,
        axle_z=wheel_radius,  # axle sits one wheel-radius above the contact line
        track_cc=p["track_cc"] * mm,
        track_width=p["track_width"] * mm,
        wheelbase=p["wheelbase"] * mm,
        footprint_len=(p["wheelbase"] + p["sprocket_pitch_dia"]) * mm,
        tub_w=p["tub_width"] * mm,
        tub_l=p["tub_len"] * mm,
        tub_h=(p["tub_height"] + p["deck_wall"]) * mm,
        ground_clearance=p["ground_clearance"] * mm,
        com_height=COM_HEIGHT_M,
        caster_wheel_radius=p["caster_wheel_dia"] / 2.0 * mm,
        caster_trail=p["caster_trail"] * mm,
        trunk_mass=TRUNK_MASS_KG,
        wheel_mass=WHEEL_MASS_KG,
        caster_mass=0.020,  # printed wheel + arm, components.csv
        motor_stall_torque=MOTOR_STALL_TORQUE_NM,
        motor_no_load_speed=MOTOR_NO_LOAD_SPEED_RAD_S,
        ground_friction=GROUND_FRICTION,
        wheel_friction=WHEEL_FRICTION,
    )


if __name__ == "__main__":
    cp = get()
    for field in cp.__dataclass_fields__:
        print(f"{field:22s} {getattr(cp, field)}")
