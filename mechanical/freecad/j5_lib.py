"""FreeCAD Part-scripting helpers shared across Johnny 5 build scripts.

Kept to the stable Part API (makeBox / makeCylinder / boolean ops) so the
scripts run unchanged on FreeCAD 0.20 through 1.1. Import only inside a FreeCAD
Python context (freecadcmd or the FreeCAD GUI console).

Conventions:
  - World origin at the centre of the track footprint, on the ground plane.
  - +X right, +Y forward (robot fore-aft), +Z up.
"""

import Part
from FreeCAD import Vector


# ---- primitives ---------------------------------------------------------

def box(l, w, h, cx=0.0, cy=0.0, z0=0.0):
    """Axis-aligned box, centred in X/Y on (cx, cy), bottom face at z0."""
    return Part.makeBox(l, w, h, Vector(cx - l / 2.0, cy - w / 2.0, z0))


def tube_shell(l, w, h, wall, z0=0.0, cx=0.0, cy=0.0, open_top=True):
    """Open-bottom-less tub: outer box minus inner cavity. open_top removes the lid."""
    outer = box(l, w, h, cx, cy, z0)
    top_gap = wall if not open_top else 0.0
    inner = box(l - 2 * wall, w - 2 * wall, h - wall - top_gap, cx, cy, z0 + wall)
    return outer.cut(inner)


def cyl(r, h, x=0.0, y=0.0, z=0.0, axis="z"):
    """Cylinder of radius r, length h, base at (x,y,z), along the given axis."""
    d = {"x": Vector(1, 0, 0), "y": Vector(0, 1, 0), "z": Vector(0, 0, 1)}[axis]
    return Part.makeCylinder(r, h, Vector(x, y, z), d)


def screw_boss(x, y, z0, h, od, bore):
    """Solid boss with a centred pilot bore (returns (boss_solid, bore_solid))."""
    boss = cyl(od / 2.0, h, x, y, z0)
    hole = cyl(bore / 2.0, h + 0.2, x, y, z0 - 0.1)
    return boss, hole


def standoff(x, y, z0, h, od, bore):
    """Standoff = boss already drilled (single solid). Use for Pi/board mounts."""
    boss, hole = screw_boss(x, y, z0, h, od, bore)
    return boss.cut(hole)


def lightening_pocket(l, w, depth, cx, cy, z_top):
    """A blind pocket solid to subtract from a wall/floor for weight relief."""
    return box(l, w, depth + 0.1, cx, cy, z_top - depth)


def key_rib(l, p):
    """Male alignment key rib (for split joints higher in the stack)."""
    return box(l, p["key_w"], p["key_h"])


def key_slot(l, p):
    """Female slot matching key_rib with slip-fit clearance."""
    c = p["key_clear"]
    return box(l + c, p["key_w"] + c, p["key_h"] + c)


# ---- export -------------------------------------------------------------

def export(shape, stl_path, fcstd_path=None, doc=None, name="part"):
    """Mesh-export a shape to STL (headless-safe) and optionally save the FCStd."""
    shape.exportStl(stl_path)
    if fcstd_path is not None and doc is not None:
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        doc.recompute()
        doc.saveAs(fcstd_path)
    return stl_path
