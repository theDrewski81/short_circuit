"""Johnny 5 - chassis / tread base build script (Phase 00, Task 7).

Run headless:   freecadcmd build_chassis.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs (relative to repo root):
    mechanical/stl/chassis_tub_v1.stl
    mechanical/stl/chassis_deck_v1.stl
    mechanical/freecad/chassis_assembly_v1.FCStd

Coordinate frame: origin at the centre of the track footprint on the ground
plane. +X right, +Y forward, +Z up. Parallel-track stance (confirmed Session 02).

The drivetrain wheels/sprockets/idlers and the TPU track print as separate
parts; this script builds only the structural tub and its top deck, plus every
mounting feature the BOM calls out.
"""

import os
import FreeCAD as App
import Part
from FreeCAD import Vector

import j5_lib as L
import j5_params

P = j5_params.get()

# --- paths ---------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STL = os.path.join(REPO, "mechanical", "stl")
os.makedirs(STL, exist_ok=True)

# --- key positions -------------------------------------------------------
W = P["tub_width"]                 # X extent
Lg = P["tub_len"]                  # Y extent (length)
H = P["tub_height"]
WALL = P["tub_wall"]
Z0 = P["ground_clearance"]         # tub floor underside
ZTOP = Z0 + H                      # tub rim
AXLE = P["axle_z"]                 # axle line, absolute z above ground
Y_REAR = -P["wheelbase"] / 2.0     # drive sprocket / motors
Y_FRONT = P["wheelbase"] / 2.0     # idler
X_WALL = W / 2.0                   # side-wall outer face
X_WALL_IN = X_WALL - WALL          # side-wall inner face


def _xhole(x, y, z, r, length):
    """Through-hole cylinder along +X starting at x."""
    return L.cyl(r, length, x, y, z, axis="x")


# --- tub shell -----------------------------------------------------------
def tub():
    s = L.tube_shell(W, Lg, H, WALL, z0=Z0, open_top=True)
    return s


# --- motor cradles (rear, one per side, axis along X) --------------------
def motor_cradles():
    solids, cuts = [], []
    bore_r = (P["motor_dia"] + 0.4) / 2.0
    cradle_l = P["motor_body_len"] + 4.0
    cradle_w = 16.0
    cradle_top = AXLE + P["motor_dia"] / 2.0 + 3.0
    for sgn in (-1, 1):
        # outboard end flush with inner wall face, body reaching inward
        x_out = sgn * X_WALL_IN
        x_in = x_out - sgn * cradle_l
        cx = (x_out + x_in) / 2.0
        block = L.box(cradle_l, cradle_w, cradle_top - Z0, cx, Y_REAR, Z0)
        # horizontal motor bore
        bore = L.cyl(bore_r, cradle_l + 2, min(x_out, x_in) - 1, Y_REAR, AXLE, axis="x")
        # drop-in slot (open top) so the motor seats from above, retained by a cap
        slot = L.box(cradle_l - 4, P["motor_dia"], cradle_top - AXLE + 2, cx, Y_REAR, AXLE)
        solids.append(block)
        cuts.append(bore)
        cuts.append(slot)
        # shaft clearance hole through the side wall
        cuts.append(_xhole(sgn * (X_WALL + 2), Y_REAR, AXLE, (P["motor_shaft_dia"] + 1.5) / 2.0, 6))
    return solids, cuts


# --- side-wall axle features (idler bearing + road wheels) ---------------
def axle_features():
    cuts = []
    bearing_r = 10.0 / 2.0          # 623ZZ OD 10
    bearing_depth = 4.0
    # idler bearing pockets (front)
    for sgn in (-1, 1):
        x_start = sgn * X_WALL
        cuts.append(L.cyl(bearing_r, bearing_depth + 0.5, x_start - sgn * (bearing_depth), Y_FRONT, AXLE, axis="x"))
        cuts.append(_xhole(sgn * (X_WALL + 1), Y_FRONT, AXLE, 3.2 / 2.0, WALL + 2))  # idler axle 3mm
    # road-wheel stub-axle holes
    n = int(P["roadwheels_per_side"])
    span = P["wheelbase"] * 0.6
    for i in range(n):
        frac = (i + 1) / (n + 1)
        y = -span / 2.0 + frac * span
        for sgn in (-1, 1):
            cuts.append(_xhole(sgn * (X_WALL + 1), y, AXLE, 3.2 / 2.0, WALL + 2))
    return cuts


# --- battery bay ---------------------------------------------------------
def battery_bay():
    bl = P["battery_l"] + 2 * P["battery_clear"]   # along Y
    bw = P["battery_w"] + 2 * P["battery_clear"]   # along X
    wall = 2.0
    floor = Z0 + WALL
    ring_h = P["battery_h"] * 0.6
    outer = L.box(bw + 2 * wall, bl + 2 * wall, ring_h, 0, -6, floor)
    inner = L.box(bw, bl, ring_h + 1, 0, -6, floor)
    ring = outer.cut(inner)
    # strap slots through the long walls
    cuts = [L.box(bw + 2 * wall + 2, 6, ring_h - 3, 0, -6 - bl / 2 + 5, floor + 2),
            L.box(bw + 2 * wall + 2, 6, ring_h - 3, 0, -6 + bl / 2 - 5, floor + 2)]
    return ring, cuts


# --- Pi-M shelf + standoffs ----------------------------------------------
def pi_shelf():
    z = Z0 + WALL + P["pi_shelf_z"]
    shelf_l = P["pi_w"] + 8     # X
    shelf_w = P["pi_l"] + 8     # Y
    plate = L.box(shelf_l, shelf_w, 2.0, 0, Y_FRONT - 28, z)
    # support ribs to side walls
    ribs = [L.box(WALL + 6, shelf_w, z - (Z0 + WALL), -shelf_l / 2 - 1, Y_FRONT - 28, Z0 + WALL),
            L.box(WALL + 6, shelf_w, z - (Z0 + WALL), shelf_l / 2 + 1, Y_FRONT - 28, Z0 + WALL)]
    solid = plate
    for r in ribs:
        solid = solid.fuse(r)
    # four standoffs at Pi hole pattern
    stand = []
    for dx in (-P["pi_hole_dy"] / 2, P["pi_hole_dy"] / 2):      # short axis along X
        for dy in (-P["pi_hole_dx"] / 2, P["pi_hole_dx"] / 2):  # long axis along Y
            stand.append(L.standoff(dx, Y_FRONT - 28 + dy, z + 2, P["pi_standoff_h"],
                                    P["boss_od"], P["m25_tap_dia"]))
    for s in stand:
        solid = solid.fuse(s)
    return solid


# --- IMU pad (centroid, floor) -------------------------------------------
def imu_pad():
    z = Z0 + WALL
    pad = L.box(P["imu_hole_cc"] + 8, P["imu_hole_cc"] + 8, 2.5, 0, -6, z)
    solid = pad
    cuts = []
    h = P["imu_hole_cc"] / 2.0
    for dx in (-h, h):
        for dy in (-h, h):
            cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, 6, dx, -6 + dy, z - 0.1))
    return solid, cuts


# --- front ToF + IMU wall features ---------------------------------------
def front_wall_features():
    cuts = []
    yf = Lg / 2.0 + 1            # front wall outer
    # ToF window
    cuts.append(L.box(P["tof_window_w"], WALL + 4, P["tof_window_h"], 0, Lg / 2.0, AXLE + 6))
    # ToF mount holes
    for dx in (-P["tof_hole_cc"] / 2, P["tof_hole_cc"] / 2):
        cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, WALL + 4, x=dx, y=Lg / 2.0 - WALL - 1, z=AXLE + 6, axis="y"))
    return cuts


# --- lightening pockets (side walls + floor) -----------------------------
def lightening():
    cuts = []
    # side-wall pockets (leave margins around axle line and rims)
    pl, ph, depth = 40, 18, WALL - 1.0
    for sgn in (-1, 1):
        for yy in (-Lg / 4, Lg / 4):
            cuts.append(L.box(depth + 0.2, pl, ph, sgn * (X_WALL - depth / 2 - 0.05), yy, AXLE + 8))
    # floor pockets fore and aft of the battery ring
    cuts.append(L.box(W - 24, 18, WALL - 1.0, 0, Lg / 2 - 16, Z0 + 0.05))
    return cuts


# --- rear trailing-caster pivot bosses (fused to the tub) ----------------
def rear_pivot():
    solids, cuts = [], []
    y_rear = -Lg / 2.0
    for sgn in (-1, 1):
        solids.append(L.cyl(5, 8, sgn * 16, y_rear - 6, P["caster_pivot_z"], axis="y"))
        cuts.append(L.cyl(1.6, 12, sgn * 16, y_rear - 8, P["caster_pivot_z"], axis="y"))
    return solids, cuts


# --- trailing caster parts (separate prints) -----------------------------
def caster_arm():
    """Swing arm: pivot eye -> trailing arm -> wheel fork."""
    arm = L.box(10, P["caster_arm_len"], 8, 0, -P["caster_arm_len"] / 2.0, 0)
    arm = arm.fuse(L.cyl(5, 12, 0, 0, 0, axis="y"))                       # pivot eye
    arm = arm.fuse(L.box(10, 10, P["caster_wheel_dia"] / 2.0 + 6, 0,
                         -P["caster_arm_len"], -P["caster_wheel_dia"] / 2.0))
    arm = arm.cut(L.cyl(1.6, 14, 0, 0, 0, axis="y"))                      # pivot bore
    arm = arm.cut(L.cyl(1.6, 14, 0, -P["caster_arm_len"], -P["caster_wheel_dia"] / 2.0, axis="y"))
    return arm


def caster_wheel():
    w = L.cyl(P["caster_wheel_dia"] / 2.0, 12, 0, 0, 0, axis="y")
    return w.cut(L.cyl(2.5, 14, 0, -1, 0, axis="y"))                      # axle bore


# --- top deck (separate part) --------------------------------------------
def deck():
    d = L.box(W, Lg, P["deck_wall"], 0, 0, 0)
    cuts = []
    # central cable pass-through
    cuts.append(L.box(P["cable_slot_w"], P["cable_slot_l"], P["deck_wall"] + 1, 0, 0, -0.5))
    # torso interface bolt rectangle (M3 heat-set bores)
    for dx in (-P["torso_iface_dx"] / 2, P["torso_iface_dx"] / 2):
        for dy in (-P["torso_iface_dy"] / 2, P["torso_iface_dy"] / 2):
            cuts.append(L.cyl(P["m3_heatset_dia"] / 2.0, P["deck_wall"] + 1, dx, dy, -0.5))
    # four perimeter screws down into tub-rim bosses
    for dx in (-(W / 2 - 6), W / 2 - 6):
        for dy in (-(Lg / 2 - 6), Lg / 2 - 6):
            cuts.append(L.cyl(P["m2_tap_dia"] / 2.0 + 0.3, P["deck_wall"] + 1, dx, dy, -0.5))
    solid = d
    for c in cuts:
        solid = solid.cut(c)
    # lean-ready waist reserve (V2 powered waist): two pivot-axle bosses
    for sgn in (-1, 1):
        boss = L.cyl(4.5, 6, sgn * 30, 0, P["deck_wall"])
        solid = solid.fuse(boss.cut(L.cyl(P["waist_pivot_dia"] / 2.0, 8, sgn * 30, 0, P["deck_wall"] - 1)))
    return solid


# --- assemble ------------------------------------------------------------
def build():
    body = tub()

    mc_solids, mc_cuts = motor_cradles()
    for s in mc_solids:
        body = body.fuse(s)

    bring, bcuts = battery_bay()
    body = body.fuse(bring)
    body = body.fuse(pi_shelf())

    ipad, icuts = imu_pad()
    body = body.fuse(ipad)

    # tub-rim screw bosses for the deck
    for dx in (-(W / 2 - 6), W / 2 - 6):
        for dy in (-(Lg / 2 - 6), Lg / 2 - 6):
            b, h = L.screw_boss(dx, dy, ZTOP - 8, 8, P["boss_od"], P["m2_tap_dia"])
            body = body.fuse(b)

    # rear trailing-caster pivot bosses
    rp_solids, rp_cuts = rear_pivot()
    for s in rp_solids:
        body = body.fuse(s)

    # subtract all cuts
    for c in (mc_cuts + bcuts + icuts + axle_features()
              + front_wall_features() + lightening() + rp_cuts):
        body = body.cut(c)

    return body, deck()


def main():
    doc = App.newDocument("chassis_assembly_v1")
    tub_shape, deck_shape = build()

    arm_shape = caster_arm()
    wheel_shape = caster_wheel()
    L.export(tub_shape, os.path.join(STL, "chassis_tub_v1.stl"))
    L.export(deck_shape, os.path.join(STL, "chassis_deck_v1.stl"))
    L.export(arm_shape, os.path.join(STL, "caster_arm_v1.stl"))
    L.export(wheel_shape, os.path.join(STL, "caster_wheel_v1.stl"))

    for shp, nm in ((tub_shape, "chassis_tub"), (deck_shape, "chassis_deck"),
                    (arm_shape, "caster_arm"), (wheel_shape, "caster_wheel")):
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "chassis_assembly_v1.FCStd"))
    print("chassis: tub bbox", tub_shape.BoundBox)
    print("chassis: deck bbox", deck_shape.BoundBox)


if __name__ == "__main__":
    main()
