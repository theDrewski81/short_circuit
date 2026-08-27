"""Johnny 5 - chassis / tread base build script (Phase 00, Task 7).

Run headless:   freecadcmd build_chassis.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs (relative to repo root):
    mechanical/stl/chassis_tub_v1.stl
    mechanical/stl/chassis_deck_v1.stl
    mechanical/stl/tail_boom_v1.stl
    mechanical/stl/tail_roller_v1.stl
    mechanical/stl/tail_tyre_v1.stl       (TPU 90A)
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
AXLE = P["axle_z"]                 # sprocket / idler axle line
RW_AXLE = P["roadwheel_axle_z"]    # road-wheel axle line, 8 mm lower
Y_IDLER = P["idler_slot_cy"]       # centre of the idler tensioning slot
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


def _wall_hole(sgn, y, z, r, thick, margin=1.0):
    """Through-hole in a wall of local thickness `thick` on side `sgn`.

    `thick` is measured inboard from the wall's outer face, so the same helper
    serves the plain 2.4 mm wall and the thicker skirt pads carrying the
    road-wheel rods.
    """
    x0 = min(sgn * X_WALL, sgn * (X_WALL - thick)) - margin
    return L.cyl(r, thick + 2 * margin, x0, y, z, axis="x")


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
    hub_clear = P["drive_hub_clear"]
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


# --- idler tensioning slot -----------------------------------------------
def idler_features():
    """Fore-aft slot and carrier bosses for the tensioned idler rod.

    The rod no longer sits in a fixed hole. The printed track loop closes at a
    119.38 mm straight run -- 29 lugs at the sprocket's own 12.566 mm tooth
    pitch -- which is 0.62 mm shorter than the nominal 120 mm wheelbase, so even
    at zero strain the rod does not belong at Y_FRONT. It runs in a slot, is
    located by a carrier inside the tub, and pretension is whatever the carrier
    gets clamped at: 1 mm forward is 2 mm of path, 0.55 % strain in the TPU.

    The old inner-face pads are gone with the fixed hole. Their job was shaft
    bearing length, which the carrier now provides; left in place they would
    only hold the carrier off the wall.

    The carrier bears on two bosses rather than on the wall itself, because the
    wall is 2.4 mm and an M2 thread needs more than that. The boss end faces are
    what the carrier slides across, and they stay clear of its slot travel by
    being centred on the fixed tapped holes.
    """
    solids, cuts = [], []
    r = P["axle_hole_dia"] / 2.0
    ln = P["idler_slot_len"]
    bt = P["idler_boss_t"]
    depth = bt + WALL - 0.4                       # blind: never breaks the outer face
    for sgn in (-1, 1):
        x0 = min(sgn * X_WALL, sgn * X_WALL_IN) - 1.0
        cuts.append(L.box(WALL + 2, ln - 2 * r, 2 * r,
                          x0 + (WALL + 2) / 2.0, Y_IDLER, AXLE - r))
        for e in (-1, 1):
            cuts.append(L.cyl(r, WALL + 2, x0,
                              Y_IDLER + e * (ln / 2.0 - r), AXLE, axis="x"))
        for i in range(2):
            z = AXLE + P["idler_carrier_screw_z0"] + i * P["idler_carrier_screw_cc"]
            bx = min(sgn * X_WALL_IN, sgn * (X_WALL_IN - bt))
            solids.append(L.cyl(P["boss_od"] / 2.0, bt, bx, Y_IDLER, z, axis="x"))
            cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, depth, bx, Y_IDLER, z, axis="x"))
    return solids, cuts


# --- road-wheel axle skirts ----------------------------------------------
def roadwheel_axles():
    """Skirt pads below each side wall, carrying the two road-wheel rods.

    A ø24 road wheel reaches the track's inner surface only from an axle line at
    15.5 mm, and the tub floor's underside is at 18 -- so the holes the wall used
    to carry at 23.5 were 8 mm too high for the wheel to touch anything, and the
    obvious fix of lowering them lands 2.5 mm below the bottom of the wall.
    Each rod therefore gets a local pad hanging off the wall, thickened inboard
    so the rod bears on 5.4 mm of material rather than 2.4.

    Separate pads per rod rather than one long skirt: 2 g lighter, and the pad
    has no structural job between the rods.
    """
    solids, cuts = [], []
    r = P["axle_hole_dia"] / 2.0
    thick = WALL + P["skirt_pad_t"]
    z0 = P["skirt_z_bottom"]
    h = (Z0 + 1.0) - z0                            # 1 mm up into the wall/floor
    for y in j5_params.roadwheel_ys(P):
        for sgn in (-1, 1):
            solids.append(L.box(thick, P["skirt_len"], h,
                                sgn * (X_WALL - thick / 2.0), y, z0))
            cuts.append(_wall_hole(sgn, y, RW_AXLE, r, thick))
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


# --- Pi-M electronics shelf: support columns on the tub -------------------
def _shelf_screw_xy():
    """Shelf screw centres, shared by the tub's tapped columns and the plate's
    clearance holes so the two cannot land in different places."""
    return [(sx * P["pi_rib_cx"], y)
            for sx in (-1, 1) for y in j5_params.pi_column_ys(P)]


def pi_shelf_columns():
    """Columns carrying the electronics shelf. Returns (solid, cuts).

    Was two solid 8.4 x 73 mm ribs. The shelf now runs 62 mm further aft so it
    can carry the IMU breadboard as well as the Pi, and ribs at that length
    would have been 58 g of wall; three columns a side do the same job for 23 g,
    and the gaps between them are where wiring crosses underneath.

    Columns also delete the idler-rod notch. The rod crosses this band at axle
    height, and the old rib had a hole cut through it to let the rod pass;
    pi_column_ys instead places the forward column clear of the rod's travel, so
    there is nothing to notch and nothing to mis-align on assembly. It clamps
    the aft column off the motor cradles for the same reason: the plate reaches
    back over them now, and a column at its aft edge would stand in the motor
    drop-in pocket.
    """
    z = Z0 + WALL + P["pi_shelf_z"]
    depth = P["motor_cap_screw_depth"]
    solid, cuts = None, []
    for sx, sy in _shelf_screw_xy():
        col = L.box(P["pi_rib_t"], P["pi_column_len"], z - (Z0 + WALL),
                    sx, sy, Z0 + WALL)
        solid = col if solid is None else solid.fuse(col)
        cuts.append(L.cyl(P["m2_tap_dia"] / 2.0, depth + 1, sx, sy, z - depth))
    return solid, cuts


# --- Pi-M electronics shelf plate (separate print) ------------------------
def pi_shelf_plate():
    """One shelf for all the tub electronics: Pi-M forward, IMU aft.

    Built flat about the shelf centre. Prints face down with no support -- the
    standoffs are the only thing above the plate and every hole is straight
    through.

    The IMU rides here rather than on the tub floor. On the floor it had to
    dodge the battery bay ring, which pushed it 35 mm off the centreline and
    left its forward screws under the shelf with no driver access; here it sits
    on the centreline again, which also removes the lever-arm term its
    accelerometer picked up during tank turns. The floor windows that were cut
    for weight then had nothing left to undermine.

    The IMU is not screwed to the plate directly any more. It sits on a
    38.1 x 50.8 mm solderable mini breadboard so the sensor, its pull-ups and
    its connectors can be built up and tested as one piece off the robot, and
    that board's four mounting holes are a 31.8 x 44.5 mm rectangle rather than
    the GY-521's 15 mm square. Its long axis runs along Y: 50.8 mm did not fit
    between the Pi board's aft edge and the old plate edge, which is what took
    pi_shelf_aft_ext from 38 to 62. Turned crosswise it would have fitted the
    old plate to within 2 mm a side and sat straight on top of the loom slot.

    Three passthroughs: two beside the Pi for sensor and servo wiring, one aft
    for the battery and motor loom coming up from the floor. Nothing forward --
    the 4 mm gap between the plate's front edge and the tub's front wall is
    where the ToF wiring already runs. The aft slot has to stay clear of the
    breadboard's footprint: the board stands 5 mm off the plate, and a loom
    surfacing under it would have to turn twice inside that gap to get out.
    """
    t = P["pi_shelf_t"]
    cy = P["pi_shelf_cy"]
    solid = L.box(2 * P["pi_shelf_half_w"], P["pi_shelf_len"], t, 0, 0, 0)
    for dx in (-P["pi_hole_dy"] / 2, P["pi_hole_dy"] / 2):      # short axis along X
        for dy in (-P["pi_hole_dx"] / 2, P["pi_hole_dx"] / 2):  # long axis along Y
            solid = solid.fuse(L.standoff(dx, P["pi_board_cy"] - cy + dy, t,
                                          P["pi_standoff_h"], P["boss_od"],
                                          P["m25_tap_dia"]))
    hx = P["imu_hole_cc_x"] / 2.0
    hy = P["imu_hole_cc_y"] / 2.0
    for dx in (-hx, hx):
        for dy in (-hy, hy):
            solid = solid.fuse(L.standoff(P["imu_pos_x"] + dx,
                                          P["imu_pos_y"] - cy + dy, t,
                                          P["pi_standoff_h"], P["boss_od"],
                                          P["imu_screw_tap_dia"]))
    for sx, sy in _shelf_screw_xy():
        solid = solid.cut(L.cyl(P["m2_tap_dia"] / 2.0 + 0.3, t + 2, sx, sy - cy, -1))
    for sx in (-1, 1):
        solid = solid.cut(L.box(P["pi_wire_slot_w"], P["pi_wire_slot_l"], t + 2,
                                sx * P["pi_wire_slot_x"],
                                P["pi_board_cy"] - cy, -1))
    solid = solid.cut(L.box(P["pi_loom_slot_w"], P["pi_loom_slot_l"], t + 2,
                            0, P["pi_loom_slot_cy"] - cy, -1))
    # Narrow tail. Everything aft of the cradle face gives up the outboard
    # 8.5 mm a side so the motor retention caps stay liftable and their inboard
    # screws stay drivable with the shelf fitted. The breadboard and its
    # standoffs are inside what is left.
    step_w = P["pi_shelf_half_w"] - P["pi_shelf_aft_half_w"]
    step_l = P["pi_shelf_step_y"] - P["pi_shelf_aft_y"]
    for sx in (-1, 1):
        solid = solid.cut(L.box(
            step_w, step_l, t + 2,
            sx * (P["pi_shelf_half_w"] + P["pi_shelf_aft_half_w"]) / 2.0,
            (P["pi_shelf_step_y"] + P["pi_shelf_aft_y"]) / 2.0 - cy, -1))
    return solid


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


# --- lightening pockets (side walls, blind) ------------------------------
def lightening():
    """Blind pockets only. Nothing here opens the tub to the ground.

    The four floor windows are gone. 6.7 g is not worth an opening straight
    into the electronics bay, and the battery bay ring -- the obvious place to
    take the weight from instead -- is only 6.8 g in total before its strap
    slots, so it could not fund them even if perforating the wall that retains
    a LiPo were a good idea.

    The side walls give the same weight back with no opening at all: six blind
    pockets a side, 1.4 mm into a 2.4 mm wall. The grid has to clear three
    things, and the last one is the reason for the guard below -- the idler
    carrier's tapped holes run from the inner boss face to within 0.4 mm of the
    outer face, so a pocket over one would turn a blind tap into a through-hole
    and nothing downstream would notice.
    """
    cuts = []
    depth = WALL - 1.0
    pl, ph = 28.0, 19.0
    # (y, z, y-margin, z-margin) around features the wall cannot afford to lose
    keepouts = [(Y_REAR, AXLE, 8.0 + P["drive_bearing_od"] / 2.0, 8.0),
                (Y_IDLER, AXLE, 3.0 + P["idler_slot_len"] / 2.0, 5.0)]
    for i in range(2):
        keepouts.append((Y_IDLER,
                         AXLE + P["idler_carrier_screw_z0"]
                         + i * P["idler_carrier_screw_cc"], 6.0, 6.0))
    for z0 in (21.5, 43.5):
        for yy in (-32.0, 0.0, 32.0):
            for ky, kz, ry, rz in keepouts:
                if (abs(yy - ky) < pl / 2.0 + ry
                        and abs((z0 + ph / 2.0) - kz) < ph / 2.0 + rz):
                    raise RuntimeError(
                        f"wall pocket at (y={yy:+.0f}, z={z0:.0f}) thins the wall "
                        f"over the feature at (y={ky:+.1f}, z={kz:.1f})")
            for sgn in (-1, 1):
                cuts.append(L.box(depth + 0.2, pl, ph,
                                  sgn * (X_WALL - depth / 2.0 - 0.05), yy, z0))
    # Floor pocket forward of the battery ring. Blind as well: it takes 1.4 mm
    # of the 2.4 mm floor and leaves 1.0 mm, so it is a pocket, not a window.
    cuts.append(L.box(W - 24, 18, WALL - 1.0, 0, Lg / 2 - 16, Z0))
    return cuts


# --- rear anti-tip tail mount (fused to the tub) -------------------------
def tail_mount():
    """Two tapped bosses on the rear wall for the anti-tip tail's flange.

    Replaces the trailing-caster pivot. That pivot never assembled -- its bosses
    were at x = +/-16 bored along Y while the arm's single eye was at x = 0, also
    bored along Y, so nothing lined up and the axis it did define swung the arm
    sideways rather than fore-aft. Rather than fix the linkage, the tail stopped
    being a linkage: a sprung caster that rides the ground scrubs on every tank
    turn and lifts weight off the tracks, and the tip margin it was approved for
    comes from where its wheel sits, not from it being sprung.

    Bosses are inboard so the flange can sit flat on the outer face, and the
    tapped hole runs from outside through wall plus boss for 6 mm of thread.
    """
    solids, cuts = [], []
    y_wall = -Lg / 2.0
    bt = P["idler_boss_t"]
    for sgn in (-1, 1):
        x = sgn * P["tail_mount_cc"] / 2.0
        solids.append(L.cyl(P["boss_od"] / 2.0, bt, x, y_wall + WALL,
                            P["caster_pivot_z"], axis="y"))
        cuts.append(L.cyl(P["m3_tap_dia"] / 2.0, WALL + bt - 0.4, x, y_wall,
                          P["caster_pivot_z"], axis="y"))
    return solids, cuts


# --- rear anti-tip tail (separate print) ---------------------------------
def tail_boom():
    """Fixed boom carrying the anti-tip roller, built about its flange face.

    Local origin is the flange's aft face on the tub's rear wall centreline;
    +Y is forward, so the boom runs out along -Y dead level and the fork drops
    to the axle. Level rather than sloped because the roller has to hang below
    the boom anyway, and a level bar is one less angle to get wrong.
    """
    fw, fh, ft = P["tail_flange_w"], P["tail_flange_h"], P["tail_flange_t"]
    bw, bh = P["tail_boom_w"], P["tail_boom_h"]
    ln = P["tail_boom_len"]
    drop = P["tail_axle_drop"]
    ct, cl = P["tail_cheek_t"], P["tail_cheek_len"]
    gap = P["caster_wheel_w"] + 1.5

    s = L.box(fw, ft, fh, 0, ft / 2.0, -fh / 2.0)          # flange, y 0..ft
    s = s.fuse(L.box(bw, ln + 3.0, bh, 0, (3.0 - ln) / 2.0, -bh / 2.0))
    # fork: a block straddling the roller, hollowed to two cheeks
    fork_w = gap + 2 * ct
    # Cheeks reach 6 mm past the axle, not past the roller: the roller hangs
    # free below them, and a fork sized to enclose it was 5 g of nothing.
    top = bh / 2.0
    bot = -drop - 6.0
    s = s.fuse(L.box(fork_w, cl, top - bot, 0, -ln, bot))
    s = s.cut(L.box(gap, cl + 2, (-drop + P["caster_wheel_dia"] / 2.0 + 1.0) - bot,
                    0, -ln, bot))
    s = s.cut(L.cyl(P["axle_hole_dia"] / 2.0, fork_w + 2,
                    -(fork_w + 2) / 2.0, -ln, -drop, axis="x"))
    for sx in (-1, 1):
        s = s.cut(L.cyl(P["m3_clear_dia"] / 2.0, ft + 2,
                        sx * P["tail_mount_cc"] / 2.0, -1, 0, axis="y"))
    return s


def tail_roller():
    """PLA hub for the anti-tip roller. The ground surface is the tyre, not this.

    A bare plastic roller is the wrong thing on the one part whose whole job is
    to catch the robot: on a hard floor it skitters rather than biting, and it
    is loud doing it. The hub keeps its bore round under the axle load and gives
    the tyre something to grip; the tyre does the contact.

    A lip at each edge stands proud of the hub, so the tyre seats in the valley
    between them and cannot walk off sideways. The lips stay well inside the
    tyre's outer diameter, so they never reach the floor themselves.
    """
    w = P["caster_wheel_w"]
    lw, lh = P["tail_tyre_lip_w"], P["tail_tyre_lip_h"]
    s = L.cyl(P["tail_hub_dia"] / 2.0, w, -w / 2.0, 0, 0, axis="x")
    for sx in (-1, 1):
        x0 = -w / 2.0 if sx < 0 else w / 2.0 - lw
        s = s.fuse(L.cyl(P["tail_hub_dia"] / 2.0 + lh, lw, x0, 0, 0, axis="x"))
    return s.cut(L.cyl(P["axle_hole_dia"] / 2.0, w + 2, -w / 2.0 - 1, 0, 0, axis="x"))


def tail_tyre():
    """TPU 90A tyre for the anti-tip roller. Prints with the same filament as
    the tracks, so it adds no BOM line -- only a second tiny print.

    Bored under the hub diameter by tail_tyre_fit so it goes on stretched; that
    interference plus the two hub lips is the whole retention scheme."""
    w = P["tail_tyre_w"]
    s = L.cyl(P["caster_wheel_dia"] / 2.0, w, -w / 2.0, 0, 0, axis="x")
    return s.cut(L.cyl((P["tail_hub_dia"] - P["tail_tyre_fit"]) / 2.0, w + 2,
                       -w / 2.0 - 1, 0, 0, axis="x"))


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
    # Lightening windows. The deck was 51 g of flat plate, the heaviest single
    # printed item after the tub, and it is an internal part with no sealing or
    # cosmetic job -- the torso sits on the bolt rectangle, not on the skin.
    # Laid out by hand rather than on a grid because everything it has to miss
    # is fixed: the cable slot, the four torso bolts, the two waist bosses and
    # the rim screws. The 4 mm ligament between the centre and side windows is
    # what keeps this one solid; the guard in main() is what proves it.
    for cx, cy, wx, wy in ((0, 43.5, 52, 37), (0, -43.5, 52, 37),
                           (40, 19.5, 20, 15), (-40, 19.5, 20, 15),
                           (40, -19.5, 20, 15), (-40, -19.5, 20, 15),
                           (40, 53, 20, 18), (-40, 53, 20, 18),
                           (40, -53, 20, 18), (-40, -53, 20, 18)):
        cuts.append(L.box(wx, wy, P["deck_wall"] + 1, cx, cy, -0.5))
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

    cols, shelf_cuts = pi_shelf_columns()
    body = body.fuse(cols)

    ax_solids, ax_cuts = idler_features()
    for s in ax_solids:
        body = body.fuse(s)

    sk_solids, sk_cuts = roadwheel_axles()
    for s in sk_solids:
        body = body.fuse(s)
    ax_cuts = ax_cuts + sk_cuts

    # tub-rim screw bosses for the deck. The pilot bores come back from
    # screw_boss() and must be cut -- they were previously discarded, leaving
    # solid bosses with nothing for the deck screws to thread into.
    rim_cuts = []
    for bx, by in _rim_boss_xy():
        b, h = L.screw_boss(bx, by, ZTOP - 8, 8, P["boss_od"], P["m2_tap_dia"])
        body = body.fuse(b)
        rim_cuts.append(h)

    # rear anti-tip tail mount
    rp_solids, rp_cuts = tail_mount()
    for s in rp_solids:
        body = body.fuse(s)

    # subtract all cuts
    for c in (mc_cuts + bcuts + ax_cuts + shelf_cuts
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

    for shp, nm in ((tail_boom(), "tail boom"), (tail_roller(), "tail roller hub"),
                    (tail_tyre(), "tail tyre")):
        if len(shp.Solids) != 1:
            raise RuntimeError(f"{nm} built as {len(shp.Solids)} solids")

    arm_shape = tail_boom()
    wheel_shape = tail_roller()
    tyre_shape = tail_tyre()
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

    # Every side-wall shaft hole must actually be open, on both sides. Each
    # entry carries its own z and its own local wall thickness now: the road
    # wheels sit 8 mm lower than the sprocket and pass through the 5.4 mm skirt
    # pads, not the 2.4 mm wall.
    ah = P["axle_hole_dia"] / 2.0
    skirt_t = WALL + P["skirt_pad_t"]
    travel = P["idler_slot_travel"] / 2.0
    wall_holes = [("drive bearing seat", Y_REAR, AXLE,
                   P["drive_bearing_od"] / 2.0, WALL),
                  ("idler slot, slack end", Y_IDLER - travel, AXLE, ah, WALL),
                  ("idler slot, taut end", Y_IDLER + travel, AXLE, ah, WALL)]
    for y in j5_params.roadwheel_ys(P):
        wall_holes.append((f"road wheel y={y:+.0f}", y, RW_AXLE, ah, skirt_t))
    for name, y, z, r, thick in wall_holes:
        for sgn in (-1, 1):
            side = "left" if sgn < 0 else "right"
            x0 = min(sgn * X_WALL, sgn * (X_WALL - thick))
            probe = L.cyl(r * 0.8, thick + 1, x0 - 0.5, y, z, axis="x")
            blocked = probe.common(tub_shape).Volume
            if blocked > 1e-6:
                raise RuntimeError(f"{name} hole is not open in the {side} wall: "
                                   f"{blocked:.1f} mm3 still in the bore")
            # ...and must not be oversized. Something has to remain solid just
            # outside the nominal diameter: a hole that is merely open passes
            # the check above even when a stray full-width cut has opened it to
            # half again its size, which is how the idler locating holes first
            # came out at 5.2 mm instead of 3.2 mm.
            wide = L.cyl(r + 0.75, thick - 0.4, x0 - 0.3, y, z, axis="x")
            if wide.common(tub_shape).Volume < 1e-6:
                raise RuntimeError(f"{name} hole in the {side} wall is oversized: "
                                   f"nothing solid at +1.5 mm on diameter")

    # Each rod runs the full width of the tub, so its whole length has to be
    # clear -- not just the two holes it passes through. The road-wheel rods
    # run below the floor in open air; the idler rod crosses the tub interior
    # and has to miss the shelf ribs at every tension setting.
    rods = [("idler rod", Y_IDLER, AXLE, P["idler_slot_len"]),
            ("idler rod, taut end", Y_IDLER + travel, AXLE, 0.0)]
    rods += [(f"road-wheel rod y={y:+.0f}", y, RW_AXLE, 0.0)
             for y in j5_params.roadwheel_ys(P)]
    for name, y, z, _ in rods:
        # probe the rod itself, not the hole: at hole radius this check trips
        # on the 0.1 mm of clearance the hole is supposed to have.
        rod = L.cyl(P["idler_axle_dia"] / 2.0, 2 * X_WALL + 4,
                    -X_WALL - 2, y, z, axis="x")
        fouled = rod.common(tub_shape).Volume
        if fouled > 1e-6:
            raise RuntimeError(f"{name} is obstructed by {fouled:.1f} mm3 along "
                               "its length")

    # Keep-outs: volumes that have to stay empty for the robot to go together.
    pack = L.box(P["battery_w"], P["battery_l"], P["battery_h"], 0, -6, Z0 + WALL)
    clash = pack.common(tub_shape).Volume
    if clash > 1e-6:
        raise RuntimeError(f"battery envelope obstructed by {clash:.1f} mm3 -- "
                           "the pack cannot seat")

    # The IMU shares the shelf with the Pi now, so what has to be proved is that
    # the two do not want the same space -- the same class of error as the old
    # floor pad, where the battery bay and the IMU both wanted the centroid and
    # neither knew about the other.
    # 12 mm is the height budget above the standoffs, not a measurement. Both
    # stacks measure about 21 mm off the plate as bought and are cut down at the
    # GPIO headers to fit it; there is 14.2 mm to the rim, so the budget has
    # 2.2 mm in hand and the rim check below is what holds it.
    z_top = Z0 + WALL + P["pi_shelf_z"] + P["pi_shelf_t"] + P["pi_standoff_h"]
    board = L.box(P["pi_w"], P["pi_l"], 12.0, 0, P["pi_board_cy"], z_top)
    imu = L.box(P["imu_board_w"], P["imu_board_l"], 12.0,
                P["imu_pos_x"], P["imu_pos_y"], z_top)
    clash = board.common(imu).Volume
    if clash > 1e-6:
        raise RuntimeError(f"Pi-M board and IMU overlap on the shelf by "
                           f"{clash:.1f} mm3")
    for env, nm in ((board, "Pi-M board"), (imu, "IMU")):
        c = env.common(tub_shape).Volume
        if c > 1e-6:
            raise RuntimeError(f"{nm} envelope fouls the tub by {c:.1f} mm3")
        if env.BoundBox.ZMax > ZTOP:
            raise RuntimeError(f"{nm} stands {env.BoundBox.ZMax - ZTOP:.1f} mm "
                               "proud of the tub rim; the deck will not close")

    # The aft loom slot has to surface beside the breadboard, not under it.
    # Footprints only -- both are projected up from the plate, so this is a 2D
    # overlap dressed as a volume.
    loom = L.box(P["pi_loom_slot_w"], P["pi_loom_slot_l"], 12.0,
                 0, P["pi_loom_slot_cy"], z_top)
    clash = imu.common(loom).Volume
    if clash > 1e-6:
        raise RuntimeError(f"the IMU breadboard covers the aft loom slot by "
                           f"{clash:.1f} mm3 of footprint")

    # Shelf in its assembled position: it should touch the rib tops and nothing
    # else, and every screw must find a tapped hole under it.
    z_shelf = Z0 + WALL + P["pi_shelf_z"]
    placed = shelf_check.copy()
    placed.translate(Vector(0, P["pi_shelf_cy"], z_shelf))
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

    # The plate reaches back over both motor cradles now, so it has to stay out
    # from over the retention caps. Sweep each fitted cap straight up to the
    # rim: anything of the shelf in that column is a cap that cannot come out
    # and, at 20 mm inboard, a cap screw with no driver over it -- the same
    # buried-fastener defect that took the IMU off the tub floor.
    for sgn in (-1, 1):
        lo, hi = _pocket_span(sgn)
        fitted = cap_shape.copy()
        fitted.translate(Vector((lo + hi) / 2.0, Y_REAR, AXLE))
        cb = fitted.BoundBox
        lift = L.box(cb.XLength, cb.YLength, ZTOP - cb.ZMax,
                     (cb.XMin + cb.XMax) / 2.0, (cb.YMin + cb.YMax) / 2.0, cb.ZMax)
        roofed = lift.common(placed).Volume
        if roofed > 1e-6:
            side = "right" if sgn > 0 else "left"
            raise RuntimeError(f"the shelf roofs {roofed:.0f} mm3 of the {side} "
                               "motor cap's lift path; the cap cannot come out "
                               "with the shelf fitted")

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
    # The tail has to bolt on and its roller has to end up where the tip
    # calculation assumes. The old caster failed both: bosses bored on one axis,
    # an arm eye on another, and a wheel hanging 6 mm clear of the floor with
    # nothing to bring it down.
    tail = tail_boom()
    tail.translate(Vector(0, P["tail_mount_y"] - P["tail_flange_t"],
                          P["caster_pivot_z"]))
    clash = tail.common(tub_shape).Volume
    if clash > 1e-6:
        raise RuntimeError(f"tail boom fouls the tub by {clash:.1f} mm3")
    for sx in (-1, 1):
        x = sx * P["tail_mount_cc"] / 2.0
        pilot = L.cyl(P["m3_tap_dia"] / 2.0 * 0.8, WALL + P["idler_boss_t"] - 1.0,
                      x, -Lg / 2.0 + 0.5, P["caster_pivot_z"], axis="y")
        blocked = pilot.common(tub_shape).Volume
        if blocked > 1e-6:
            raise RuntimeError(f"no tapped hole behind the tail flange bolt at "
                               f"x={x:+.0f}: {blocked:.1f} mm3")
    z_axle = P["caster_pivot_z"] - P["tail_axle_drop"]
    roller = tail_roller()
    roller.translate(Vector(0, P["tail_contact_y"], z_axle))
    tyre = tail_tyre()
    tyre.translate(Vector(0, P["tail_contact_y"], z_axle))
    for shp, nm in ((roller, "roller hub"), (tyre, "tyre")):
        if shp.common(tail).Volume > 1e-6:
            raise RuntimeError(f"anti-tip {nm} does not fit between the fork cheeks")
    # The tyre has to be the thing that touches, and it has to be a tyre: bored
    # under the hub so it goes on stretched, and with the hub's lips buried well
    # inside its outer diameter so they never reach the floor.
    if roller.common(tyre).Volume <= 1e-6:
        raise RuntimeError("tyre bore is not an interference fit on the hub")
    if roller.BoundBox.ZMin <= tyre.BoundBox.ZMin + 1.0:
        raise RuntimeError(f"hub reaches z={roller.BoundBox.ZMin:.2f} against the "
                           f"tyre at {tyre.BoundBox.ZMin:.2f}; the lips would ground")
    low = tyre.BoundBox.ZMin
    if abs(low - P["caster_float"]) > 1e-6:
        raise RuntimeError(f"anti-tip tyre sits {low:.2f} mm off the floor, "
                           f"not the {P['caster_float']:.1f} mm it is designed to")
    if tail.BoundBox.ZMin <= low:
        raise RuntimeError(f"tail structure reaches z={tail.BoundBox.ZMin:.1f}, "
                           f"below the roller at {low:.1f} -- it would ground first")

    # The underside is a floor, not a grille. Probe it just below the skin and
    # again just above it: material missing from both is a hole right through.
    # The two the motors make are unavoidable -- a ø12 motor on a 23.5 mm axle
    # line has its belly at 17.5, below the tub's own underside at 18.0 -- so
    # they are named and allowed, and anything else is a mistake.
    lo = L.box(W, Lg, 0.2, 0, 0, Z0 + 0.05)
    hi = L.box(W, Lg, 0.2, 0, 0, Z0 + WALL - 0.25)
    lo_open = lo.cut(tub_shape)
    hi_open = hi.cut(tub_shape)
    hi_open.translate(Vector(0, 0, -(WALL - 0.3)))     # onto the lower probe
    through = lo_open.common(hi_open)
    area = through.Volume / 0.2
    motor_holes = 2 * (P["motor_pocket_l"] + 1) * (P["motor_dia"] + P["motor_fit_clear"])
    if area > motor_holes:
        raise RuntimeError(f"{area:.0f} mm2 of the tub underside is open right "
                           f"through, more than the {motor_holes:.0f} mm2 the "
                           "motor pockets account for")

    L.export(tub_shape, os.path.join(STL, "chassis_tub_v1.stl"))
    L.export(deck_shape, os.path.join(STL, "chassis_deck_v1.stl"))
    L.export(arm_shape, os.path.join(STL, "tail_boom_v1.stl"))
    L.export(wheel_shape, os.path.join(STL, "tail_roller_v1.stl"))
    L.export(tyre_shape, os.path.join(STL, "tail_tyre_v1.stl"))
    L.export(cap_shape, os.path.join(STL, "motor_cap_v1.stl"))
    L.export(shelf_shape, os.path.join(STL, "pi_shelf_v1.stl"))

    for shp, nm in ((tub_shape, "chassis_tub"), (deck_shape, "chassis_deck"),
                    (arm_shape, "tail_boom"), (wheel_shape, "tail_roller"),
                    (tyre_shape, "tail_tyre"),
                    (cap_shape, "motor_cap"), (shelf_shape, "pi_shelf")):
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "chassis_assembly_v1.FCStd"))
    print("chassis: tub bbox", tub_shape.BoundBox)
    print("chassis: deck bbox", deck_shape.BoundBox)


if __name__ == "__main__":
    main()
