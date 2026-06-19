# Johnny 5 — Mechanical (FreeCAD, parametric)

All body geometry is generated from a single parameter sheet by headless Python
build scripts. Nothing is modelled by hand in the GUI.

```
mechanical/
  freecad/
    params.csv            single source of truth (locked + design dims)
    j5_params.py          CSV loader + derived geometry (no FreeCAD dependency)
    j5_lib.py             Part-scripting helpers (boxes, bosses, keyed splits, export)
    build_chassis.py      chassis / tread base build  → STL + FCStd
    chassis_assembly_v1.FCStd   (generated)
  stl/                    generated STL exports for printing
  preview/
    validate.py           FreeCAD-free param checks (bed fit, clearance, packaging, mass)
    preview_chassis.py    matplotlib massing preview → PNG
    chassis_massing_v1.png
```

## Generate the chassis

```
cd mechanical/freecad
freecadcmd build_chassis.py          # FreeCAD 1.1.1; writes STLs to ../stl and the FCStd here
```

(or paste `build_chassis.py` into the FreeCAD Python console)

## Check before printing

```
cd mechanical/preview
python3 validate.py                  # all-PASS gate on the parameters
python3 preview_chassis.py           # regenerate the massing preview
```

## Conventions

World origin at the centre of the track footprint, on the ground plane.
**+X right, +Y forward, +Z up.** Edit `params.csv` and re-run — never edit
dimensions inside the scripts. `locked=1` rows trace to the approved BOM and the
Phase 00 handoff; changing one is a phase decision.
