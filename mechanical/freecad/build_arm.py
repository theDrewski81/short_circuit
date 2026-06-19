"""Johnny 5 - arm subassembly build script (Phase 00, Task 7).

Run headless:   freecadcmd build_arm.py
or paste into the FreeCAD 1.1.1 Python console.

Outputs:
    mechanical/stl/arm_right_v1.stl
    mechanical/stl/arm_left_v1.stl
    mechanical/freecad/arm_assembly_v1.FCStd

A mirrored pair of single-DOF limbs that bolt to the shoulder-servo horns:
horn hub -> upper arm -> fixed elbow bend -> forearm -> static 3-finger claw.
Hollow thin-wall PLA inside the <=50 g / <=90 mm-lever budget. Grip-ready for the
V2 tendon claw: a reserved tendon channel runs the limb to an anchor boss at the
palm, with the cable entry near the shoulder axis so arm pitch does not tension it.

Local print frame: origin at the horn face, hub axis along -X (toward the servo),
limb hanging -Z and bending +Y (forward). Right arm is built; left is mirrored.
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

S = P["arm_section"]
UA = P["upper_arm_len"]
FA = P["forearm_len"]
EA = P["elbow_angle"]
WALL = P["arm_wall"]
TCH = P["tendon_channel_dia"]
BLK = S + 4                       # shoulder block size
Z_BLK = -BLK                      # block bottom z (top at 0)
Z_ELBOW = Z_BLK - UA             # elbow point


def hollow(box_solid, l, w, h, cx, cy, z0):
    """Subtract an inner cavity to keep the limb light."""
    inner = L.box(l - 2 * WALL, w - 2 * WALL, h - 2 * WALL, cx, cy, z0 + WALL)
    return box_solid.cut(inner)


def forearm_assembly():
    """Forearm + claw built at origin extending -Z (before elbow transform)."""
    fa = L.box(S, S, FA, 0, 0, -FA)
    fa = hollow(fa, S, S, FA, 0, 0, -FA)
    solid = fa

    # palm
    palm = L.box(S + 2, S + 2, 8, 0, 0, -FA - 8)
    solid = solid.fuse(palm)

    # three static fingers (centre straight, outer two splayed)
    cl = P["claw_len"]
    cf = P["claw_finger"]
    centre = L.box(cf, cf, cl, 0, 0, -FA - 8 - cl)
    solid = solid.fuse(centre)
    for sgn in (-1, 1):
        f = L.box(cf, cf, cl, sgn * 5, 0, -FA - 8 - cl)
        f.rotate(Vector(sgn * 5, 0, -FA - 8), Vector(1, 0, 0), 0)
        f.rotate(Vector(sgn * 5, 0, -FA - 8), Vector(0, 1, 0), sgn * 12)
        solid = solid.fuse(f)

    # tendon anchor boss at palm + channel down the forearm
    anchor = L.cyl(3.0, 5, 0, 0, -FA - 5)
    solid = solid.fuse(anchor)
    chan = L.cyl(TCH / 2.0, FA + 6, 0, 0, -FA - 5)
    solid = solid.cut(chan)
    return solid


def right_arm():
    # shoulder block
    solid = L.box(BLK, BLK - 2, BLK, 0, 0, Z_BLK)
    solid = hollow(solid, BLK, BLK - 2, BLK, 0, 0, Z_BLK)

    # horn hub on the -X face
    hub = L.cyl(P["horn_hub_dia"] / 2.0, 5, -BLK / 2 - 5, 0, -BLK / 2, axis="x")
    solid = solid.fuse(hub)

    # upper arm
    ua = L.box(S, S, UA, 0, 0, Z_ELBOW)
    ua = hollow(ua, S, S, UA, 0, 0, Z_ELBOW)
    solid = solid.fuse(ua)

    # forearm + claw, rotated by the fixed elbow bend, moved to the elbow
    fwd = forearm_assembly()
    fwd.rotate(Vector(0, 0, 0), Vector(1, 0, 0), -EA)
    fwd.translate(Vector(0, 0, Z_ELBOW))
    solid = solid.fuse(fwd)

    # --- cuts ---
    # horn spline bore + 4 mounting screw holes
    solid = solid.cut(L.cyl((P["scs_shaft_dia"] + 0.6) / 2.0, BLK + 12, -BLK / 2 - 6, 0, -BLK / 2, axis="x"))
    import math
    for i in range(4):
        a = math.radians(45 + 90 * i)
        solid = solid.cut(L.cyl(1.1, BLK + 12, -BLK / 2 - 6,
                                6 * math.cos(a), -BLK / 2 + 6 * math.sin(a), axis="x"))
    # tendon channel down the upper arm (cable entry near the shoulder axis)
    solid = solid.cut(L.cyl(TCH / 2.0, UA + BLK, 0, 0, Z_ELBOW + 2))
    return solid


def build():
    right = right_arm()
    left = right.mirror(Vector(0, 0, 0), Vector(1, 0, 0))
    return right, left


def main():
    doc = App.newDocument("arm_assembly_v1")
    right, left = build()
    L.export(right, os.path.join(STL, "arm_right_v1.stl"))
    L.export(left, os.path.join(STL, "arm_left_v1.stl"))
    for shp, nm in ((right, "arm_right"), (left, "arm_left")):
        o = doc.addObject("Part::Feature", nm)
        o.Shape = shp
    doc.recompute()
    doc.saveAs(os.path.join(HERE, "arm_assembly_v1.FCStd"))
    print("arm right bbox", right.BoundBox)


if __name__ == "__main__":
    main()
