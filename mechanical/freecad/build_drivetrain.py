"""Johnny 5 - drivetrain build script (Phase 00, Session 04).

Run headless:   freecadcmd build_drivetrain.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs (relative to repo root):
    mechanical/stl/drive_sprocket_v1.stl   (print x2)
    mechanical/stl/front_idler_v1.stl      (print x2)
    mechanical/stl/road_wheel_v1.stl       (print x4)
    mechanical/stl/track_loop_v1.stl       (print x2, TPU 90A)
    mechanical/stl/idler_carrier_v1.stl    (print x2)
    mechanical/freecad/drivetrain_v1.FCStd

Coordinate frame matches build_chassis.py: origin at the centre of the track
footprint on the ground plane, +X right, +Y forward, +Z up.

Track system
------------
Centre-guide lug track. The TPU loop carries one central row of lugs on its
inner face. The drive sprocket has matching pockets in its rim and drives the
lug flanks; the idler and road wheels have a trapezoidal clearance groove and
ride the two smooth lands either side of the lug row. The lug row is also the
anti-derailment guide, and it decouples road-wheel diameter from tooth pitch --
which is what lets the ø24 road wheels sit on their own lowered axle line while
the ø40 sprocket and idler share the ø40 pitch circle.

Loop closure is exact rather than approximate: the lug pitch is the sprocket's
tooth pitch by construction (pi * 40 / 10 = 12.566 mm), and 29 lugs make a
364.42 mm inner path. That wants a 119.38 mm straight run rather than the tub's
nominal 120 mm wheelbase, so the idler rod sits 0.62 mm aft of nominal at zero
strain and is pulled forward in its slot to pretension. Every millimetre of
forward travel adds 2 mm of path, i.e. 0.55 % strain.

Print orientation
-----------------
Every part is built about the origin. The wheels keep their assembled axis
(along X) because they are bodies of revolution and their orientation on the
bed is the slicer's business -- but they are shaped so that with the axis
vertical nothing needs support: the lightening is full-width through-features
(vertical walls), and both the groove ceiling and the track's lug flanks are
45 deg or steeper. The track loop is built with its loop plane in XY and the
width running up +Z, and is rotated into place only for the checks.

The loop is built in two forms from one parameter set and one traversal
function. "running" is the shape it takes on the robot, wrapped round a
sprocket and an idler track_straight_len apart: every clearance question is
asked in that state, so that is the form the assembly checks and the document
view use. "print" is a circle of the same inner path, r = 58.0, and is the form
that becomes the STL -- see track_print_r in j5_params.derive() for why a
circle, and why the radius is not a free choice. The two are pinned together at
the end of main().
"""

import math
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
AXLE = P["axle_z"]                    # sprocket / idler axle line
RW_AXLE = P["roadwheel_axle_z"]       # road-wheel axle line (smaller wheel, lower)
Y_REAR = -P["wheelbase"] / 2.0        # drive sprocket
Y_IDLER = P["idler_y_nom"]            # idler at zero track strain
X_SPR = P["sprocket_x"]               # track centreline, +X side
X_WALL = P["tub_width"] / 2.0         # side-wall outer face
WID = P["wheel_width"]
R_IN = P["track_inner_r"]             # 20.0 -- band inner surface / wheel land radius
R_OUT = P["track_outer_r"]            # 23.5 -- ground contact radius


# --- shared wheel primitives ---------------------------------------------

def _blank(od):
    """Wheel blank: axis along X, centred on the origin."""
    return L.cyl(od / 2.0, WID, -WID / 2.0, 0, 0, axis="x")


def _rim_in_r(od):
    """Inner radius of the rim, or None when the wheel is too small to lighten."""
    r = od / 2.0 - P["wheel_groove_depth"] - P["wheel_rim_wall"]
    return r if r - P["wheel_hub_od"] / 2.0 >= 5.0 else None


def _groove_cut(od):
    """Trapezoidal centre groove clearing the lug row (idler and road wheel).

    Revolved rather than boolean-differenced from cylinders because the flanks
    are tapered: they follow the lug's 45 deg flare, which keeps the side
    clearance even all the way down instead of only at the mouth, and turns the
    groove ceiling into a 49 deg slope that prints without support.

    On a wheel big enough to lighten, the groove runs on down to the rim inner
    radius instead of stopping at the lug tip. The floor it would otherwise
    leave is 4.2 g of material per ø40 wheel doing nothing: the two running
    lands are already tied to the spokes through the full-thickness ring either
    side of the groove.
    """
    r = od / 2.0
    d = P["wheel_groove_depth"]
    a = P["wheel_groove_w"] / 2.0          # half width at the mouth
    b = P["wheel_groove_root_w"] / 2.0     # half width at the root
    floor = _rim_in_r(od)
    pts = [Vector(-a, 0, r), Vector(-b, 0, r - d)]
    if floor is not None:
        pts += [Vector(-b, 0, floor), Vector(b, 0, floor)]
    pts += [Vector(b, 0, r - d), Vector(a, 0, r),
            Vector(a, 0, r + 2.0), Vector(-a, 0, r + 2.0)]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.revolve(Vector(0, 0, 0), Vector(1, 0, 0), 360.0)


def _bearing_seat(sgn):
    """623ZZ press seat opening on the +X (sgn=+1) or -X face."""
    w = P["bearing_623_w"] + 0.2
    r = P["bearing_623_seat_od"] / 2.0
    x0 = WID / 2.0 - w if sgn > 0 else -WID / 2.0
    return L.cyl(r, w, x0, 0, 0, axis="x")


def _through_bore(dia):
    return L.cyl(dia / 2.0, WID + 2.0, -WID / 2.0 - 1.0, 0, 0, axis="x")


def _lighten(solid, od):
    """Replace the solid interior with a hub and full-width spokes.

    Through-features only. With the wheel axis vertical on the bed every face
    added here is a vertical wall, so the part prints with no support at all --
    which a mid-plane web or a blind annular pocket would not.
    """
    rim_in_r = _rim_in_r(od)
    hub_r = P["wheel_hub_od"] / 2.0
    if rim_in_r is None:
        return solid          # ø24 road wheel: nothing worth removing
    solid = solid.cut(L.cyl(rim_in_r, WID + 2.0, -WID / 2.0 - 1.0, 0, 0, axis="x"))
    solid = solid.fuse(L.cyl(hub_r, WID, -WID / 2.0, 0, 0, axis="x"))
    n = int(P["wheel_spokes"])
    for i in range(n):
        spoke = L.box(WID, P["wheel_spoke_w"],
                      (rim_in_r + 0.5) - (hub_r - 0.5), 0, 0, hub_r - 0.5)
        spoke.rotate(Vector(0, 0, 0), Vector(1, 0, 0), i * 360.0 / n)
        solid = solid.fuse(spoke)
    return solid


def _d_bore(dia, flat_half, length, x0):
    """D-profile bore cut solid, axis along X, open at x0, running +X."""
    c = L.cyl(dia / 2.0, length, x0, 0, 0, axis="x")
    r = dia / 2.0 + 1.0
    keep = L.box(length, flat_half + r, 2 * r,
                 x0 + length / 2.0, (flat_half - r) / 2.0, -r)
    return c.common(keep)


def _land_probe(od, over):
    """Two thin rings at the wheel's running lands, grown by `over` on radius.

    Used to prove contact. A tangency shares zero volume with the track, exactly
    like a 5 mm gap does, so contact can only be shown by growing the wheel until
    it must intersect. The probe is confined to the lands so it cannot be fooled
    by clipping a lug in the groove.
    """
    lw = P["wheel_land_w"]
    rings = None
    for x0 in (-WID / 2.0, WID / 2.0 - lw):
        ring = L.cyl(od / 2.0 + over, lw, x0, 0, 0, axis="x")
        rings = ring if rings is None else rings.fuse(ring)
    return rings


# --- drive sprocket ------------------------------------------------------

def drive_sprocket():
    """ø40 pitch, 10 lug pockets, stepped hub for the MR106ZZ in the rear wall.

    Built in right-hand-side orientation: inboard is -X. Symmetric about its
    axis, so one print serves both sides -- the left one is the same part turned
    end for end.

    Unlike the idler there is no continuous groove: the centre band stays at
    full radius except at the ten pockets, and that full-radius material between
    pockets is what drives the lug flanks.
    """
    od = P["sprocket_pitch_dia"]
    s = _blank(od)

    pw = P["wheel_groove_w"]
    pl = P["track_lug_len"] + P["lug_pocket_clear"]
    # Pockets run to the rim inner radius, not just past the lug tip: the lug
    # cannot bottom out either way, and the deeper cut is 3 g off the sprocket.
    root_r = _rim_in_r(od) or (od / 2.0 - P["wheel_groove_depth"])
    for i in range(int(P["sprocket_teeth"])):
        pocket = L.box(pw, pl, (od / 2.0 + 1.0) - root_r, 0, 0, root_r)
        pocket.rotate(Vector(0, 0, 0), Vector(1, 0, 0),
                      i * 360.0 / P["sprocket_teeth"])
        s = s.cut(pocket)

    s = _lighten(s, od)

    # stepped hub, inboard: collar (set screw) then journal (MR106ZZ + wall land)
    x_face = -WID / 2.0
    x_collar = x_face - P["sprocket_collar_len"]
    x_journal = x_collar - P["sprocket_journal_len"]
    s = s.fuse(L.cyl(P["sprocket_collar_od"] / 2.0, P["sprocket_collar_len"],
                     x_collar, 0, 0, axis="x"))
    s = s.fuse(L.cyl(P["drive_hub_od"] / 2.0, P["sprocket_journal_len"],
                     x_journal, 0, 0, axis="x"))

    # D-bore for the ø3 D-shaft. Torque goes through the flat; the grub screw
    # only stops the sprocket walking off the shaft.
    s = s.cut(_d_bore(P["motor_shaft_dia"] + 0.05, P["motor_shaft_flat_half"],
                      P["motor_shaft_len"] + 1.0, x_journal))
    s = s.cut(L.cyl(P["m25_tap_dia"] / 2.0, P["sprocket_collar_od"],
                    x_collar + P["sprocket_collar_len"] / 2.0, 0, 0, axis="z"))
    return s


# --- front idler ---------------------------------------------------------

def front_idler():
    """ø40 idler on the full-width 3 mm rod, two 623ZZ in the hub."""
    od = P["idler_dia"]
    s = _blank(od)
    s = s.cut(_groove_cut(od))
    s = _lighten(s, od)
    s = s.cut(_bearing_seat(+1))
    s = s.cut(_bearing_seat(-1))
    s = s.cut(_through_bore(P["axle_hole_dia"]))
    return s


# --- road wheel ----------------------------------------------------------

def road_wheel():
    """ø24 road wheel: one 623ZZ at the inboard face, plain land outboard.

    Inboard is -X, which is the side the skirt supports the rod from, so the
    bearing sits closest to its support and the plain land only has to stop the
    wheel cocking. Symmetric by flip, so one printed part serves all four.
    """
    od = P["roadwheel_dia"]
    s = _blank(od)
    s = s.cut(_groove_cut(od))
    s = _lighten(s, od)
    s = s.cut(_bearing_seat(-1))
    s = s.cut(_through_bore(P["axle_hole_dia"]))
    return s


# --- idler tensioner carrier ---------------------------------------------

def idler_carrier():
    """Locates the idler rod and clamps it anywhere along the wall slot.

    Sits against the side wall's inner face. The wall carries only a plain
    fore-aft slot; the rod is located by this carrier, and tension is set by
    sliding it and then pinching it to the wall with two M2 screws.

    Both screws are above the rod, not straddling it: the tub floor is 3.1 mm
    below the axle line, so a plate symmetric about the rod would be buried in
    the floor. Stacked vertically they still take the fore-aft moment that track
    tension applies about the rod.

    Built flat about the rod centre -- thickness along X, height up +Z -- so it
    prints on its back face with no overhangs.
    """
    t = P["idler_carrier_t"]
    h = P["idler_carrier_h"]
    drop = P["idler_carrier_drop"]
    w = P["axle_hole_dia"] + 14.0
    s = L.box(t, w, h, t / 2.0, 0, -drop)
    # rod bore: close fit, this is what actually locates the shaft
    s = s.cut(L.cyl(P["idler_axle_dia"] / 2.0 + 0.05, t + 2.0, -1.0, 0, 0, axis="x"))
    travel = P["idler_slot_travel"]
    slot_d = P["m2_tap_dia"] + 0.6
    for i in range(2):
        z = P["idler_carrier_screw_z0"] + i * P["idler_carrier_screw_cc"]
        s = s.cut(L.box(t + 2.0, travel, slot_d, t / 2.0, 0, z - slot_d / 2.0))
        for sy in (-1, 1):
            s = s.cut(L.cyl(slot_d / 2.0, t + 2.0, -1.0, sy * travel / 2.0, z,
                            axis="x"))
    return s


# --- axle collar ---------------------------------------------------------

def axle_collar():
    """Grub-screw collar that stops a rod sliding along its own axis.

    Each of the three rods runs the full 176 mm from one wheel's outer face to
    the other's, so it passes right through the tub and out the far side. The
    wheels themselves cannot walk sideways -- the lug row sits in their groove
    and holds them to +/-0.5 mm -- but nothing stops the rod, so one collar
    clamps inboard of each wall. Print six.
    """
    od = P["axle_collar_od"]
    ln = P["axle_collar_len"]
    s = L.cyl(od / 2.0, ln, -ln / 2.0, 0, 0, axis="x")
    s = s.cut(L.cyl(P["idler_axle_dia"] / 2.0 + 0.05, ln + 2, -ln / 2.0 - 1,
                    0, 0, axis="x"))
    s = s.cut(L.cyl(P["m25_tap_dia"] / 2.0, od, 0, 0, 0, axis="z"))
    return s


# --- TPU track loop ------------------------------------------------------

def _path_point(s_arc, r=None, straight=None):
    """(position, outward-normal angle in degrees) at arc length s_arc along the
    path at radius r, in the loop's build frame: long axis Y, short axis X.

    Defaults to the inner surface of the running form, where the lugs live; the
    treads call it with the outer valley radius instead. The print form passes
    straight=0, which degenerates the stadium into a circle and needs no second
    traversal function -- the two straight branches below simply never fire.
    """
    S = P["track_straight_len"] if straight is None else straight
    if r is None:
        r = R_IN
    arc = math.pi * r
    if s_arc < S:                                   # right straight, +X side
        return (r, -S / 2.0 + s_arc), 0.0
    s_arc -= S
    if s_arc < arc:                                 # front turn
        th = s_arc / r
        return (r * math.cos(th), S / 2.0 + r * math.sin(th)), math.degrees(th)
    s_arc -= arc
    if s_arc < S:                                   # left straight, -X side
        return (-r, S / 2.0 - s_arc), 180.0
    s_arc -= S
    th = s_arc / r                                  # rear turn
    return (-r * math.cos(th), -S / 2.0 - r * math.sin(th)), 180.0 + math.degrees(th)


def _lug_solid():
    """One centre lug, root face on the YZ plane at x=0, extending -X.

    Trapezoidal across the track width: the tip is narrower than the root by a
    45 deg flare each side. The loop prints with its width vertical, so a
    straight-sided centre lug would begin in mid-air 7 mm up the part; the flare
    turns that into a 45 deg overhang and leaves a root fillet where the shear
    load is highest.
    """
    h = P["track_lug_h"]
    ln = P["track_lug_len"]
    root = P["track_lug_root_w"] / 2.0
    tip = P["track_lug_tip_w"] / 2.0
    zc = P["track_width"] / 2.0
    y0 = -ln / 2.0
    pts = [Vector(0.0, y0, zc - root), Vector(-h, y0, zc - tip),
           Vector(-h, y0, zc + tip), Vector(0.0, y0, zc + root)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(Vector(0, ln, 0))


def _chevron_segments():
    """Yield (z0, dz, lean, s_off) for each segment of one chevron arm pair.

    The arms are built as a chain of short pieces, each placed on its own point
    along the path, rather than as two straight bars. A straight bar is fine on
    the flat runs and wrong on the curves: laid tangentially on the 22 mm valley
    radius, a 15 mm arm leaves the band surface 6.6 mm from its root, so 1.6 mm
    of each arm end floats free on every wrapped section and its tip stands
    1.36 mm proud of the tip radius. That is not something the single-solid
    check can see -- the bar is still attached over most of its length -- and
    the tread-tip envelope guard is what caught it.

    Five steps per arm takes the worst chord to 0.2 mm and keeps every piece
    attached everywhere on the loop.
    """
    th = math.radians(P["tread_angle"])
    half = P["track_width"] / 2.0
    k = int(P["tread_segments"])
    dz = half / k
    adv = dz * math.tan(th)
    for j in range(k):                                  # lower arm, rising aft
        yield j * dz, dz, -P["tread_angle"], j * adv
    for j in range(k):                                  # upper arm, mirrored
        yield half + j * dz, dz, P["tread_angle"], (k - j) * adv


def _chevron_piece(z0, dz, lean, ov=0.3):
    """One segment of a chevron arm: root on the YZ plane at x=0, standing +X."""
    th = math.radians(abs(lean))
    h = (dz + ov) / math.cos(th)
    bar = L.box(P["tread_depth"] + 1.0, P["tread_rib_w"], h,
                (P["tread_depth"] - 1.0) / 2.0, 0, z0)
    bar.rotate(Vector(0, 0, z0), Vector(1, 0, 0), lean)
    return bar


def _loop_form(form):
    """(inner radius, straight-run length) for one build form of the loop.

    Both forms have the same inner path, so every feature keeps its pitch across
    them, and offsetting a closed convex curve outward by dr adds exactly
    2 pi dr to its length whatever the shape -- so the tread valley path comes
    out the same in both as well, and all 24 chevrons carry over untouched.
    """
    if form == "print":
        return P["track_print_r"], 0.0
    if form == "running":
        return R_IN, P["track_straight_len"]
    raise ValueError(f"unknown track loop form {form!r}")


def track_loop(form="print"):
    """Closed TPU loop, loop plane XY, width along +Z.

    Defaults to the print form because that is the one that becomes an STL.
    Pass form="running" for the wrapped shape the assembly checks need.
    """
    r_in, S = _loop_form(form)
    r_out = r_in + P["track_thickness"]
    W = P["track_width"]

    def region(r):
        """Filled plan outline at radius r. A zero-length box is not a legal
        solid, so the circle is built as the disc it is rather than as a
        stadium with degenerate straights."""
        if S <= 0:
            return L.cyl(r, W, 0, 0, 0, axis="z")
        body = L.box(2 * r, S, W, 0, 0, 0)
        body = body.fuse(L.cyl(r, W, 0, S / 2.0, 0, axis="z"))
        body = body.fuse(L.cyl(r, W, 0, -S / 2.0, 0, axis="z"))
        return body

    band = region(r_out).cut(region(r_in))
    lug = _lug_solid()
    lugs = []
    for i in range(int(P["track_lug_count"])):
        (px, py), ang = _path_point(i * P["track_lug_pitch"], r_in, S)
        piece = lug.copy()
        piece.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
        piece.translate(Vector(px, py, 0))
        lugs.append(piece)
    band = band.multiFuse(lugs)

    # Relieve the whole ground face, then stand the herringbone back up on it.
    # Cutting the treads out of the band instead of adding them on top is what
    # keeps the tip radius at 23.5 -- proud grousers would have raised the robot,
    # lengthened the rolling radius and taken 6 % off a drive that has about 1x
    # continuous torque margin to give.
    rv = r_out - P["tread_depth"]
    band = band.cut(region(r_out).cut(region(rv)))
    core = band                       # pre-tread, for the attachment check
    n = int(P["tread_count"])
    path = 2 * S + 2 * math.pi * rv
    treads, probe = [], []
    worst = S + math.pi * rv / 2.0    # mid-curve: tightest place for a chord
    for i in range(n):
        s0 = i * path / n
        for z0, dz, lean, s_off in _chevron_segments():
            piece = _chevron_piece(z0, dz, lean)
            (px, py), ang = _path_point((s0 + s_off) % path, rv, S)
            piece.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
            piece.translate(Vector(px, py, 0))
            treads.append(piece)
    for z0, dz, lean, s_off in _chevron_segments():
        piece = _chevron_piece(z0, dz, lean)
        (px, py), ang = _path_point((worst + s_off) % path, rv, S)
        piece.rotate(Vector(0, 0, 0), Vector(0, 0, 1), ang)
        piece.translate(Vector(px, py, 0))
        probe.append(piece)
    # Every piece has to be sitting on the band, checked where the band curves
    # tightest. A piece that has drifted off it still fuses into one solid, so
    # nothing downstream would notice.
    for j, piece in enumerate(probe):
        if piece.common(core).Volume <= 1e-6:
            raise RuntimeError(f"tread segment {j} of a chevron on the curve is "
                               "not attached to the band")
    # A leaning segment swings its corners past the end of its own z range, so
    # the chevrons overhang both track edges by 0.74 mm. Trim the loop to its
    # own width: the tread arms end square at the edges, which is what they
    # should do anyway. Safe to apply to the whole band -- the band and the lugs
    # are already inside 0..track_width.
    slab = L.box(4 * r_out, 2 * S + 4 * r_out, P["track_width"], 0, 0, 0)
    return band.multiFuse(treads).common(slab)


def track_assembled(loop, sgn=1, idler_y=None):
    """Move a loop into place on side `sgn` with the idler at idler_y.

    Translates and rotates; it cannot bend. Give it the running form. A loop in
    the print form is a 123 mm ring and would sit in the tub as one, which is
    the kind of thing that passes every clearance check for the wrong reason.
    """
    if idler_y is None:
        idler_y = Y_IDLER
    if loop.BoundBox.YLength < P["track_straight_len"]:
        raise RuntimeError("track_assembled was handed a loop only "
                           f"{loop.BoundBox.YLength:.1f} mm long, shorter than "
                           f"the {P['track_straight_len']:.1f} mm straight run "
                           "it has to span -- that is the print form, not the "
                           "running form")
    s = loop.copy()
    # print frame -> assembled: rotate about Y so the loop plane becomes YZ and
    # the width runs along +X.
    s.rotate(Vector(0, 0, 0), Vector(0, 1, 0), 90.0)
    s.translate(Vector(sgn * P["track_cc"] / 2.0 - P["track_width"] / 2.0,
                       (Y_REAR + idler_y) / 2.0, AXLE))
    return s


# --- assembly ------------------------------------------------------------

def _place(shape, x, y, z, spin=0.0):
    s = shape.copy()
    if spin:
        s.rotate(Vector(0, 0, 0), Vector(1, 0, 0), spin)
    s.translate(Vector(x, y, z))
    return s


def main():
    doc = App.newDocument("drivetrain_v1")

    spr = drive_sprocket()
    idl = front_idler()
    rw = road_wheel()
    car = idler_carrier()
    col = axle_collar()
    trk = track_loop("print")            # exported
    trk_run = track_loop("running")      # checked and displayed

    parts = (("drive_sprocket", spr), ("front_idler", idl), ("road_wheel", rw),
             ("idler_carrier", car), ("axle_collar", col),
             ("track_loop", trk), ("track_loop_running", trk_run))
    for nm, shp in parts:
        n = len(shp.Solids)
        if n != 1:
            raise RuntimeError(f"{nm} built as {n} solids -- refusing to export")

    # --- loop closure, asked of the running form --------------------------
    bb = trk_run.BoundBox
    # With the ground face relieved, the loop's extreme Y falls between the
    # valley and a tread tip depending on where a chevron lands; only the X
    # extremes are guaranteed to sit on one, because the straight runs are an
    # exact whole number of pitches apart.
    lo = P["track_straight_len"] + 2 * P["tread_valley_r"]
    hi = P["track_straight_len"] + 2 * (R_OUT + 0.3)
    if not lo - 0.05 <= bb.YLength <= hi + 0.05:
        raise RuntimeError(f"track loop length {bb.YLength:.2f} outside "
                           f"{lo:.2f}..{hi:.2f}")
    if abs(bb.ZLength - P["track_width"]) > 1e-6:
        raise RuntimeError(f"track width {bb.ZLength:.2f} != {P['track_width']:.2f}")
    # The treads have to reach the tip radius on both straights, or the robot is
    # riding on its valleys and the pattern is decorative.
    for got, side in ((bb.XMax, "outer"), (-bb.XMin, "inner")):
        if not R_OUT - 0.05 <= got <= R_OUT + 0.3:
            raise RuntimeError(f"tread tips reach {got:.2f} on the {side} "
                               f"straight, not {R_OUT:.2f} (+0.3 chord allowance)")
    if P["track_band_t"] < 1.6:
        raise RuntimeError(f"continuous band only {P['track_band_t']:.2f} mm "
                           "after the tread relief")

    # --- the printed form is the same part, rolled up ---------------------
    # Two forms sharing one traversal function diverge one way: someone changes
    # a path the other never walks. Four things pin them together.
    pb = trk.BoundBox
    tip_d = 2 * (P["track_print_r"] + P["track_thickness"])
    val_d = 2 * (P["track_print_r"] + P["track_thickness"] - P["tread_depth"])
    if abs(pb.ZLength - P["track_width"]) > 1e-6:
        raise RuntimeError(f"printed loop width {pb.ZLength:.2f} != "
                           f"{P['track_width']:.2f}")
    # Across the tips where a chevron lands, across the valley where none does.
    # A stadium would read 332 x 94 here and fail on the first bound.
    for got, ax in ((pb.XLength, "X"), (pb.YLength, "Y")):
        if not val_d - 0.05 <= got <= tip_d + 0.6:
            raise RuntimeError(f"printed loop is {got:.2f} mm across {ax}, "
                               f"outside {val_d:.2f}..{tip_d:.2f} -- that is "
                               "not a circle of the right size")
    if max(pb.XLength, pb.YLength) > min(P["bed_x"], P["bed_y"]):
        raise RuntimeError(f"printed loop is {max(pb.XLength, pb.YLength):.1f} mm "
                           f"across, wider than the {min(P['bed_x'], P['bed_y']):.0f} mm bed")
    # A band of thickness t and inner path Lp has cross-section area
    # t * (Lp + pi * t) in ANY closed convex form, so the forms can only differ
    # by how the lug roots and tread pieces chord onto their own curves -- a
    # fraction of a percent, and less in the print form because its curves are
    # gentler. Anything larger means one form grew a feature the other did not.
    drift = abs(trk.Volume - trk_run.Volume) / trk_run.Volume
    if drift > 0.02:
        raise RuntimeError(f"printed and running loops differ by "
                           f"{100 * drift:.2f} % in volume -- the two forms "
                           "have diverged")

    loop = track_assembled(trk_run, 1)

    # --- the track must actually touch every wheel ------------------------
    # A tangency cannot be measured with a boolean: two solids that just touch
    # share zero volume, exactly like two solids 5 mm apart. So each wheel is
    # probed twice -- the nominal wheel must NOT intersect the band (no
    # interference) and its lands grown 0.3 mm on the radius MUST intersect it
    # (contact). Only a wheel sitting on the running surface passes both.
    seats = [("front idler", idl, P["idler_dia"], Y_IDLER, AXLE, 0.0)]
    for y in j5_params.roadwheel_ys(P):
        seats.append((f"road wheel y={y:+.0f}", rw, P["roadwheel_dia"], y,
                      RW_AXLE, 0.0))

    # The sprocket's teeth sit where the lugs are, so it only clears at the
    # right phase. Find that phase first, then hold it to the same two checks.
    n_steps = 24
    spin = None
    for k in range(n_steps):
        a = k * 360.0 / P["sprocket_teeth"] / n_steps
        if _place(spr, X_SPR, Y_REAR, AXLE, a).common(loop).Volume < 1e-6:
            spin = a
            break
    if spin is None:
        raise RuntimeError("no sprocket phase clears the lug row -- the pockets "
                           "do not line up with the lugs")
    seats.insert(0, ("drive sprocket", spr, P["sprocket_pitch_dia"], Y_REAR,
                     AXLE, spin))

    for name, shape, od, y, z, sp in seats:
        clash = _place(shape, X_SPR, y, z, sp).common(loop).Volume
        if clash > 1e-6:
            raise RuntimeError(f"{name} interferes with the track band by "
                               f"{clash:.1f} mm3 at ({y:+.1f}, {z:.1f})")
        probe = _place(_land_probe(od, 0.3), X_SPR, y, z)
        if probe.common(loop).Volume < 1e-6:
            raise RuntimeError(f"{name} does not reach the track: still clear "
                               f"at +0.3 mm on radius")

    # --- wheels must not foul each other ----------------------------------
    hubs = [(Y_REAR, AXLE, P["sprocket_pitch_dia"]), (Y_IDLER, AXLE, P["idler_dia"])]
    hubs += [(y, RW_AXLE, P["roadwheel_dia"]) for y in j5_params.roadwheel_ys(P)]
    for i in range(len(hubs)):
        for j in range(i + 1, len(hubs)):
            (y1, z1, d1), (y2, z2, d2) = hubs[i], hubs[j]
            gap = math.hypot(y1 - y2, z1 - z2) - (d1 + d2) / 2.0
            if gap < 1.0:
                raise RuntimeError(f"wheels at y={y1:+.1f} and y={y2:+.1f} are "
                                   f"{gap:.2f} mm apart on the rim")

    # --- nothing may foul the tread envelope ------------------------------
    # Built from the real chassis solid rather than from numbers: the lesson of
    # Session 03 is that the numbers agreed while the solids did not.
    try:
        import build_chassis as C
        tub_shape, deck_shape = C.build()
    except Exception as exc:                      # keeps this script standalone
        tub_shape = deck_shape = None
        print(f"drivetrain: chassis interference check SKIPPED ({exc})")

    if tub_shape is not None:
        for sgn in (-1, 1):
            env = L.box(P["track_width"], P["track_straight_len"] + 2 * R_OUT,
                        2 * R_OUT, sgn * P["track_cc"] / 2.0,
                        (Y_REAR + Y_IDLER) / 2.0, 0)
            for shp, nm in ((tub_shape, "tub"), (deck_shape, "deck")):
                clash = env.common(shp).Volume
                if clash > 1e-6:
                    side = "left" if sgn < 0 else "right"
                    raise RuntimeError(f"{nm} intrudes {clash:.1f} mm3 into the "
                                       f"{side} tread envelope")
        # every wheel against the real tub, including the new skirt pads: the
        # road wheels pass within 3 mm of them and the envelope check above
        # only covers x >= 61.
        for name, shape, y, z, sp in (("drive sprocket", spr, Y_REAR, AXLE, spin),
                                      ("front idler", idl, Y_IDLER, AXLE, 0.0)):
            clash = _place(shape, X_SPR, y, z, sp).common(tub_shape).Volume
            if clash > 1e-6:
                raise RuntimeError(f"{name} fouls the tub by {clash:.1f} mm3")
        for y in j5_params.roadwheel_ys(P):
            for sgn in (-1, 1):
                clash = _place(rw, sgn * X_SPR, y, RW_AXLE).common(tub_shape).Volume
                if clash > 1e-6:
                    raise RuntimeError(f"road wheel at y={y:+.0f} fouls the tub "
                                       f"(skirt) by {clash:.1f} mm3")
        gap = X_SPR - WID / 2.0 - X_WALL
        if gap < P["sprocket_collar_len"] - 0.4:
            raise RuntimeError(f"only {gap:.2f} mm between the tub wall and the "
                               f"sprocket face; the collar needs "
                               f"{P['sprocket_collar_len']:.1f} mm")

    # --- mass -------------------------------------------------------------
    pla = P["pla_density"] / 1000.0        # g/mm3
    tpu = 1.21 / 1000.0
    mass = (2 * spr.Volume * pla + 2 * idl.Volume * pla + 4 * rw.Volume * pla
            + 2 * car.Volume * pla + 6 * col.Volume * pla + 2 * trk.Volume * tpu)

    L.export(spr, os.path.join(STL, "drive_sprocket_v1.stl"))
    L.export(idl, os.path.join(STL, "front_idler_v1.stl"))
    L.export(rw, os.path.join(STL, "road_wheel_v1.stl"))
    L.export(car, os.path.join(STL, "idler_carrier_v1.stl"))
    L.export(col, os.path.join(STL, "axle_collar_v1.stl"))
    L.export(trk, os.path.join(STL, "track_loop_v1.stl"))

    for nm, shp in parts:
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "drivetrain_v1.FCStd"))

    print(f"drivetrain: lug pitch {P['track_lug_pitch']:.3f} x "
          f"{int(P['track_lug_count'])} = {P['track_inner_path']:.2f} mm inner path")
    print(f"drivetrain: straight run {P['track_straight_len']:.2f} mm, idler "
          f"nominal y {Y_IDLER:+.2f}, sprocket phase {spin:.1f} deg")
    print(f"drivetrain: loop prints as a circle r {P['track_print_r']:.2f} "
          f"({tip_d:.1f} mm across), running form {bb.YLength:.1f} x "
          f"{bb.XLength:.1f}; volumes differ {100 * drift:.2f} %")
    print(f"drivetrain: sprocket {spr.Volume * pla:5.1f} g   "
          f"idler {idl.Volume * pla:5.1f} g   road wheel {rw.Volume * pla:5.1f} g   "
          f"carrier {car.Volume * pla:5.1f} g   track {trk.Volume * tpu:5.1f} g")
    print(f"drivetrain: printed mass for the whole drivetrain {mass:.0f} g")


if __name__ == "__main__":
    main()
