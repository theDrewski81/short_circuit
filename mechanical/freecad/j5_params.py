"""Parameter loader for the Johnny 5 mechanical build scripts.

Pure-Python, no FreeCAD dependency, so the same loader feeds both the FreeCAD
build scripts and the (FreeCAD-free) validation / preview scripts.

Source of truth is params.csv, sitting next to this file. Derived geometry is
computed once, here, so every consumer agrees on the same numbers.
"""

import csv
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CSV = os.path.join(_HERE, "params.csv")


def load_raw(path=_CSV):
    """Return {name: float} from params.csv, ignoring comment/blank rows."""
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            if not name or name.startswith("#"):
                continue
            out[name] = float(row["value"])
    return out


def derive(p):
    """Add computed geometry to the raw parameter dict (returns the same dict)."""
    p["overall_track_width"] = p["track_cc"] + p["track_width"]          # outer track-to-track
    p["tub_inner_gap"] = p["track_cc"] - p["track_width"]                # between inner track faces
    p["footprint_len"] = p["wheelbase"] + p["sprocket_pitch_dia"]        # ground contact length
    # axle sits at pitch radius + track band thickness above the ground contact line
    p["axle_z"] = p["sprocket_pitch_dia"] / 2.0 + p["track_thickness"]
    p["wheel_outer_r"] = p["sprocket_pitch_dia"] / 2.0 + p["track_thickness"]
    p["base_height_total"] = p["ground_clearance"] + p["tub_height"]     # underside floor to deck top
    # Motor cradle. Derived here, not in the build script, because validate.py
    # was re-deriving it independently and the two drifted apart.
    # The motor drops straight down into its pocket: nothing of it passes
    # through the side wall, because the sprocket rides a hub on its own
    # bearing rather than on the output shaft. Length is therefore the body,
    # plus axial clearance, plus the material reserved inboard of the wall for
    # the bearing seat shoulder.
    p["cradle_l"] = (p["motor_body_len"] + p["motor_insert_margin"]
                     + p["drive_boss_t"])
    p["cradle_w"] = p["motor_cap_screw_cc"] + p["boss_od"]
    p["motor_pocket_l"] = p["cradle_l"] - p["drive_boss_t"]   # usable slot length
    p["sprocket_x"] = p["track_cc"] / 2.0                     # sprocket centreline
    # Pi-M shelf ribs. Derived once so the tub's tapped holes and the separate
    # shelf plate's clearance holes cannot land in different places.
    p["pi_rib_t"] = p["tub_wall"] + 6.0
    p["pi_rib_cx"] = p["pi_rib_x_in"] + p["pi_rib_t"] / 2.0
    # One electronics shelf: the Pi board forward, the IMU breadboard aft.
    # Front edge stays where the Pi-only plate had it; the aft edge runs back
    # over ground the IMU used to occupy on the tub floor, and now far enough
    # past it to take the breadboard's 50.8 mm long axis plus the loom slot.
    p["pi_board_cy"] = p["wheelbase"] / 2.0 - 28.0
    p["pi_shelf_fwd_y"] = p["pi_board_cy"] + (p["pi_l"] + 8.0) / 2.0
    p["pi_shelf_aft_y"] = (p["pi_board_cy"] - (p["pi_l"] + 8.0) / 2.0
                           - p["pi_shelf_aft_ext"])
    p["pi_shelf_len"] = p["pi_shelf_fwd_y"] - p["pi_shelf_aft_y"]
    p["pi_shelf_cy"] = (p["pi_shelf_fwd_y"] + p["pi_shelf_aft_y"]) / 2.0
    # Aft loom slot centre. Derived here because the plate cuts it and the
    # breadboard-clearance guards measure against it, and those were about to
    # carry two private copies of the same 5.5 mm offset.
    p["pi_loom_slot_cy"] = p["pi_shelf_aft_y"] + 5.5
    # Where the plate steps in to its narrow tail: the motor cradle's forward
    # face, which is the first Y at which a full-width plate would start
    # roofing a retention cap. Aft of the last support column, so the step
    # never eats into a shelf screw.
    p["pi_shelf_step_y"] = -p["wheelbase"] / 2.0 + p["cradle_w"] / 2.0
    # Battery bay ring stops clear of the motor cradle, so it is shorter than
    # the pack and open at the aft end.
    p["bay_aft_y"] = -p["wheelbase"] / 2.0 + p["cradle_w"] / 2.0 + p["battery_bay_aft_clear"]
    p["bay_fwd_y"] = -6.0 + (p["battery_l"] + 2 * p["battery_clear"]) / 2.0 + 2.0
    p["tub_outer_w"] = p["tub_width"]
    p["tub_outer_l"] = p["tub_len"]
    p["tub_outer_h"] = p["tub_height"] + p["deck_wall"]
    # --- drivetrain -------------------------------------------------------
    # Lug pitch IS the sprocket tooth pitch, by construction, so engagement can
    # never accumulate error around the loop. The loop then closes at whatever
    # straight run 29 lugs demand (119.38 mm), which is 0.62 mm shorter than the
    # tub's nominal 120 mm wheelbase -- taken up in the idler tensioning slot
    # along with all pretension. Each mm the idler moves forward adds 2 mm of
    # path, i.e. 0.55 % strain in the TPU.
    p["track_lug_pitch"] = math.pi * p["sprocket_pitch_dia"] / p["sprocket_teeth"]
    p["track_inner_path"] = p["track_lug_count"] * p["track_lug_pitch"]
    p["track_straight_len"] = (p["track_inner_path"]
                               - math.pi * p["sprocket_pitch_dia"]) / 2.0
    p["idler_y_nom"] = -p["wheelbase"] / 2.0 + p["track_straight_len"]
    p["track_inner_r"] = p["sprocket_pitch_dia"] / 2.0
    p["track_outer_r"] = p["track_inner_r"] + p["track_thickness"]
    p["track_lug_root_w"] = p["track_lug_tip_w"] + 2 * p["track_lug_chamfer"]
    # The wheel groove is trapezoidal, matching the lug's flare. Two reasons:
    # it clears the lug root chamfer with even side clearance instead of only at
    # the mouth, and its ceiling becomes a 49 deg slope rather than a horizontal
    # annular ledge, so the wheels print support-free with the axis vertical.
    p["wheel_groove_w"] = p["track_lug_root_w"] + p["lug_side_clear"]
    p["wheel_groove_root_w"] = p["track_lug_tip_w"] + p["lug_side_clear"]
    p["wheel_groove_depth"] = p["track_lug_h"] + p["lug_clear_r"]
    p["wheel_land_w"] = (p["wheel_width"] - p["wheel_groove_w"]) / 2.0
    p["bearing_623_seat_od"] = p["bearing_623_od"] + p["bearing_seat_fit"]
    # Road wheels are smaller than the sprocket, so they ride a lower axle line
    # to reach the same track inner surface. At 15.5 mm that line is below the
    # tub floor, which is why the side walls carry a skirt.
    p["roadwheel_axle_z"] = p["roadwheel_dia"] / 2.0 + p["track_thickness"]
    # Idler slot: nominal (zero-strain) position at the aft end, adjustment
    # forward only.
    p["idler_slot_cy"] = p["idler_y_nom"] + p["idler_slot_travel"] / 2.0
    p["idler_slot_len"] = p["axle_hole_dia"] + p["idler_slot_travel"]
    # Treads are relieved out of the band, so the tip radius is unchanged and
    # the continuous section is what gets thinner.
    p["track_band_t"] = p["track_thickness"] - p["tread_depth"]
    p["tread_valley_r"] = p["track_outer_r"] - p["tread_depth"]
    # --- rear anti-tip tail -----------------------------------------------
    # A fixed boom, not a pivoting caster. It carries a roller floating
    # caster_float above the floor, so it does nothing until the robot pitches
    # back far enough to drop it -- about 2 deg -- and then becomes the rear
    # ground contact, moving the tip-over pivot from the rear track tangent out
    # to the roller and taking the rearward margin from 33 to 54 deg.
    p["tail_mount_y"] = -p["tub_len"] / 2.0                  # rear wall outer face
    p["tail_contact_y"] = -(p["wheelbase"] / 2.0 + p["track_outer_r"]) - p["caster_trail"]
    p["tail_axle_z"] = p["caster_wheel_dia"] / 2.0 + p["caster_float"]
    p["tail_axle_drop"] = p["caster_pivot_z"] - p["tail_axle_z"]
    p["tail_boom_len"] = (p["tail_mount_y"] - p["tail_flange_t"]) - p["tail_contact_y"]
    # The roller is a PLA hub inside a TPU tyre. The tyre carries the overall
    # diameter, so the float and the tip-margin geometry are unchanged by it.
    p["tail_hub_dia"] = p["caster_wheel_dia"] - 2 * p["tail_tyre_t"]
    p["tail_tyre_w"] = p["caster_wheel_w"] - 2 * p["tail_tyre_lip_w"]
    # --- vertical stack (absolute z, ground = 0) ---
    p["deck_top"] = p["ground_clearance"] + p["tub_height"] + p["deck_wall"]
    p["shoulder_z"] = p["deck_top"] + p["shoulder_z_off"]
    p["torso_top"] = p["deck_top"] + p["torso_h"]
    p["neck_top"] = p["torso_top"] + p["neck_h"]
    p["head_top"] = p["neck_top"] + p["head_h"]
    p["total_h"] = p["head_top"] + p["antenna_h"]
    return p


def pi_column_ys(p):
    """Support-column centres along Y, shared by the tub and the shelf plate.

    The forward column stops clear of the idler rod at its slackest setting --
    the rod crosses the column band at axle height, and a column notched for it
    would be mostly notch. The plate cantilevers the last 14 mm to its front
    edge, which is carrying nothing but air.

    The aft column is clamped the same way, off the motor cradles. The plate
    reaches back over both of them to carry the IMU breadboard, and a column at
    its aft edge would stand inside the motor drop-in pocket, where the
    retention cap has to come out. So the last column sits in front of the
    cradle face and the plate cantilevers the remainder -- about 21 mm, loaded
    only by the breadboard.
    """
    n = int(p["pi_columns_per_side"])
    half = p["pi_column_len"] / 2.0
    aft = p["pi_shelf_aft_y"] + 2.0 + half
    cradle_fwd = -p["wheelbase"] / 2.0 + p["cradle_w"] / 2.0
    aft = max(aft, cradle_fwd + p["pi_column_cradle_clear"] + half)
    fwd = p["idler_y_nom"] - p["idler_axle_dia"] / 2.0 - 3.0 - half
    if n < 2:
        return [(aft + fwd) / 2.0]
    step = (fwd - aft) / (n - 1)
    return [aft + i * step for i in range(n)]


def roadwheel_ys(p):
    """Road-wheel centres along Y, centred on the wheelbase.

    Shared by the tub and the drivetrain so the holes and the wheels cannot end
    up in different places. Spacing is an explicit pitch rather than a fraction
    of the wheelbase: the old wheelbase*0.6 formula put two ø24 wheels 24 mm
    apart, which is exactly tangent, and nothing in the parameter sheet showed
    it -- the build-time rim-gap check is what found it.
    """
    n = int(p["roadwheels_per_side"])
    pitch = p["roadwheel_pitch"]
    return [(i - (n - 1) / 2.0) * pitch for i in range(n)]


def get():
    """Convenience: loaded + derived parameter dict."""
    return derive(load_raw())


if __name__ == "__main__":
    p = get()
    for k in sorted(p):
        print(f"{k:24s} {p[k]:.3f}")
