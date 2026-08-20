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

    Both lengths come from j5_params.derive() rather than being recomputed
    here, because validate.py was deriving its own copy and the two disagreed.

    Width is set by the cap screws: the columns must sit clear of the drop-in
    slot on both sides.
    """
    return P["cradle_l"], P["cradle_w"], AXLE + P["motor_dia"] / 2.0 + 3.0


def _pocket_span(sgn):
    """(inboard, outboard) x of the motor pocket on side `sgn`.

    The outboard end is the motor's front face, which stops drive_boss_t short
    of the wall inner face. That reserved slug is what the drive bearing seat
    shoulders against -- if the bore or the drop-in slot ran all the way to the
    wall there would be nothing behind the bearing to stop it pressing through.
    """
    cradle_l, _, _ = _cradle_dims()
    lo = sgn * (X_WALL_IN - cradle_l)
    hi = sgn * (X_WALL_IN - P["drive_boss_t"])
    return (lo, hi) if sgn > 0 else (hi, lo)


def _cap_dims():
    """Cap footprint, clipped off the cradle footprint.

    The cradle is fused to the tub, so it can run into the side and rear walls
    and simply merge with them. The cap cannot: it is a separate printed part
    that has to drop between those walls, so it gives up motor_cap_wall_clear
    against each one. At the current wheelbase the rear wall is the binding
    constraint, sitting only 12.6 mm behind the motor axis.
    """
    _, cradle_w, _ = _cradle_dims()
    clear = P["motor_cap_wall_clear"]
    rear_span = Lg / 2.0 - WALL - abs(Y_REAR) - clear
    # Sized off the pocket, not the cradle: the cap closes the drop-in slot, and
    # the slot now stops short of the wall to leave the bearing seat its shoulder.
    cap_l = P["motor_pocket_l"] - 2 * clear       # clears the side wall outboard
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
        # Bore and drop-in slot both stop at the motor front face rather than
        # running the length of the block, leaving drive_boss_t of solid material
        # behind the bearing seat. Previously the slot was cradle_l - 4, which
        # came out exactly equal to motor_body_len: zero axial clearance, with a
        # 2 mm roof tab at each end for the motor to catch on.
        lo, hi = _pocket_span(sgn)
        pk_l = hi - lo
        pk_cx = (lo + hi) / 2.0
        bore = L.cyl(bore_r, pk_l + 1, lo - 1, Y_REAR, AXLE, axis="x")
        slot = L.box(pk_l, P["motor_dia"] + fit, cradle_top - AXLE + 2,
                     pk_cx, Y_REAR, AXLE)
        # Connector relief. The Pololu #5218 is the back-connector variant, and
        # its connector stands proud of the can toward the tub rear, so the
        # -Y pocket wall is opened over the inboard motor_conn_relief_l -- the
        # travel needed to seat the shaft fully through the sprocket.
        # Full pocket height, which grazes the inboard cap screw on that side;
        # the alternatives all fail elsewhere. Widening the screw spacing to
        # clear it puts the cradle past the tub rear wall, and the cap cannot
        # grow to match because rear_span already pins cap_w at 24.4.
        rl, rd = P["motor_conn_relief_l"], P["motor_conn_relief_d"]
        y_edge = Y_REAR - (P["motor_dia"] + fit) / 2.0
        rz0 = AXLE - bore_r
        rx0 = lo if sgn > 0 else hi - rl
        relief = L.box(rl, rd, (cradle_top + 2) - rz0,
                       rx0 + rl / 2.0, y_edge - rd / 2.0, rz0)
        solids.append(block)
        cuts.append(bore)
        cuts.append(slot)
        cuts.append(relief)
        # four tapped columns per side, flanking the slot, for the retention cap
        for dx in (-P["motor_cap_screw_x"] / 2.0, P["motor_cap_screw_x"] / 2.0):
            for dy in (-P["motor_cap_screw_cc"] / 2.0, P["motor_cap_screw_cc"] / 2.0):
                cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, depth + 1,
                                  pk_cx + dx, Y_REAR + dy, cradle_top - depth))
    return solids, cuts


# --- drive sprocket bearing (rear wall, one per side) --------------------
def drive_axle_features():
    """Rear-wall bearing seat carrying the drive sprocket.

    The sprocket sits on the track centreline, track_cc/2 outboard, which a
    9 mm output shaft cannot reach from a motor whose body cannot pass the
    wall. Extending the shaft would not help either: a sprocket hung 16 mm off
    an N20 output shaft feeds the robot's weight and every tread tension spike
    straight into the gearbox bushings, which are not built to take it.

    The sprocket instead rides a stepped hub, bored 3 mm and set-screwed to the
    motor shaft over its full 9 mm, running in a bearing pressed into the rear
    wall from outside. The wall carries the load; the motor only supplies
    torque. Seat depth is the bearing width, taken from the outer face, so the
    shoulder it presses against is the drive_boss_t slug left by _pocket_span.
    """
    cuts = []
    bw = P["drive_bearing_w"]
    boss_t = P["drive_boss_t"]
    hub_clear = P["drive_hub_od"] + 0.6
    for sgn in (-1, 1):
        cuts.append(L.cyl(P["drive_bearing_od"] / 2.0, bw,
                          min(sgn * X_WALL, sgn * (X_WALL - bw)),
                          Y_REAR, AXLE, axis="x"))
        cuts.append(L.cyl(hub_clear / 2.0, boss_t + WALL + 2,
                          min(sgn * (X_WALL_IN - boss_t), sgn * X_WALL) - 1,
                          Y_REAR, AXLE, axis="x"))
    return cuts


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
    """Three-sided bay ring: side walls plus a forward end stop, open aft.

    The ring used to run the full length of the pack, which put 12 mm of wall
    right across the motor cradle's inboard opening -- blocking hand access and
    the motor's rear wire exit. It now stops battery_bay_aft_clear short of the
    cradle face.

    That makes the ring shorter than the pack, so it cannot have an aft end
    wall: one at bay_aft_y would sit 14.5 mm inside the pack's footprint and
    stop it seating. The pack's aft end is therefore unfenced and held by the
    straps; if it walks in testing, a drop-in aft stop fitted after the motors
    are in is the fix, rather than putting the wall back.
    """
    bw = P["battery_w"] + 2 * P["battery_clear"]   # along X
    wall = 2.0
    floor = Z0 + WALL
    ring_h = P["battery_h"] * 0.6
    y_aft, y_fwd = P["bay_aft_y"], P["bay_fwd_y"]
    ring_l = y_fwd - y_aft

    outer = L.box(bw + 2 * wall, ring_l, ring_h, 0, (y_aft + y_fwd) / 2.0, floor)
    # Inner cut runs past the aft face, so no end wall is left there.
    inner = L.box(bw, ring_l - wall + 1, ring_h + 1, 0,
                  (y_aft - 1 + y_fwd - wall) / 2.0, floor)
    ring = outer.cut(inner)
    # strap slots through the long walls, moved inboard with the ring
    cuts = [L.box(bw + 2 * wall + 2, 6, ring_h - 3, 0, y_aft + 5, floor + 2),
            L.box(bw + 2 * wall + 2, 6, ring_h - 3, 0, y_fwd - wall - 5, floor + 2)]
    return ring, cuts


# --- Pi-M shelf + standoffs ----------------------------------------------
def _shelf_screw_xy():
    """Shelf screw centres, shared by the tub's tapped holes and the plate's
    clearance holes so the two cannot land in different places."""
    cy = Y_FRONT - 28
    dy = (P["pi_l"] + 8) / 2.0 - P["pi_shelf_screw_inset"]
    return [(sx * P["pi_rib_cx"], cy + sy * dy)
            for sx in (-1, 1) for sy in (-1, 1)]


def pi_shelf_ribs():
    """The two ribs that carry the Pi-M shelf, on the tub. Returns (solid, cuts).

    The shelf itself is no longer fused on top of these. As one piece the
    underside of the plate needed support material, and the only way in to pick
    it out was a 44 x 26 mm tunnel further obstructed by the battery bay ring.
    Open-topped ribs print clean with no support at all, and the plate becomes
    a flat part that needs none either.

    The ribs sit outboard of the battery bay ring. They used to sit at the
    plate edge, 15.8 mm off centre, which put them 1.7 mm inside the battery
    envelope on each side over 53.5 mm of the pack's length.

    The full-width idler shaft passes through the rib band at (Y_FRONT, AXLE),
    so each rib takes a clearance notch. Clearance, not a fit: the shaft is
    located by the wall pads, and making the ribs a third and fourth bearing
    would just add two more holes to align on assembly.
    """
    z = Z0 + WALL + P["pi_shelf_z"]
    cy = Y_FRONT - 28
    shelf_w = P["pi_l"] + 8     # Y
    rib_t = P["pi_rib_t"]
    depth = P["motor_cap_screw_depth"]

    solid = None
    for sgn in (-1, 1):
        rib = L.box(rib_t, shelf_w, z - (Z0 + WALL), sgn * P["pi_rib_cx"], cy, Z0 + WALL)
        solid = rib if solid is None else solid.fuse(rib)

    cuts = []
    # Confined to the rib band. A full-width cut here also passes through both
    # side walls and their idler pads, opening the ø3.2 locating holes out to
    # the notch diameter and leaving the shaft nothing to be located by.
    for sgn in (-1, 1):
        lo = min(sgn * P["pi_rib_x_in"], sgn * (P["pi_rib_x_in"] + rib_t))
        cuts.append(L.cyl(P["axle_hole_dia"] / 2.0 + 1.0, rib_t + 2,
                          lo - 1, Y_FRONT, AXLE, axis="x"))
    # tapped holes in the rib top faces for the shelf screws
    for sx, sy in _shelf_screw_xy():
        cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, depth + 1, sx, sy, z - depth))
    return solid, cuts


# --- Pi-M shelf plate (separate print) -----------------------------------
def pi_shelf_plate():
    """Standalone shelf plate. Built flat about the origin, like the motor cap.

    Prints face down with no support: the standoffs are the only thing above
    the plate and the screw holes are straight through.
    """
    cy = Y_FRONT - 28
    shelf_w = P["pi_l"] + 8
    solid = L.box(2 * P["pi_shelf_half_w"], shelf_w, 2.0, 0, 0, 0)
    for dx in (-P["pi_hole_dy"] / 2, P["pi_hole_dy"] / 2):      # short axis along X
        for dy in (-P["pi_hole_dx"] / 2, P["pi_hole_dx"] / 2):  # long axis along Y
            solid = solid.fuse(L.standoff(dx, dy, 2.0, P["pi_standoff_h"],
                                          P["boss_od"], P["m25_tap_dia"]))
    for sx, sy in _shelf_screw_xy():
        solid = solid.cut(L.cyl(P["m2_tap_dia"] / 2.0 + 0.3, 4.0, sx, sy - cy, -1))
    return solid


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

    ribs, shelf_cuts = pi_shelf_ribs()
    body = body.fuse(ribs)

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
              + drive_axle_features()
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

    # The shelf is a separate print now, so it has to be checked the same way
    # and then checked again in place: it must land on the ribs without
    # fouling anything, and its clearance holes must sit over the tapped ones.
    shelf_check = pi_shelf_plate()
    if len(shelf_check.Solids) != 1:
        raise RuntimeError(f"pi shelf built as {len(shelf_check.Solids)} solids")

    arm_shape = caster_arm()
    wheel_shape = caster_wheel()
    cap_shape = motor_cap()
    shelf_shape = pi_shelf_plate()

    # --- assembly guards -------------------------------------------------
    # Param checks in preview/validate.py cannot see any of this. They compare
    # numbers to numbers; every defect guarded below was a solid that either
    # missed what it was meant to cut or landed inside something else, and all
    # of them survived a full-PASS validate run and reached the print bed.

    lo, hi = _pocket_span(1)
    cx = (lo + hi) / 2.0
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

    # The motor now drops straight down: nothing of it passes through the wall.
    # Check it seated hard against the bearing shoulder on both sides.
    for sgn in (-1, 1):
        p_lo, p_hi = _pocket_span(sgn)
        x0 = p_hi - P["motor_body_len"] if sgn > 0 else p_lo
        seated = Part.makeCylinder(
            P["motor_dia"] / 2.0, P["motor_body_len"],
            Vector(x0, Y_REAR, AXLE), Vector(1, 0, 0))
        clash = seated.common(tub_shape).Volume
        if clash > 1e-6:
            side = "left" if sgn < 0 else "right"
            raise RuntimeError(f"motor does not fit the {side} pocket: "
                               f"{clash:.1f} mm3 interference")

    # The bearing seat must have a shoulder behind it, or the bearing presses
    # straight through into the motor pocket. Probe the annulus between the hub
    # clearance bore and the seat, just inboard of the seat: it must be solid.
    for sgn in (-1, 1):
        x_sh = min(sgn * (X_WALL - P["drive_bearing_w"]),
                   sgn * (X_WALL_IN - P["drive_boss_t"]))
        ring = L.cyl(P["drive_bearing_od"] / 2.0, 0.8, x_sh, Y_REAR, AXLE, axis="x")
        ring = ring.cut(L.cyl(P["drive_hub_od"] / 2.0 + 0.5, 2.0,
                              x_sh - 0.6, Y_REAR, AXLE, axis="x"))
        present = ring.common(tub_shape).Volume
        if present < 0.5 * ring.Volume:
            side = "left" if sgn < 0 else "right"
            raise RuntimeError(f"{side} drive bearing seat has no shoulder: only "
                               f"{present:.1f} of {ring.Volume:.1f} mm3 present")

    # Every side-wall shaft hole must actually be open, on both sides.
    n = int(P["roadwheels_per_side"])
    span = P["wheelbase"] * 0.6
    wall_holes = [("drive bearing seat", Y_REAR, P["drive_bearing_od"] / 2.0),
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
            # ...and must not be oversized. Something has to remain solid just
            # outside the nominal diameter: a hole that is merely open passes
            # the check above even when a stray full-width cut has opened it to
            # half again its size, which is how the idler locating holes first
            # came out at 5.2 mm instead of 3.2 mm.
            wide = L.cyl(r + 0.75, WALL + 0.6,
                         min(sgn * X_WALL, sgn * X_WALL_IN) - 0.3, y, AXLE, axis="x")
            if wide.common(tub_shape).Volume < 1e-6:
                side = "left" if sgn < 0 else "right"
                raise RuntimeError(f"{name} hole in the {side} wall is oversized: "
                                   f"nothing solid at +1.5 mm on diameter")

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

    # Shelf in its assembled position: it should touch the rib tops and nothing
    # else, and every screw must find a tapped hole under it.
    z_shelf = Z0 + WALL + P["pi_shelf_z"]
    placed = shelf_check.copy()
    placed.translate(Vector(0, Y_FRONT - 28, z_shelf))
    clash = placed.common(tub_shape).Volume
    if clash > 1e-6:
        raise RuntimeError(f"pi shelf fouls the tub by {clash:.1f} mm3 "
                           "in its assembled position")
    depth = P["motor_cap_screw_depth"]
    for sx, sy in _shelf_screw_xy():
        pilot = L.cyl(P["m2_tap_dia"] / 2.0 * 0.8, depth - 1, sx, sy,
                      z_shelf - depth + 0.5)
        blocked = pilot.common(tub_shape).Volume
        if blocked > 1e-6:
            raise RuntimeError(f"no tapped hole under the shelf screw at "
                               f"({sx:+.1f}, {sy:+.1f}): {blocked:.1f} mm3")

    # The bay's aft end must be open so the pack can run back past the ring.
    # Probe the cavity, not the ring: the ring's side walls overlap the cradle
    # by 0.5 mm on purpose, so anything sampling their x band always trips.
    aft_gap = L.box(P["battery_w"] + 2 * P["battery_clear"], 4.0,
                    P["battery_h"] * 0.6, 0, P["bay_aft_y"] - 2.0, Z0 + WALL)
    blocked = aft_gap.common(tub_shape).Volume
    if blocked > 1e-6:
        raise RuntimeError(f"battery bay is walled off at its aft end by "
                           f"{blocked:.1f} mm3 -- the pack is longer than the "
                           "ring and has to run past it")
    L.export(tub_shape, os.path.join(STL, "chassis_tub_v1.stl"))
    L.export(deck_shape, os.path.join(STL, "chassis_deck_v1.stl"))
    L.export(arm_shape, os.path.join(STL, "caster_arm_v1.stl"))
    L.export(wheel_shape, os.path.join(STL, "caster_wheel_v1.stl"))
    L.export(cap_shape, os.path.join(STL, "motor_cap_v1.stl"))
    L.export(shelf_shape, os.path.join(STL, "pi_shelf_v1.stl"))

    for shp, nm in ((tub_shape, "chassis_tub"), (deck_shape, "chassis_deck"),
                    (arm_shape, "caster_arm"), (wheel_shape, "caster_wheel"),
                    (cap_shape, "motor_cap"), (shelf_shape, "pi_shelf")):
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "chassis_assembly_v1.FCStd"))
    print("chassis: tub bbox", tub_shape.BoundBox)
    print("chassis: deck bbox", deck_shape.BoundBox)


if __name__ == "__main__":
    main()
