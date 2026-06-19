"""FreeCAD-free sanity checks on the Johnny 5 parameters.

Bed-fit, ground/motor clearance, internal packaging, full-stack height, arms,
head + articulated brow, and a rough PLA mass estimate before printing.
Run: python3 validate.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "freecad"))
import j5_params

P = j5_params.get()
checks = []


def chk(name, ok, detail):
    checks.append((ok, name, detail))


# --- bed fit -------------------------------------------------------------
chk("Tub fits bed X", P["tub_width"] <= P["bed_x"], f'{P["tub_width"]:.0f} <= {P["bed_x"]:.0f}')
chk("Tub fits bed Y", P["tub_len"] <= P["bed_y"], f'{P["tub_len"]:.0f} <= {P["bed_y"]:.0f}')

# --- track packaging -----------------------------------------------------
chk("Tub sits inside inner track faces",
    P["tub_width"] / 2 <= P["track_cc"] / 2 - P["track_width"] / 2,
    f'half-tub {P["tub_width"]/2:.1f} <= {P["track_cc"]/2 - P["track_width"]/2:.1f}')

# --- ground / motor clearance -------------------------------------------
motor_bottom = P["axle_z"] - P["motor_dia"] / 2
chk("Main belly clearance in 15-20 band", 15 <= P["ground_clearance"] <= 20, f'{P["ground_clearance"]:.0f} mm')
chk("Motor lower edge clears ground >= 15", motor_bottom >= 15, f'motor bottom {motor_bottom:.1f} mm')

# --- internal packaging --------------------------------------------------
inner_w = P["tub_width"] - 2 * P["tub_wall"]
inner_l = P["tub_len"] - 2 * P["tub_wall"]
chk("Battery bay fits tub interior (Y)", P["battery_l"] + 2 * P["battery_clear"] <= inner_l,
    f'{P["battery_l"] + 2 * P["battery_clear"]:.0f} <= {inner_l:.1f}')
chk("Pi-M board fits across interior", P["pi_l"] <= inner_w, f'{P["pi_l"]:.0f} <= {inner_w:.1f}')

# --- full stack height ---------------------------------------------------
chk("Total height in floor-roaming band",
    P["height_target_min"] <= P["total_h"] <= P["height_target_max"],
    f'{P["total_h"]:.0f} mm (band {P["height_target_min"]:.0f}-{P["height_target_max"]:.0f})')

# --- torso ---------------------------------------------------------------
chk("Torso seats on chassis (base <= track width)", P["torso_w_base"] <= P["overall_track_width"],
    f'{P["torso_w_base"]:.0f} <= {P["overall_track_width"]:.0f}')
chk("Deck bolt rectangle fits torso footprint",
    P["torso_iface_dx"] < P["torso_w_base"] and P["torso_iface_dy"] < P["torso_depth"],
    f'{P["torso_iface_dx"]:.0f}x{P["torso_iface_dy"]:.0f} in {P["torso_w_base"]:.0f}x{P["torso_depth"]:.0f}')
chk("Head-yaw servo fits neck riser",
    P["scs_body_h"] <= P["neck_h"] and max(P["scs_body_l"], P["scs_body_w"]) <= P["neck_dia"],
    f'servo {P["scs_body_h"]:.0f} <= neck {P["neck_h"]:.0f}')

# --- arms ----------------------------------------------------------------
reach = P["upper_arm_len"] + P["forearm_len"] * math.cos(math.radians(P["elbow_angle"]))
chk("Arm effective lever within torque budget", reach <= P["arm_lever_max"],
    f'reach {reach:.0f} <= {P["arm_lever_max"]:.0f} mm')
sec, w = P["arm_section"], P["arm_wall"]
arm_mass = (((sec * sec - (sec - 2 * w) ** 2) * (P["upper_arm_len"] + P["forearm_len"]) + 9000)
            / 1000.0 * P["pla_density"])
chk("Per-arm mass within budget", arm_mass <= P["arm_mass_budget"], f'~{arm_mass:.0f} g')

# --- head + brow ---------------------------------------------------------
chk("Head shell half fits bed", P["head_w"] <= P["bed_x"] and P["head_h"] <= P["bed_y"],
    f'{P["head_w"]:.0f} x {P["head_h"]:.0f}')
chk("Eyes fit across the face",
    P["eye_spacing"] + P["eye_dia"] <= P["head_w"] - 2 * P["head_wall"],
    f'{P["eye_spacing"]:.0f}+{P["eye_dia"]:.0f} <= {P["head_w"] - 2 * P["head_wall"]:.1f}')
chk("Brow pivots inside head width", 2 * P["brow_pivot_offset"] < P["head_w"],
    f'2x{P["brow_pivot_offset"]:.0f} < {P["head_w"]:.0f}')
chk("Brow blades clear centre (no collision)",
    P["brow_blade_len"] <= P["brow_pivot_offset"] - 3,
    f'len {P["brow_blade_len"]:.0f} <= {P["brow_pivot_offset"] - 3:.0f} (tips gap {2*(P["brow_pivot_offset"]-P["brow_blade_len"]):.0f} mm)')
chk("Brow servo fits inside head",
    P["scs_body_l"] <= P["head_w"] - 2 * P["head_wall"] and P["scs_body_h"] <= P["head_depth"] - 2 * P["head_wall"],
    f'servo {P["scs_body_l"]:.0f}x{P["scs_body_h"]:.0f} in head')
chk("Eyes + camera fit head height",
    P["head_h"] * 0.62 + P["eye_dia"] / 2 <= P["head_h"],
    f'eye top {P["head_h"]*0.62 + P["eye_dia"]/2:.0f} <= {P["head_h"]:.0f}')

# --- rough chassis PLA mass ---------------------------------------------
W, Lg, H, wall = P["tub_width"], P["tub_len"], P["tub_height"], P["tub_wall"]
mass = ((W * Lg + 2 * W * H + 2 * Lg * H) * wall * 1.10 + W * Lg * P["deck_wall"] * 0.85) / 1000.0 * P["pla_density"]
chk("Chassis structural mass sane (<300 g)", mass < 300, f'~{mass:.0f} g')

# --- report --------------------------------------------------------------
print("\n  Johnny 5 - parameter validation")
print("  " + "-" * 56)
fails = 0
for ok, name, detail in checks:
    fails += 0 if ok else 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:42s} {detail}")
print("  " + "-" * 56)
print(f"  footprint {P['footprint_len']:.0f}x{P['overall_track_width']:.0f} mm | "
      f"height {P['total_h']:.0f} mm | head {P['head_w']:.0f}x{P['head_h']:.0f} mm")
print(f"  {'ALL CHECKS PASS' if fails == 0 else str(fails) + ' CHECK(S) FAILED'}\n")
sys.exit(1 if fails else 0)
