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
    solids, cuts = [], []
    for dx in (-P["torso_iface_dx"] / 2, P["torso_iface_dx"] / 2):
        for dy in (-P["torso_iface_dy"] / 2, P["torso_iface_dy"] / 2):
            b, _ = L.screw_boss(dx, dy, Z0, 10, P["boss_od"] + 1, 0)
            solids.append(b)
            cuts.append(L.cyl(3.4 / 2.0, 14, dx, dy, Z0 - 1))     # M3 clearance
    return solids, cuts


# --- shoulder servo features (both sides, shaft along X) -----------------
def shoulders():
    solids, cuts = [], []
    wsh = width_at(SH_Z)
    ysh = lean_at(SH_Z)
    for sgn in (-1, 1):
        xface = sgn * wsh / 2
        # shaft hole through the side wall
        cuts.append(L.cyl((P["scs_shaft_dia"] + 2) / 2.0, WALL + 6,
                          xface - sgn * (WALL + 3), ysh, SH_Z, axis="x"))
        # external horn clearance recess
        cuts.append(L.cyl(P["scs_horn_dia"] / 2.0 + 1, 3,
                          xface - sgn * 1.5, ysh, SH_Z, axis="x"))
        # internal servo-mount bosses flanking the shaft (M2 tapped)
        for dz in (-P["scs_screw_cc"] / 2, P["scs_screw_cc"] / 2):
            boss = L.cyl(P["boss_od"] / 2.0, 5, xface - sgn * (WALL + 5),
                         ysh, SH_Z + dz, axis="x")
            bore = L.cyl(P["m2_tap_dia"] / 2.0, 6, xface - sgn * (WALL + 5.5),
                         ysh, SH_Z + dz, axis="x")
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
def neck():
    riser = L.cyl(P["neck_dia"] / 2.0, P["neck_h"], 0, lean_at(ZT), ZT)
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
    y_wall = -D / 2 + WALL
    zc = Z0 + 70
    stand = []
    for dz in (-P["pi_hole_dx"] / 2, P["pi_hole_dx"] / 2):       # 58 along Z
        for dx in (-P["pi_hole_dy"] / 2, P["pi_hole_dy"] / 2):   # 23 along X
            base = L.cyl(P["boss_od"] / 2.0, P["piV_standoff_h"], dx,
                         y_wall, zc + dz, axis="y")
            bore = L.cyl(P["m25_tap_dia"] / 2.0, P["piV_standoff_h"] + 1, dx,
                         y_wall - 0.5, zc + dz, axis="y")
            stand.append(base.cut(bore))
    return stand


# --- lightening pockets on side walls ------------------------------------
def lightening():
    cuts = []
    for sgn in (-1, 1):
        for zc in (Z0 + 45, Z0 + 110):
            wsh = width_at(zc)
            cuts.append(L.cyl((WALL - 1.0), 26, sgn * (wsh / 2 - (WALL - 1) / 2 - 0.05),
                              lean_at(zc), zc, axis="x"))
    return cuts


# --- split joinery (cut shared holes, then halve) ------------------------
def split_holes():
    """Horizontal M3 holes through both halves, near the four vertical edges."""
    cuts = []
    for zc in (Z0 + 18, ZT - 18):
        wsh = width_at(zc)
        for sgn in (-1, 1):
            cuts.append(L.cyl(3.4 / 2.0, D + 4, sgn * (wsh / 2 - 5), -D / 2 - 2, zc, axis="y"))
    return cuts


def key_pins(front):
    """Registration pins on the back half (front=False) / holes on the front."""
    feats = []
    for zc in (Z0 + 40, ZT - 40):
        wsh = width_at(zc)
        for sgn in (-1, 1):
            x = sgn * (wsh / 2 - 12)
            if front:
                feats.append(("cut", L.cyl(2.3, 8, x, -4, zc, axis="y")))
            else:
                feats.append(("add", L.cyl(2.0, 6, x, 0, zc, axis="y")))
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

    for grp in (deck_bolts, shoulders, utility_pad, neck):
        s, c = grp()
        for x in s:
            body = body.fuse(x)
        for x in c:
            body = body.cut(x)

    for st in piV():
        body = body.fuse(st)

    body = body.fuse(neck()[0][0])  # ensure riser welded

    for c in lightening() + split_holes():
        body = body.cut(c)

    front = half(body, True)
    back = half(body, False)
    return front, back


def main():
    doc = App.newDocument("torso_assembly_v1")
    front, back = build()
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
