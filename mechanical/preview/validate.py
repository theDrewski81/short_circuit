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

# --- motor cradle + retention cap ----------------------------------------
# The cap screws set the cradle width, so these guard the geometry that
# build_chassis.motor_cradles()/motor_cap() derive rather than choose.
cradle_l = P["cradle_l"]
cradle_w = P["cradle_w"]
slot_half = (P["motor_dia"] + P["motor_fit_clear"]) / 2
col_inner = P["motor_cap_screw_cc"] / 2 - P["boss_od"] / 2
chk("Cap screw columns clear the motor slot", col_inner >= slot_half,
    f'column inner edge {col_inner:.1f} >= slot half-width {slot_half:.1f}')
chk("Cap screws land on the cradle top face (X)",
    P["motor_cap_screw_x"] / 2 + P["boss_od"] / 2 <= cradle_l / 2,
    f'{P["motor_cap_screw_x"]/2 + P["boss_od"]/2:.1f} <= {cradle_l/2:.1f}')
chk("Motor cradle inside the tub rear wall",
    P["wheelbase"] / 2 + cradle_w / 2 <= P["tub_len"] / 2,
    f'cradle rear edge {P["wheelbase"]/2 + cradle_w/2:.1f} <= {P["tub_len"]/2:.1f}')
# The motor cannot be lowered straight onto its seat: the shaft would have to
# pass through solid side wall. It goes in shaft-clear and slides outboard, so
# the cradle has to be long enough to hold it at that drop position.
chk("Cradle swallows motor body + shaft",
    cradle_l >= P["motor_body_len"] + P["motor_shaft_len"],
    f'{cradle_l:.1f} >= {P["motor_body_len"] + P["motor_shaft_len"]:.0f}')
chk("Drop-in slot longer than the motor body",
    cradle_l > P["motor_body_len"],
    f'slot {cradle_l:.1f} > body {P["motor_body_len"]:.0f} '
    f'({cradle_l - P["motor_body_len"]:.1f} mm axial clearance)')
chk("Cradle inboard end clears the battery bay cavity",
    P["tub_width"] / 2 - P["tub_wall"] - cradle_l
    >= P["battery_w"] / 2 + P["battery_clear"],
    f'{P["tub_width"]/2 - P["tub_wall"] - cradle_l:.1f} >= '
    f'{P["battery_w"]/2 + P["battery_clear"]:.1f}')
rear_span = P["tub_len"] / 2 - P["tub_wall"] - P["wheelbase"] / 2 - P["motor_cap_wall_clear"]
cap_w = min(cradle_w, 2 * rear_span)
hole_r = P["m2_tap_dia"] / 2 + 0.3
chk("Cap clears the tub rear wall", cap_w / 2 <= rear_span + 1e-9,
    f'cap half-width {cap_w/2:.2f} <= free span {rear_span:.2f}')
chk("Cap plate still covers its screw holes",
    cap_w / 2 >= P["motor_cap_screw_cc"] / 2 + hole_r + 0.8,
    f'margin round hole {cap_w/2 - P["motor_cap_screw_cc"]/2 - hole_r:.2f} mm')
chk("Cap saddle grips (tongue narrower than motor)",
    P["motor_dia"] + P["motor_fit_clear"] - 2 * P["motor_cap_fit"] < P["motor_dia"],
    f'tongue {P["motor_dia"] + P["motor_fit_clear"] - 2*P["motor_cap_fit"]:.1f} < motor {P["motor_dia"]:.1f}')

# --- internal packaging --------------------------------------------------
inner_w = P["tub_width"] - 2 * P["tub_wall"]
inner_l = P["tub_len"] - 2 * P["tub_wall"]
chk("Battery bay fits tub interior (Y)", P["battery_l"] + 2 * P["battery_clear"] <= inner_l,
    f'{P["battery_l"] + 2 * P["battery_clear"]:.0f} <= {inner_l:.1f}')
chk("Pi-M board fits across interior", P["pi_l"] <= inner_w, f'{P["pi_l"]:.0f} <= {inner_w:.1f}')

# --- keep-outs -----------------------------------------------------------
# Added after the first tub was printed. Every one of these guards a case where
# two features each independently wanted the same volume and the fuse silently
# gave it to both: an overlapping fuse is legal and still returns one solid, so
# the existing single-solid check cannot see it.
rib_in = P["pi_rib_x_in"]
chk("Shelf ribs clear the battery envelope",
    rib_in >= P["battery_w"] / 2 + P["battery_clear"],
    f'rib inner face {rib_in:.1f} >= pack half-width + clear '
    f'{P["battery_w"]/2 + P["battery_clear"]:.1f}')
chk("Shelf plate reaches the ribs that carry it",
    P["pi_shelf_half_w"] >= rib_in + (P["tub_wall"] + 6) / 2,
    f'{P["pi_shelf_half_w"]:.1f} >= {rib_in + (P["tub_wall"] + 6)/2:.1f}')
chk("Pi board fits the shelf plate", P["pi_w"] <= 2 * P["pi_shelf_half_w"],
    f'{P["pi_w"]:.0f} <= {2*P["pi_shelf_half_w"]:.0f}')
imu_half = (P["imu_hole_cc"] + 8) / 2
chk("IMU pad clear of the battery bay",
    P["imu_pos_x"] - imu_half >= P["battery_w"] / 2 + P["battery_clear"] + 2,
    f'pad inner edge {P["imu_pos_x"] - imu_half:.1f} >= bay outer '
    f'{P["battery_w"]/2 + P["battery_clear"] + 2:.1f}')
chk("IMU screws reachable from above (aft of the shelf)",
    P["imu_pos_y"] + imu_half <= (P["wheelbase"] / 2 - 28) - (P["pi_l"] + 8) / 2,
    f'pad front edge {P["imu_pos_y"] + imu_half:.1f} <= shelf aft edge '
    f'{(P["wheelbase"]/2 - 28) - (P["pi_l"] + 8)/2:.1f}')
chk("IMU pad inside the tub interior",
    P["imu_pos_x"] + imu_half <= P["tub_width"] / 2 - P["tub_wall"],
    f'{P["imu_pos_x"] + imu_half:.1f} <= {P["tub_width"]/2 - P["tub_wall"]:.1f}')
# Bearings sit in the wheel hubs, so the wall only carries a locating hole --
# but the pad behind it is what gives the shaft usable bearing length.
chk("Idler shaft bearing length worth having",
    P["tub_wall"] + P["idler_pad_t"] >= 1.5 * P["idler_axle_dia"],
    f'{P["tub_wall"] + P["idler_pad_t"]:.1f} >= '
    f'{1.5*P["idler_axle_dia"]:.1f} (1.5x shaft dia)')
chk("Idler pad wider than its hole",
    P["idler_pad_od"] > P["axle_hole_dia"] + 4,
    f'{P["idler_pad_od"]:.0f} > {P["axle_hole_dia"] + 4:.1f}')

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
