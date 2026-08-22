"""Johnny 5 - head subassembly build script (Phase 00, Task 7).

Run headless:   freecadcmd build_head.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs:
    mechanical/stl/head_face_v1.stl
    mechanical/stl/head_back_v1.stl
    mechanical/stl/brow_blade_left_v1.stl
    mechanical/stl/brow_blade_right_v1.stl
    mechanical/stl/antenna_v1.stl
    mechanical/freecad/head_assembly_v1.FCStd

Wide film-accurate binocular head as a two-part keyed shell (face + back). The
face carries two brass-ring eye domes (WS2812B pixel behind a translucent pupil),
a central camera aperture in the bridge, and a mouth LED bar with the speaker
behind it. Two brow blades pivot OUTBOARD over the outer side of each eye and are
driven by the 6th bus servo through a gear bridge - pinion to the left blade gear
direct and to the right blade gear via one idler, so the blades mirror (roll-only,
3 poses). A nod gimbal at the base pivots on the neck nod servo; antenna on top.

Spur gears are modelled here as pitch-dia BLANKS with bores and centre distances
set; cut the teeth with the FreeCAD Gear workbench (module from params) or drop in
a printed library gear. Local frame: origin at head base centre, +Y forward.

NOTE: the eye/LED domes and the camera module are separate press-fit inserts.
"""

import math
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

HW = P["head_w"]
HD = P["head_depth"]
HH = P["head_h"]
WALL = P["head_wall"]
YF = HD / 2.0                      # front face plane
EYE_Z = HH * 0.62
CAM_Z = HH * 0.49
MOUTH_Z = HH * 0.27
PIV_X = P["brow_pivot_offset"]
PIV_Z = P["brow_pivot_z"]
BURY = 1.5                         # how far an internal boss sits into the wall


def _inner_boss(r, depth, x, z, bury=BURY):
    """Boss on the inside of the face, rooted `bury` mm into the wall.

    Everything internal here used to stop flush with the inner surface, or
    short of it. Flush survives only because the head's walls happen to be flat
    -- a coplanar face fuses -- and short does not survive at all: the brow
    idler gear boss stopped 2 mm shy and shipped as a floating island in the
    Session 02 STL. Overlapping by a real volume works either way.
    """
    return L.cyl(r, depth + bury, x, YF - WALL - depth, z, axis="y")


def shell():
    outer = L.box(HW, HD, HH, 0, 0, 0)
    inner = L.box(HW - 2 * WALL, HD - 2 * WALL, HH - 2 * WALL, 0, 0, WALL)
    return outer.cut(inner)


def eyes():
    solids, cuts = [], []
    for sgn in (-1, 1):
        x = sgn * P["eye_spacing"] / 2.0
        # brass-ring lens housing protruding from the face
        solids.append(L.cyl(P["eye_dia"] / 2.0 + 2, 8, x, YF - 2, EYE_Z, axis="y"))
        # eye dome / LED bore through the face
        cuts.append(L.cyl(P["eye_dia"] / 2.0, WALL + 14, x, YF - WALL - 8, EYE_Z, axis="y"))
    return solids, cuts


def camera():
    cuts = [L.cyl(P["cam_aperture"] / 2.0, WALL + 6, 0, YF - WALL - 3, CAM_Z, axis="y")]
    # internal camera-board mount bosses (M2)
    solids = []
    for dx in (-12.5, 12.5):
        boss = _inner_boss(3.0, 6, dx, CAM_Z)
        bore = L.cyl(P["m2_tap_dia"] / 2.0, 6.5, dx, YF - WALL - 6.5, CAM_Z,
                     axis="y")
        solids.append(boss.cut(bore))
    return solids, cuts


def mouth():
    cuts = [L.box(P["mouth_w"], WALL + 4, P["mouth_h"], 0, YF - WALL / 2, MOUTH_Z)]
    solids = []
    # LED-bar pocket + speaker pocket behind the mouth
    led = L.box(P["mouth_w"] + 6, 5.0, P["mouth_h"] + 6, 0,
                YF - WALL + 1.0 - 2.5, MOUTH_Z)
    spk = L.cyl(15, 6, 0, YF - WALL - 12, MOUTH_Z + P["mouth_h"] / 2, axis="y")
    solids += [led]
    # speaker grille holes
    for dx in (-8, 0, 8):
        cuts.append(L.cyl(2.0, WALL + 2, dx, YF - WALL, MOUTH_Z - 10, axis="y"))
    cuts.append(spk)
    return solids, cuts


def brow_mounts():
    """Pivot bearings, brow servo pocket, and gear-centre bosses (blanks)."""
    solids, cuts = [], []
    # outboard pivot bearings (blade gear axis), through the top front
    for sgn in (-1, 1):
        x = sgn * PIV_X
        solids.append(_inner_boss(P["brow_gear_pitch_dia"] / 2.0 + 3, 6, x, PIV_Z))
        cuts.append(L.cyl(2.1, WALL + 10, x, YF - WALL - 8, PIV_Z, axis="y"))   # pivot shaft bore
    # central brow servo pocket (SCS0009, output toward the gear train on +Y)
    cuts.append(L.box(P["scs_body_l"], P["scs_body_h"], P["scs_body_w"], 0, YF - WALL - P["scs_body_h"] / 2 - 4, PIV_Z))
    # gear-centre bosses: pinion (centre) + idler (offset) — blanks
    # 4 mm long from 6 mm out: it stopped 2 mm short of the wall and floated.
    solids.append(_inner_boss(P["brow_idler_pitch_dia"] / 2.0, 6,
                              P["brow_pivot_offset"] * 0.45, PIV_Z))
    return solids, cuts


def nod_gimbal():
    """Two ears at the head base that pivot on the neck nod-servo output (axis X)."""
    solids, cuts = [], []
    for sgn in (-1, 1):
        solids.append(L.box(6, 20, 24, sgn * 14, 0, -6))
    # bore the nod pivot axis (lateral X) through both ears, just below the base
    cuts.append(L.cyl((P["scs_shaft_dia"] + 0.6) / 2.0, 40, -20, 0, 6, axis="x"))
    return solids, cuts


def antenna_boss():
    return L.cyl(P["antenna_dia"] / 2.0 + 2.5, 6, 0, 0, HH - 2)


PIN_Z = (HH * 0.3, HH * 0.8)
PIN_PAD = 7.0                      # pad depth inboard of the side wall
PIN_X = HW / 2.0 - WALL - PIN_PAD / 2.0


def split_pads():
    """Pads on the inner side walls, straddling y=0, for the registration pins.

    The split plane cuts a hollow shell, so the only material on that face is
    two 2 mm side-wall strips -- nothing a ø4 pin can root in. The pins sat at
    x = +/-67, which is 6 mm inboard of a wall that starts at 73: free air, and
    moving them along y did not change that. Same defect as the torso's, and
    the same fix -- a pad straddling the split so each half keeps its share.
    """
    return [L.box(PIN_PAD, 12.0, 10.0, sgn * PIN_X, 0, zc - 5.0)
            for zc in PIN_Z for sgn in (-1, 1)]


def half(solid, front):
    big = L.box(HW + 40, 1000, HH + 80, 0, (500 if front else -500), -40)
    h = solid.common(big)
    for zc in PIN_Z:
        for sgn in (-1, 1):
            x = sgn * PIN_X
            if front:
                h = h.cut(L.cyl(2.3, 8, x, -4, zc, axis="y"))
            else:
                # Rooted 2 mm inside the back half's pad.
                h = h.fuse(L.cyl(2.0, 6, x, -2, zc, axis="y"))
    return h


def brow_blade(side):
    """One brow blade with a geared hub at its outboard pivot end."""
    bl, bw, bt = P["brow_blade_len"], P["brow_blade_w"], P["brow_blade_t"]
    blade = L.box(bl, bt, bw, bl / 2.0, 0, -bw / 2.0)        # extends +X from the hub
    # geared hub blank at the pivot end (teeth cut later via the Gear workbench)
    solid = blade.fuse(L.cyl(P["brow_gear_pitch_dia"] / 2.0 + 1, bt + 2, 0, -1, 0, axis="y"))
    solid = solid.cut(L.cyl(2.0, bt + 6, 0, -3, 0, axis="y"))   # pivot bore
    if side < 0:
        solid = solid.mirror(Vector(0, 0, 0), Vector(1, 0, 0))
    return solid


def antenna_rod():
    rod = L.cyl(P["antenna_dia"] / 2.0, P["antenna_h"], 0, 0, 0)
    rod = rod.fuse(L.cyl(P["antenna_dia"] / 2.0 + 2, 3, 0, 0, P["antenna_h"] - 3))
    return rod


def build():
    body = shell()
    for grp in (eyes, camera, mouth, brow_mounts, nod_gimbal):
        s, c = grp()
        for x in s:
            body = body.fuse(x)
        for x in c:
            body = body.cut(x)
    body = body.fuse(antenna_boss())
    for pad in split_pads():
        body = body.fuse(pad)
    return half(body, True), half(body, False)


def main():
    doc = App.newDocument("head_assembly_v1")
    face, back = build()

    # Every printed part here must be exactly one solid. Session 02 shipped the
    # face as 2 and the back as 5: the brow idler boss and the four split-key
    # pins had never fused to the shell, and an island slices as an island in
    # mid-air rather than failing loudly.
    for shp, nm in ((face, "head face"), (back, "head back"),
                    (brow_blade(+1), "brow blade"), (antenna_rod(), "antenna")):
        n = len(shp.Solids)
        if n != 1:
            raise RuntimeError(f"{nm} built as {n} solids -- something is not "
                               "fused to the shell; refusing to export")
    bl = brow_blade(+1)
    br = brow_blade(-1)
    ant = antenna_rod()
    exports = [(face, "head_face"), (back, "head_back"),
               (bl, "brow_blade_left"), (br, "brow_blade_right"), (ant, "antenna")]
    for shp, nm in exports:
        L.export(shp, os.path.join(STL, nm + "_v1.stl"))
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "head_assembly_v1.FCStd"))
    print("head face bbox", face.BoundBox)


if __name__ == "__main__":
    main()
