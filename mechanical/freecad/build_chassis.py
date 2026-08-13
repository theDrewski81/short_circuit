"""Johnny 5 - chassis / tread base build script (Phase 00, Task 7).

Run headless:   freecadcmd build_chassis.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs (relative to repo root):
    mechanical/stl/chassis_tub_v1.stl
    mechanical/stl/chassis_deck_v1.stl
    mechanical/stl/caster_arm_v1.stl
    mechanical/stl/caster_wheel_v1.stl
    mechanical/stl/motor_cap_v1.stl      (print x2 -- one per motor cradle)
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


def _xhole(sgn, y, z, r, margin=1.0):
    """Through-hole in the side wall on side `sgn`, centred on (y, z).

    L.cyl only ever extrudes +X, so the start point must be the *lower* x of
    the two wall faces whichever side is being cut. The previous signature took
    a raw start point and every caller passed sgn * (X_WALL + n): correct on the
    left, and on the right it started outboard and extruded further outboard,
    cutting nothing. That is why the printed tub came off the bed with no motor
    shaft, road-wheel or idler holes on the right-hand wall.
    """
    x0 = min(sgn * X_WALL, sgn * X_WALL_IN) - margin
    return L.cyl(r, WALL + 2 * margin, x0, y, z, axis="x")


# --- tub shell -----------------------------------------------------------
def tub():
    s = L.tube_shell(W, Lg, H, WALL, z0=Z0, open_top=True)
    return s


# --- motor cradles (rear, one per side, axis along X) --------------------
def _cradle_dims():
    """Shared cradle geometry, so motor_cap() cannot drift out of step with it.

    Both lengths now come from j5_params.derive() rather than being recomputed
    here, because validate.py was deriving its own copy and the two disagreed.

    Length is set by insertion, not by the motor body. The shaft protrudes
    motor_shaft_len past the front face, so a motor lowered straight down at
    its seated position would have to pass that shaft through solid side wall.
    The cradle therefore swallows body + shaft + margin: the motor drops in
    with the shaft clear of the wall, then slides outboard onto it. At the old
    body+4 length there was no drop position at all -- anywhere far enough
    inboard put the motor's underside through the tub floor.

    Width is set by the cap screws: the columns must sit clear of the drop-in
    slot on both sides.
    """
    return P["cradle_l"], P["cradle_w"], AXLE + P["motor_dia"] / 2.0 + 3.0


def _cap_dims():
    """Cap footprint, clipped off the cradle footprint.

    The cradle is fused to the tub, so it can run into the side and rear walls
    and simply merge with them. The cap cannot: it is a separate printed part
    that has to drop between those walls, so it gives up motor_cap_wall_clear
    against each one. At the current wheelbase the rear wall is the binding
    constraint, sitting only 12.6 mm behind the motor axis.
    """
    cradle_l, cradle_w, _ = _cradle_dims()
    clear = P["motor_cap_wall_clear"]
    rear_span = Lg / 2.0 - WALL - abs(Y_REAR) - clear
    cap_l = cradle_l - 2 * clear                  # clears the side wall outboard
    cap_w = min(cradle_w, 2.0 * rear_span)        # clears the rear wall
    return cap_l, cap_w


def _rim_boss_xy():
    """Deck screw-boss centres. Shared with deck() so the holes cannot drift apart.

    The inset is set so each boss overlaps the tub wall it sits against by 1 mm.
    At the original W/2-6 the bosses stopped 0.1 mm short of the inner faces and
    came out of the fuse as four solids floating free of the tub.
    """
    inset = P["tub_wall"] + P["boss_od"] / 2.0 - 1.0
    return [(sx * (W / 2.0 - inset), sy * (Lg / 2.0 - inset))
            for sx in (-1, 1) for sy in (-1, 1)]


def motor_cradles():
    solids, cuts = [], []
    fit = P["motor_fit_clear"]
    bore_r = (P["motor_dia"] + fit) / 2.0
    cradle_l, cradle_w, cradle_top = _cradle_dims()
    depth = P["motor_cap_screw_depth"]
    for sgn in (-1, 1):
        # outboard end flush with inner wall face, body reaching inward
        x_out = sgn * X_WALL_IN
        x_in = x_out - sgn * cradle_l
        cx = (x_out + x_in) / 2.0
        # At the current wheelbase the widened block runs 0.9 mm past the rear
        # wall's inner face and merges into it on the fuse. That is intended --
        # it stiffens the wall behind the drive loads -- and it stays inside the
        # tub's outer face, which validate.py checks.
        block = L.box(cradle_l, cradle_w, cradle_top - Z0, cx, Y_REAR, Z0)
        # horizontal motor bore
        bore = L.cyl(bore_r, cradle_l + 2, min(x_out, x_in) - 1, Y_REAR, AXLE, axis="x")
        # Drop-in slot, open top, running the full cradle length. It used to be
        # cradle_l - 4, which at the old cradle length came out exactly equal to
        # motor_body_len -- zero axial clearance, with a 2 mm roof tab at each
        # end for the motor to catch on. Full length also gives the motor room
        # to slide outboard onto its shaft after being lowered in.
        slot = L.box(cradle_l, P["motor_dia"] + fit, cradle_top - AXLE + 2, cx, Y_REAR, AXLE)
        solids.append(block)
        cuts.append(bore)
        cuts.append(slot)
        # shaft clearance hole through the side wall
        cuts.append(_xhole(sgn, Y_REAR, AXLE, (P["motor_shaft_dia"] + 1.5) / 2.0))
        # four tapped columns per side, flanking the slot, for the retention cap
        for dx in (-P["motor_cap_screw_x"] / 2.0, P["motor_cap_screw_x"] / 2.0):
            for dy in (-P["motor_cap_screw_cc"] / 2.0, P["motor_cap_screw_cc"] / 2.0):
                cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, depth + 1,
                                  cx + dx, Y_REAR + dy, cradle_top - depth))
    return solids, cuts


# --- motor retention cap (separate print, x2) ----------------------------
def motor_cap():
    """Closes the cradle slot and holds a motor in. One part, printed twice.

    Built about the origin with the motor axis along X rather than in place, so
    it exports as a printable part (same convention as the caster pieces). The
    tongue drops into the cradle slot and is carved out by the motor body,
    leaving a saddle that bears on the top of the can. The plate is held
    motor_cap_clamp_gap above the cradle top so the four M2 screws preload the
    motor down into the bore instead of bottoming the plate out first.
    """
    fit = P["motor_cap_fit"]
    cradle_l, cradle_w, cradle_top = _cradle_dims()
    cap_l, cap_w = _cap_dims()
    # cradle top and plate underside, expressed relative to the motor axis
    top_rel = cradle_top - AXLE
    plate_z = top_rel + P["motor_cap_clamp_gap"]

    plate = L.box(cap_l, cap_w, P["motor_cap_t"], 0, 0, plate_z)
    # Tongue is sized off the cap plate, not the cradle, so it can never end up
    # longer than the plate carrying it.
    tongue = L.box(cap_l - 2 * fit,
                   P["motor_dia"] + P["motor_fit_clear"] - 2 * fit,
                   plate_z, 0, 0, 0.0)
    solid = plate.fuse(tongue)
    # carve the saddle: nominal motor radius, no clearance, so the cap grips
    solid = solid.cut(L.cyl(P["motor_dia"] / 2.0, cradle_l + 4,
                            -(cradle_l + 2) / 2.0, 0, 0, axis="x"))
    # M2 clearance holes over the cradle's tapped columns
    for dx in (-P["motor_cap_screw_x"] / 2.0, P["motor_cap_screw_x"] / 2.0):
        for dy in (-P["motor_cap_screw_cc"] / 2.0, P["motor_cap_screw_cc"] / 2.0):
            solid = solid.cut(L.cyl(P["m2_tap_dia"] / 2.0 + 0.3, P["motor_cap_t"] + 2,
                                    dx, dy, plate_z - 1))
    return solid


# --- side-wall axle features (idler bearing + road wheels) ---------------
def axle_features():
    """Side-wall shaft features for the idler and road wheels.

    Bearings live in the wheel hubs, not in the wall. The BOM's 8x 623ZZ works
    out to two per idler wheel plus one per road wheel, and the road wheels
    were already treated this way. The old version counterbored a 10 x 4 mm
    bearing pocket into a 2.4 mm wall, which cannot work at any sign -- and its
    sign handling was inverted relative to _xhole, so it cut clean through on
    the right and landed in mid-air inboard of the left wall. The two together
    are why the printed idler holes measured ~9.8 mm one side and ~3.25 mm the
    other.

    The idler runs one full-width 3 mm rod so it cannot cock; each wall gets a
    pad on the inner face to take shaft bearing length from tub_wall to
    tub_wall + idler_pad_t.
    """
    solids, cuts = [], []
    r = P["axle_hole_dia"] / 2.0
    pad_t = P["idler_pad_t"]
    for sgn in (-1, 1):
        solids.append(L.cyl(P["idler_pad_od"] / 2.0, pad_t,
                            min(sgn * X_WALL_IN, sgn * (X_WALL_IN - pad_t)),
                            Y_FRONT, AXLE, axis="x"))
        cuts.append(L.cyl(r, WALL + pad_t + 2,
                          min(sgn * X_WALL, sgn * (X_WALL_IN - pad_t)) - 1,
                          Y_FRONT, AXLE, axis="x"))
    # road-wheel stub-axle holes
    n = int(P["roadwheels_per_side"])
    span = P["wheelbase"] * 0.6
    for i in range(n):
        frac = (i + 1) / (n + 1)
        y = -span / 2.0 + frac * span
        for sgn in (-1, 1):
            cuts.append(_xhole(sgn, y, AXLE, r))
    return solids, cuts


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
    """Pi-M shelf, its support ribs, and the cuts they need. Returns (solid, cuts).

    The ribs used to sit at the plate edge, 15.8 mm off centre, which put them
    1.7 mm inside the battery envelope on each side over 53.5 mm of the pack's
    length -- the battery could not seat at all. They now start outboard of the
    battery bay ring and the plate widens to reach them.

    The full-width idler shaft passes straight through the rib band at
    (Y_FRONT, AXLE), so each rib takes a clearance notch. Clearance, not a fit:
    the shaft is located by the wall pads, and making the ribs a third and
    fourth bearing would just add two more holes to align on assembly.
    """
    z = Z0 + WALL + P["pi_shelf_z"]
    cy = Y_FRONT - 28
    shelf_w = P["pi_l"] + 8     # Y
    rib_t = WALL + 6
    rib_cx = P["pi_rib_x_in"] + rib_t / 2.0

    solid = L.box(2 * P["pi_shelf_half_w"], shelf_w, 2.0, 0, cy, z)
    for sgn in (-1, 1):
        solid = solid.fuse(L.box(rib_t, shelf_w, z - (Z0 + WALL),
                                 sgn * rib_cx, cy, Z0 + WALL))
    # four standoffs at Pi hole pattern
    for dx in (-P["pi_hole_dy"] / 2, P["pi_hole_dy"] / 2):      # short axis along X
        for dy in (-P["pi_hole_dx"] / 2, P["pi_hole_dx"] / 2):  # long axis along Y
            solid = solid.fuse(L.standoff(dx, cy + dy, z + 2, P["pi_standoff_h"],
                                          P["boss_od"], P["m25_tap_dia"]))
    notch = L.cyl(P["axle_hole_dia"] / 2.0 + 1.0, W + 4,
                  -(W / 2.0 + 2), Y_FRONT, AXLE, axis="x")
    return solid, [notch]


# --- IMU pad (centroid, floor) -------------------------------------------
def imu_pad():
    """IMU pad on the tub floor, outboard of the battery bay.

    It used to sit at (0, -6) -- concentric with the battery bay, so the pack
    landed on top of it -- and its two forward screws fell under the Pi shelf,
    with no vertical driver access. Both features wanted the centroid and
    neither knew about the other.

    The lateral offset costs nothing for the gyro: angular rate is identical
    anywhere on a rigid body. It adds a small centripetal term to the
    accelerometer during tank turns, which is a fixed lever-arm correction.
    """
    z = Z0 + WALL
    px, py = P["imu_pos_x"], P["imu_pos_y"]
    solid = L.box(P["imu_hole_cc"] + 8, P["imu_hole_cc"] + 8, 2.5, px, py, z)
    cuts = []
    h = P["imu_hole_cc"] / 2.0
    for dx in (-h, h):
        for dy in (-h, h):
            cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, 6, px + dx, py + dy, z - 0.1))
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
    # four perimeter screws down into tub-rim bosses (same centres as the bosses)
    for bx, by in _rim_boss_xy():
        cuts.append(L.cyl(P["m2_tap_dia"] / 2.0 + 0.3, P["deck_wall"] + 1, bx, by, -0.5))
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

    shelf, shelf_cuts = pi_shelf()
    body = body.fuse(shelf)

    ax_solids, ax_cuts = axle_features()
    for s in ax_solids:
        body = body.fuse(s)

    ipad, icuts = imu_pad()
    body = body.fuse(ipad)

    # tub-rim screw bosses for the deck. The pilot bores come back from
    # screw_boss() and must be cut -- they were previously discarded, leaving
    # solid bosses with nothing for the deck screws to thread into.
    rim_cuts = []
    for bx, by in _rim_boss_xy():
        b, h = L.screw_boss(bx, by, ZTOP - 8, 8, P["boss_od"], P["m2_tap_dia"])
        body = body.fuse(b)
        rim_cuts.append(h)

    # rear trailing-caster pivot bosses
    rp_solids, rp_cuts = rear_pivot()
    for s in rp_solids:
        body = body.fuse(s)

    # subtract all cuts
    for c in (mc_cuts + bcuts + icuts + ax_cuts + shelf_cuts
              + front_wall_features() + lightening() + rp_cuts + rim_cuts):
        body = body.cut(c)

    return body, deck()


def main():
    doc = App.newDocument("chassis_assembly_v1")
    tub_shape, deck_shape = build()

    # A printable part must come out of the fuse as exactly one solid. More than
    # one means something was placed clear of the body and is floating -- it
    # slices as an island in mid-air rather than failing loudly, so guard here
    # instead of finding out on the bed.
    for shp, nm in ((tub_shape, "tub"), (deck_shape, "deck")):
        n = len(shp.Solids)
        if n != 1:
            raise RuntimeError(f"{nm} built as {n} solids -- geometry is not "
                               f"fused to the body; refusing to export")

    arm_shape = caster_arm()
    wheel_shape = caster_wheel()
    cap_shape = motor_cap()

    # --- assembly guards -------------------------------------------------
    # Param checks in preview/validate.py cannot see any of this. They compare
    # numbers to numbers; every defect guarded below was a solid that either
    # missed what it was meant to cut or landed inside something else, and all
    # of them survived a full-PASS validate run and reached the print bed.

    cradle_l, _, _ = _cradle_dims()
    cx = X_WALL_IN - cradle_l / 2.0
    fitted = cap_shape.copy()
    fitted.translate(Vector(cx, Y_REAR, AXLE))
    motor = Part.makeCylinder(
        P["motor_dia"] / 2.0, P["motor_body_len"],
        Vector(cx - P["motor_body_len"] / 2.0, Y_REAR, AXLE), Vector(1, 0, 0))
    for a, b, what in ((fitted, tub_shape, "cap vs tub"),
                       (fitted, motor, "cap vs motor"),
                       (motor, tub_shape, "motor vs cradle")):
        clash = a.common(b).Volume
        if clash > 1e-6:
            raise RuntimeError(f"{what} interference: {clash:.1f} mm3 -- "
                               "parts do not assemble; refusing to export")

    # The motor is lowered in with its shaft clear of the side wall, then slid
    # outboard onto it. Check that drop position on both sides -- at the old
    # cradle length no such position existed and nothing in the build said so.
    drop_front = X_WALL_IN - P["motor_shaft_len"]
    for sgn in (-1, 1):
        x0 = min(sgn * drop_front, sgn * (drop_front - P["motor_body_len"]))
        dropped = Part.makeCylinder(
            P["motor_dia"] / 2.0, P["motor_body_len"],
            Vector(x0, Y_REAR, AXLE), Vector(1, 0, 0))
        clash = dropped.common(tub_shape).Volume
        if clash > 1e-6:
            side = "left" if sgn < 0 else "right"
            raise RuntimeError(f"motor cannot be lowered into the {side} cradle: "
                               f"{clash:.1f} mm3 interference at the drop position")

    # Every side-wall shaft hole must actually be open, on both sides.
    n = int(P["roadwheels_per_side"])
    span = P["wheelbase"] * 0.6
    wall_holes = [("motor shaft", Y_REAR, (P["motor_shaft_dia"] + 1.5) / 2.0),
                  ("idler axle", Y_FRONT, P["axle_hole_dia"] / 2.0)]
    for i in range(n):
        y = -span / 2.0 + (i + 1) / (n + 1) * span
        wall_holes.append((f"road wheel y={y:+.0f}", y, P["axle_hole_dia"] / 2.0))
    for name, y, r in wall_holes:
        for sgn in (-1, 1):
            probe = L.cyl(r * 0.8, WALL + 1,
                          min(sgn * X_WALL, sgn * X_WALL_IN) - 0.5, y, AXLE, axis="x")
            blocked = probe.common(tub_shape).Volume
            if blocked > 1e-6:
                side = "left" if sgn < 0 else "right"
                raise RuntimeError(f"{name} hole is not open in the {side} wall: "
                                   f"{blocked:.1f} mm3 still in the bore")

    # Keep-outs: volumes that have to stay empty for the robot to go together.
    pack = L.box(P["battery_w"], P["battery_l"], P["battery_h"], 0, -6, Z0 + WALL)
    clash = pack.common(tub_shape).Volume
    if clash > 1e-6:
        raise RuntimeError(f"battery envelope obstructed by {clash:.1f} mm3 -- "
                           "the pack cannot seat")

    h = P["imu_hole_cc"] / 2.0
    for dx in (-h, h):
        for dy in (-h, h):
            col = L.cyl(2.0, ZTOP - (Z0 + WALL + 2.5),
                        P["imu_pos_x"] + dx, P["imu_pos_y"] + dy, Z0 + WALL + 2.5)
            clash = col.common(tub_shape).Volume
            if clash > 1e-6:
                raise RuntimeError(
                    f"no driver access to the imu screw at "
                    f"({P['imu_pos_x'] + dx:+.1f}, {P['imu_pos_y'] + dy:+.1f}): "
                    f"{clash:.1f} mm3 overhead")
    L.export(tub_shape, os.path.join(STL, "chassis_tub_v1.stl"))
    L.export(deck_shape, os.path.join(STL, "chassis_deck_v1.stl"))
    L.export(arm_shape, os.path.join(STL, "caster_arm_v1.stl"))
    L.export(wheel_shape, os.path.join(STL, "caster_wheel_v1.stl"))
    L.export(cap_shape, os.path.join(STL, "motor_cap_v1.stl"))

    for shp, nm in ((tub_shape, "chassis_tub"), (deck_shape, "chassis_deck"),
                    (arm_shape, "caster_arm"), (wheel_shape, "caster_wheel"),
                    (cap_shape, "motor_cap")):
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "chassis_assembly_v1.FCStd"))
    print("chassis: tub bbox", tub_shape.BoundBox)
    print("chassis: deck bbox", deck_shape.BoundBox)


if __name__ == "__main__":
    main()
