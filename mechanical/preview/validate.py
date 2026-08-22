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
# --- connector relief (Pololu #5218, back connector) ---------------------
_relief_edge = (P["motor_dia"] + P["motor_fit_clear"]) / 2 + P["motor_conn_relief_d"]
_screw_y = P["motor_cap_screw_cc"] / 2
_graze = _relief_edge - (_screw_y - P["m2_tap_dia"] / 2)
chk("Connector relief clears the inboard cap screw centre",
    _relief_edge < _screw_y,
    f'relief edge {_relief_edge:.2f} < screw {_screw_y:.1f}'
    + (f' (grazes hole by {_graze:.2f} mm)' if _graze > 0 else ''))
chk("Connector relief shorter than the motor pocket",
    P["motor_conn_relief_l"] < P["motor_pocket_l"],
    f'{P["motor_conn_relief_l"]:.0f} < {P["motor_pocket_l"]:.1f}')
chk("Relief stays inside the cradle width",
    _relief_edge <= P["cradle_w"] / 2,
    f'{_relief_edge:.2f} <= {P["cradle_w"]/2:.1f}')
chk("Motor pocket longer than the motor body",
    P["motor_pocket_l"] > P["motor_body_len"],
    f'pocket {P["motor_pocket_l"]:.1f} > body {P["motor_body_len"]:.0f} '
    f'({P["motor_pocket_l"] - P["motor_body_len"]:.1f} mm axial clearance)')
# --- drive sprocket bearing ---------------------------------------------
# The sprocket rides a hub on its own bearing rather than the output shaft, so
# the wall carries the wheel load instead of the gearbox bushings.
chk("Motor shaft reaches through the bearing seat",
    P["motor_shaft_len"] >= P["drive_boss_t"] + P["tub_wall"],
    f'shaft {P["motor_shaft_len"]:.0f} >= '
    f'{P["drive_boss_t"] + P["tub_wall"]:.1f} to the wall outer face')
chk("Bearing seat fits the wall plus its shoulder slug",
    P["drive_bearing_w"] <= P["tub_wall"] + P["drive_boss_t"],
    f'{P["drive_bearing_w"]:.0f} <= {P["tub_wall"] + P["drive_boss_t"]:.1f}')
chk("Bearing seat leaves a shoulder to press against",
    P["drive_bearing_od"] > P["drive_hub_od"] + 2,
    f'seat {P["drive_bearing_od"]:.0f} > hub {P["drive_hub_od"]:.0f} + 2')
chk("Hub bore matches the motor shaft",
    abs(P["drive_bearing_id"] - P["drive_hub_od"]) < 1e-9
    and P["drive_hub_od"] > P["motor_shaft_dia"],
    f'hub {P["drive_hub_od"]:.0f} on shaft {P["motor_shaft_dia"]:.0f}, '
    f'bearing id {P["drive_bearing_id"]:.0f}')
chk("Sprocket sits on the track centreline",
    P["sprocket_x"] == P["track_cc"] / 2,
    f'{P["sprocket_x"]:.0f} mm ({P["sprocket_x"] - P["tub_width"]/2:.0f} mm '
    f'cantilever past the wall)')
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
chk("Bay ring stops clear of the motor cradle",
    P["bay_aft_y"] >= -P["wheelbase"] / 2 + P["cradle_w"] / 2,
    f'ring aft {P["bay_aft_y"]:.1f} >= cradle face '
    f'{-P["wheelbase"]/2 + P["cradle_w"]/2:.1f}')
# The trimmed ring is shorter than the pack, so it is open at the aft end by
# design -- an end wall there would land inside the pack's footprint.
chk("Bay ring is shorter than the pack (aft end must stay open)",
    P["bay_fwd_y"] - P["bay_aft_y"] < P["battery_l"],
    f'ring {P["bay_fwd_y"] - P["bay_aft_y"]:.1f} < pack {P["battery_l"]:.0f} '
    f'({abs(-6 - P["battery_l"]/2 - P["bay_aft_y"]):.1f} mm unfenced aft)')
_s_aft, _s_fwd = P["bay_aft_y"] + 5, P["bay_fwd_y"] - 7
chk("Both strap slots sit in the ring and straddle the pack centre",
    P["bay_aft_y"] < _s_aft < -6 < _s_fwd < P["bay_fwd_y"],
    f'slots at {_s_aft:.1f} and {_s_fwd:.1f} inside ring '
    f'{P["bay_aft_y"]:.1f}..{P["bay_fwd_y"]:.1f}')
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
chk("Shelf seats an m2 head over the rib centreline",
    P["pi_shelf_half_w"] >= P["pi_rib_cx"] + 2.0,
    f'plate edge {P["pi_shelf_half_w"]:.1f} >= screw {P["pi_rib_cx"]:.1f} + 2 '
    f'({P["pi_shelf_half_w"] - P["pi_rib_cx"]:.1f} mm head margin)')
chk("Shelf screws land within the rib width",
    abs(P["pi_rib_cx"] - (rib_in + P["pi_rib_t"] / 2)) < 1e-9,
    f'screw at {P["pi_rib_cx"]:.1f}, rib {rib_in:.1f}-{rib_in + P["pi_rib_t"]:.1f}')
chk("Shelf screw inset clears the plate edge",
    P["pi_shelf_screw_inset"] >= P["boss_od"] / 2,
    f'{P["pi_shelf_screw_inset"]:.0f} >= {P["boss_od"]/2:.1f}')
chk("Pi board fits the shelf plate", P["pi_w"] <= 2 * P["pi_shelf_half_w"],
    f'{P["pi_w"]:.0f} <= {2*P["pi_shelf_half_w"]:.0f}')
imu_half = (P["imu_hole_cc"] + 8) / 2
# The IMU rides the Pi-M shelf now, not the tub floor, so the checks are about
# sharing a plate with the Pi rather than dodging the battery bay ring.
chk("IMU sits aft of the Pi board on the shelf",
    P["imu_pos_y"] + imu_half + 3 <= P["pi_board_cy"] - P["pi_l"] / 2,
    f'IMU front edge {P["imu_pos_y"] + imu_half:.1f} <= board aft edge '
    f'{P["pi_board_cy"] - P["pi_l"]/2:.1f}')
chk("IMU fits across the shelf",
    abs(P["imu_pos_x"]) + imu_half <= P["pi_shelf_half_w"],
    f'{abs(P["imu_pos_x"]) + imu_half:.1f} <= {P["pi_shelf_half_w"]:.0f}')
chk("Shelf reaches aft of the IMU",
    P["pi_shelf_aft_y"] <= P["imu_pos_y"] - imu_half - 3,
    f'shelf aft {P["pi_shelf_aft_y"]:.1f} <= IMU aft edge - 3 '
    f'{P["imu_pos_y"] - imu_half - 3:.1f}')
chk("Electronics stack clears the tub rim",
    (P["ground_clearance"] + P["tub_wall"] + P["pi_shelf_z"] + P["pi_shelf_t"]
     + P["pi_standoff_h"] + 12) <= P["ground_clearance"] + P["tub_height"],
    f'board top {P["ground_clearance"] + P["tub_wall"] + P["pi_shelf_z"] + P["pi_shelf_t"] + P["pi_standoff_h"] + 12:.1f}'
    f' <= rim {P["ground_clearance"] + P["tub_height"]:.1f}')
_cols = j5_params.pi_column_ys(P)
chk("Shelf columns clear the idler rod",
    max(_cols) + P["pi_column_len"] / 2
    <= P["idler_y_nom"] - P["idler_axle_dia"] / 2 - 2,
    f'front column face {max(_cols) + P["pi_column_len"]/2:.1f} <= rod aft '
    f'{P["idler_y_nom"] - P["idler_axle_dia"]/2 - 2:.1f}')
chk("Shelf columns clear the battery bay ring",
    P["pi_rib_x_in"] >= (P["battery_w"] + 2 * P["battery_clear"]) / 2 + 2,
    f'{P["pi_rib_x_in"]:.1f} >= {(P["battery_w"] + 2*P["battery_clear"])/2 + 2:.1f}')

# --- track treads --------------------------------------------------------
chk("Tread relief leaves a usable continuous band",
    P["track_band_t"] >= 1.6,
    f'{P["track_band_t"]:.1f} mm continuous under a {P["tread_depth"]:.1f} mm tread')
chk("Tread depth does not change the ride height",
    abs(P["track_outer_r"] - (P["sprocket_pitch_dia"] / 2 + P["track_thickness"])) < 1e-9,
    f'tip radius {P["track_outer_r"]:.1f} unchanged')
chk("Chevron lean is self-supporting",
    P["tread_angle"] <= 45,
    f'{P["tread_angle"]:.0f} deg off vertical in the print orientation')
chk("Ground run always spans several chevrons",
    P["track_straight_len"] /
    ((2 * P["track_straight_len"] + 2 * math.pi * P["tread_valley_r"])
     / P["tread_count"]) >= 4,
    f'{P["track_straight_len"] / ((2*P["track_straight_len"] + 2*math.pi*P["tread_valley_r"])/P["tread_count"]):.1f} chevrons in contact')

# Bearings sit in the wheel hubs, so the wall carries only a locating feature.
# The idler's is now a slot, and the carrier clamped over it is what gives the
# rod its bearing length -- the old inner-face pad is gone with the fixed hole.
chk("Idler rod bearing length worth having",
    P["idler_carrier_t"] >= 1.5 * P["idler_axle_dia"],
    f'carrier {P["idler_carrier_t"]:.1f} >= '
    f'{1.5*P["idler_axle_dia"]:.1f} (1.5x shaft dia)')
chk("Idler slot leaves the rod somewhere to go",
    P["idler_slot_len"] > P["axle_hole_dia"] + 1,
    f'{P["idler_slot_len"]:.1f} > {P["axle_hole_dia"] + 1:.1f}')
chk("Track loop closes inside the idler slot travel",
    abs(P["idler_y_nom"] - P["idler_slot_cy"]) <= P["idler_slot_travel"] / 2 + 1e-9,
    f'zero-strain idler y {P["idler_y_nom"]:.2f} within '
    f'{P["idler_slot_travel"]/2:.1f} mm of slot centre {P["idler_slot_cy"]:.2f}')

# --- road wheels ---------------------------------------------------------
_rw_ys = j5_params.roadwheel_ys(P)
chk("Road wheels reach the track inner surface",
    abs((P["roadwheel_axle_z"] - P["roadwheel_dia"] / 2) - P["track_thickness"]) < 1e-9,
    f'wheel bottom {P["roadwheel_axle_z"] - P["roadwheel_dia"]/2:.1f} == '
    f'band inner face {P["track_thickness"]:.1f}')
chk("Road wheels clear each other",
    all(abs(a - b) > P["roadwheel_dia"] + 1
        for i, a in enumerate(_rw_ys) for b in _rw_ys[i+1:]),
    f'centres {[round(y,1) for y in _rw_ys]}, need > {P["roadwheel_dia"]+1:.0f} apart')
chk("Skirt carries the road-wheel hole",
    P["skirt_z_bottom"] + 2.5 <= P["roadwheel_axle_z"] - P["axle_hole_dia"] / 2,
    f'skirt bottom {P["skirt_z_bottom"]:.1f}+2.5 <= hole bottom '
    f'{P["roadwheel_axle_z"] - P["axle_hole_dia"]/2:.1f}')

# --- rear anti-tip tail --------------------------------------------------
chk("Anti-tip roller floats clear of the floor",
    P["tail_axle_z"] - P["caster_wheel_dia"] / 2 > 2.0,
    f'{P["tail_axle_z"] - P["caster_wheel_dia"]/2:.1f} mm float')
chk("Roller is the tail's lowest point",
    P["caster_pivot_z"] - P["tail_boom_h"] / 2 > P["tail_axle_z"],
    f'boom underside {P["caster_pivot_z"] - P["tail_boom_h"]/2:.1f} > axle '
    f'{P["tail_axle_z"]:.1f}')

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
