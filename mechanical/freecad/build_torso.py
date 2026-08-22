"""Johnny 5 - torso subassembly build script (Phase 00, Task 7).

Run headless:   freecadcmd build_torso.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs:
    mechanical/stl/torso_front_v1.stl
    mechanical/stl/torso_back_v1.stl
    mechanical/freecad/torso_assembly_v1.FCStd

A tapered boxy shell on the chassis deck, split front/back on the Y=0 plane for
wiring access and support-free printing, keyed with registration pins and joined
with M3 screws. Carries: 2 shoulder-pitch servos (shaft along X), a left-shoulder
utility-tilt servo, a top neck riser holding the head-yaw servo (shaft along Z),
Pi-V on the inner back wall, deck bolt interface, and a central cable path.

Frame: origin at footprint centre on the ground. +X right, +Y forward, +Z up.
"""

import os
import FreeCAD as App
import Part
from FreeCAD import Vector

import j5_lib as L
import j5_params

P = j5_params.get()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STL = os.path.join(REPO, "mechanical", "stl")
os.makedirs(STL, exist_ok=True)

# --- key dims ------------------------------------------------------------
Z0 = P["deck_top"]
TH = P["torso_h"]
ZT = P["torso_top"]
WB = P["torso_w_base"]
WT = P["torso_w_top"]
D = P["torso_depth"]
WALL = P["torso_wall"]
LEAN = P["torso_lean"]
SH_Z = P["shoulder_z"]


def width_at(z):
    """Torso X-width at absolute height z (linear taper base->top)."""
    f = (z - Z0) / TH
    return WB + (WT - WB) * f


def lean_at(z):
    return LEAN * (z - Z0) / TH


def inner_w_at(z):
    """Inner-surface X-width at z. The inner loft runs Z0-1 to ZT+1, so it is
    NOT width_at(z) - 2*WALL; deriving it separately is what lets features be
    placed against the real surface instead of an approximation of it."""
    f = (z - (Z0 - 1.0)) / (TH + 2.0)
    return (WB - 2 * WALL) + ((WT - 2 * WALL) - (WB - 2 * WALL)) * f


def inner_lean_at(z):
    return LEAN * (z - (Z0 - 1.0)) / (TH + 2.0)


def rect_wire(w, d, z, yshift):
    p = [Vector(-w / 2, -d / 2 + yshift, z), Vector(w / 2, -d / 2 + yshift, z),
         Vector(w / 2, d / 2 + yshift, z), Vector(-w / 2, d / 2 + yshift, z)]
    p.append(p[0])
    return Part.makePolygon(p)


# --- shell ---------------------------------------------------------------
def shell():
    outer = Part.makeLoft([rect_wire(WB, D, Z0, 0),
                           rect_wire(WT, D, ZT, LEAN)], True)
    inner = Part.makeLoft([rect_wire(WB - 2 * WALL, D - 2 * WALL, Z0 - 1, 0),
                           rect_wire(WT - 2 * WALL, D - 2 * WALL, ZT + 1, LEAN)], True)
    return outer.cut(inner)


# --- deck bolt interface (4x M3 down into deck heat-sets) ----------------
def deck_bolts():
    """Four M3 bosses down into the deck heat-sets, each ribbed to a wall.

    Without the rib the boss is a column standing in the middle of a hollow
    shell touching nothing at all: it fuses into no solid, and slices as an
    island in mid-air. Ribbing to the nearest wall in Y rather than in X also
    keeps each boss in the same half as the wall it holds onto, so the front/back
    split does not orphan it again.
    """
    solids, cuts = [], []
    h = 10.0
    for dx in (-P["torso_iface_dx"] / 2, P["torso_iface_dx"] / 2):
        for dy in (-P["torso_iface_dy"] / 2, P["torso_iface_dy"] / 2):
            b, _ = L.screw_boss(dx, dy, Z0, h, P["boss_od"] + 1, 0)
            solids.append(b)
            y_wall = (inner_lean_at(Z0 + h / 2.0)
                      + (1.0 if dy > 0 else -1.0) * (D / 2.0 - WALL))
            solids.append(L.box(5.0, abs(y_wall - dy) + 2.0, h, dx,
                                (y_wall + dy) / 2.0, Z0))
            cuts.append(L.cyl(3.4 / 2.0, 14, dx, dy, Z0 - 1))     # M3 clearance
    return solids, cuts


# --- shoulder servo features (both sides, shaft along X) -----------------
def shoulders():
    """Shoulder-pitch servo features, both sides.

    Two bugs lived here. L.cyl only ever extrudes +X, so every `xface - sgn*n`
    start point was correct on the right and wrong on the left: the left shaft
    hole and horn recess began inboard of the wall and ran further inboard,
    cutting nothing, so the left arm servo had no way through the shell at all.
    Same defect that lost the tub's right-hand wall holes in Session 03, mirrored.

    And the mount bosses ended flush with the inner surface. That surface is
    lofted and tapered, so a flat boss face meets it along a line rather than
    over an area and the fuse leaves the boss floating. They are buried 1.5 mm
    into the wall now, which is a volume overlap and cannot half-fuse.
    """
    solids, cuts = [], []
    xface = width_at(SH_Z) / 2.0
    ysh = lean_at(SH_Z)
    for sgn in (-1, 1):
        xf = sgn * xface
        cuts.append(L.cyl((P["scs_shaft_dia"] + 2) / 2.0, WALL + 6,
                          min(xf - sgn * (WALL + 3), xf + sgn * 3.0),
                          ysh, SH_Z, axis="x"))
        cuts.append(L.cyl(P["scs_horn_dia"] / 2.0 + 1, 3,
                          min(xf - sgn * 1.5, xf + sgn * 1.5),
                          ysh, SH_Z, axis="x"))
        for dz in (-P["scs_screw_cc"] / 2, P["scs_screw_cc"] / 2):
            zb = SH_Z + dz
            xin = sgn * inner_w_at(zb) / 2.0
            yb = inner_lean_at(zb)
            boss = L.cyl(P["boss_od"] / 2.0, 6.5,
                         min(xin - sgn * 5.0, xin + sgn * 1.5), yb, zb, axis="x")
            bore = L.cyl(P["m2_tap_dia"] / 2.0, 5.0,
                         min(xin, xin - sgn * 5.0), yb, zb, axis="x")
            solids.append(boss.cut(bore))
    return solids, cuts


# --- left-shoulder utility-tilt servo pad --------------------------------
def utility_pad():
    wsh = width_at(SH_Z + 25)
    x = -wsh / 2
    pad = L.box(P["scs_body_l"] + 6, P["scs_body_w"] + 6, 4, x + 6, lean_at(SH_Z + 25),
                SH_Z + 25)
    cut = L.box(P["scs_body_l"], P["scs_body_w"], 6, x + 6, lean_at(SH_Z + 25), SH_Z + 24)
    return [pad], [cut]


# --- neck riser + head-yaw servo (shaft along Z) -------------------------
def shoulder_deck():
    """Top plate closing the torso, and the thing the neck riser stands on.

    The riser used to start at ZT, the top of the shell -- which is open, so it
    sat over a hole with its whole ø34 footprint in mid-air and fused to
    nothing. That is not a detail: the head, the nod servo and the yaw servo all
    hang off it. A plate is the right answer rather than ribs because it also
    closes the box against dust and ties the two shoulders together in shear.
    Windowed down to 14 g.
    """
    t = P["torso_wall"]
    z0 = ZT - t
    # Oversized by 1.5 mm all round so it bites into the walls. Sized to the
    # cavity exactly, the plate's vertical sides and the lofted taper agree to
    # within 0.04 mm over the plate thickness -- overlapping on one side of that
    # and gapping on the other. OCC will grind for minutes on slivers like that
    # and the result is not a reliable weld either way.
    # 0.6 mm of bite per side: enough to be an unambiguous volume overlap, an
    # order of magnitude above the 0.04 mm sliver, and it still leaves 1.35 mm
    # of skin outboard of the plate. At 1.5 mm of bite that skin was 0.46 mm.
    w = inner_w_at(z0) + 1.2
    d = (D - 2 * WALL) + 1.2
    cy = inner_lean_at(z0 + t / 2.0)
    plate = L.box(w, d, t, 0, cy, z0)
    cuts = [L.cyl(12.0, t + 2, 0, cy, z0 - 1)]          # cable + yaw servo pass
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(L.cyl(12.5, t + 2, sx * ((w - 1.2) / 4.0 + 6.0),
                              cy + sy * ((d - 1.2) / 4.0 + 4.0), z0 - 1))
    return [plate], cuts


def neck():
    t = P["torso_wall"]
    riser = L.cyl(P["neck_dia"] / 2.0, P["neck_h"] + t, 0, lean_at(ZT), ZT - t)
    cuts = []
    # vertical servo pocket (head-yaw SCS0009)
    cuts.append(L.box(P["scs_body_l"], P["scs_body_w"], P["scs_body_h"] + 2,
                      0, lean_at(ZT), ZT + P["neck_h"] - P["scs_body_h"]))
    # output shaft hole through the riser top
    cuts.append(L.cyl((P["scs_shaft_dia"] + 2) / 2.0, P["neck_h"] + 2,
                      0, lean_at(ZT), ZT - 1))
    return [riser], cuts


# --- Pi-V standoffs on inner back wall (board in XZ plane) ----------------
def piV():
    """Pi-V standoffs on the inner back wall.

    The back wall leans, so its inner surface moves 6 mm in Y over the torso
    height; anchoring all four standoffs to one constant y_wall put the upper
    pair through the outer skin and the lower pair short of it. Each one is now
    placed against the wall at its own height and buried 1.5 mm into it.
    """
    h = P["piV_standoff_h"]
    zc = Z0 + 70
    stand = []
    for dz in (-P["pi_hole_dx"] / 2, P["pi_hole_dx"] / 2):       # 58 along Z
        for dx in (-P["pi_hole_dy"] / 2, P["pi_hole_dy"] / 2):   # 23 along X
            z = zc + dz
            y_in = inner_lean_at(z) - (D / 2.0 - WALL)
            base = L.cyl(P["boss_od"] / 2.0, h + 1.5, dx, y_in - 1.5, z, axis="y")
            bore = L.cyl(P["m25_tap_dia"] / 2.0, h + 0.5, dx, y_in - 0.5, z,
                         axis="y")
            stand.append(base.cut(bore))
    return stand


# --- side-wall lightening: withdrawn -------------------------------------
def lightening():
    """Deliberately empty. What was here cut a ø2.8 x 26 mm rod, not a pocket:
    on the right it punched a through-hole in the side wall, on the left it
    bored inward from just under the skin. Neither was the intent, and a blind
    pocket cannot be made to work against a tapered face -- over a 26 mm tall
    pocket the surface moves 1.1 mm, so a 1.0 mm floor becomes 0.45 mm at one
    end. The wall going 2.4 -> 2.0 mm saves far more than this ever did.
    """
    return []


# --- split joinery (cut shared holes, then halve) ------------------------
def split_holes():
    """Horizontal M3 holes through both halves, near the four vertical edges."""
    cuts = []
    for zc in (Z0 + 18, ZT - 18):
        wsh = width_at(zc)
        for sgn in (-1, 1):
            cuts.append(L.cyl(3.4 / 2.0, D + 4, sgn * (wsh / 2 - 5), -D / 2 - 2, zc, axis="y"))
    return cuts


PIN_Z = (Z0 + 40, ZT - 60)          # clear of the shoulder bosses at SH_Z +/- 9
PIN_PAD = 7.0                       # pad depth inboard of the side wall


def _pin_x(zc, sgn):
    """Pin centre: mid-thickness of the pad, not somewhere in mid-air."""
    return sgn * (inner_w_at(zc) / 2.0 - PIN_PAD / 2.0)


def split_pads():
    """Pads on the inner side walls, straddling y=0, for the registration pins.

    The split plane cuts a hollow shell, so the only material anywhere on that
    face is two 2 mm side-wall strips -- there is nothing for a ø4 pin to root
    in. The pins were placed 12 mm inboard of the outer face, which is neither
    the wall nor anything else: they were in free air, and moving them along y
    did not change that. Each station gets a pad thick enough to hold a pin,
    and because the pad straddles the split each half keeps its own share of it.
    """
    solids = []
    for zc in PIN_Z:
        xin = inner_w_at(zc) / 2.0
        for sgn in (-1, 1):
            solids.append(L.box(PIN_PAD, 12.0, 10.0,
                                sgn * (xin - PIN_PAD / 2.0), 0, zc - 5.0))
    return solids


def key_pins(front):
    """Registration pins on the back half (front=False) / holes on the front."""
    feats = []
    for zc in PIN_Z:
        for sgn in (-1, 1):
            x = _pin_x(zc, sgn)
            if front:
                feats.append(("cut", L.cyl(2.3, 8, x, -4, zc, axis="y")))
            else:
                # Rooted 2 mm inside the back half's pad. Starting at y=0 put
                # the whole pin in the front half's space, touching its own half
                # only on the split plane.
                feats.append(("add", L.cyl(2.0, 6, x, -2, zc, axis="y")))
    return feats


def half(solid, front):
    big = L.box(400, 1000, 700, 0, (500 if front else -500), Z0 - 60)
    h = solid.common(big)
    for kind, feat in key_pins(front):
        h = h.fuse(feat) if kind == "add" else h.cut(feat)
    return h


# --- assemble ------------------------------------------------------------
def build():
    body = shell()

    for grp in (deck_bolts, shoulders, utility_pad, shoulder_deck, neck):
        s, c = grp()
        for x in s:
            body = body.fuse(x)
        for x in c:
            body = body.cut(x)

    for st in piV() + split_pads():
        body = body.fuse(st)

    for c in lightening() + split_holes():
        body = body.cut(c)

    front = half(body, True)
    back = half(body, False)
    return front, back


def main():
    doc = App.newDocument("torso_assembly_v1")
    front, back = build()

    # Each half must come out as exactly one solid. Session 02 exported these
    # as 7- and 8-solid compounds: bosses, pins and the neck riser that had
    # never fused to anything. An island slices as an island in mid-air rather
    # than failing loudly, so it has to be caught here.
    for shp, nm in ((front, "torso front"), (back, "torso back")):
        n = len(shp.Solids)
        if n != 1:
            raise RuntimeError(f"{nm} built as {n} solids -- something is not "
                               "fused to the shell; refusing to export")
    L.export(front, os.path.join(STL, "torso_front_v1.stl"))
    L.export(back, os.path.join(STL, "torso_back_v1.stl"))
    for shp, nm in ((front, "torso_front"), (back, "torso_back")):
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "torso_assembly_v1.FCStd"))
    print("torso front bbox", front.BoundBox)
    print("torso back  bbox", back.BoundBox)


if __name__ == "__main__":
    main()
