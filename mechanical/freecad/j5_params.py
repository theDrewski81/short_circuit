"""Parameter loader for the Johnny 5 mechanical build scripts.

Pure-Python, no FreeCAD dependency, so the same loader feeds both the FreeCAD
build scripts and the (FreeCAD-free) validation / preview scripts.

Source of truth is params.csv, sitting next to this file. Derived geometry is
computed once, here, so every consumer agrees on the same numbers.
"""

import csv
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CSV = os.path.join(_HERE, "params.csv")


def load_raw(path=_CSV):
    """Return {name: float} from params.csv, ignoring comment/blank rows."""
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            if not name or name.startswith("#"):
                continue
            out[name] = float(row["value"])
    return out


def derive(p):
    """Add computed geometry to the raw parameter dict (returns the same dict)."""
    p["overall_track_width"] = p["track_cc"] + p["track_width"]          # outer track-to-track
    p["tub_inner_gap"] = p["track_cc"] - p["track_width"]                # between inner track faces
    p["footprint_len"] = p["wheelbase"] + p["sprocket_pitch_dia"]        # ground contact length
    # axle sits at pitch radius + track band thickness above the ground contact line
    p["axle_z"] = p["sprocket_pitch_dia"] / 2.0 + p["track_thickness"]
    p["wheel_outer_r"] = p["sprocket_pitch_dia"] / 2.0 + p["track_thickness"]
    p["base_height_total"] = p["ground_clearance"] + p["tub_height"]     # underside floor to deck top
    p["tub_outer_w"] = p["tub_width"]
    p["tub_outer_l"] = p["tub_len"]
    p["tub_outer_h"] = p["tub_height"] + p["deck_wall"]
    # --- vertical stack (absolute z, ground = 0) ---
    p["deck_top"] = p["ground_clearance"] + p["tub_height"] + p["deck_wall"]
    p["shoulder_z"] = p["deck_top"] + p["shoulder_z_off"]
    p["torso_top"] = p["deck_top"] + p["torso_h"]
    p["neck_top"] = p["torso_top"] + p["neck_h"]
    p["head_top"] = p["neck_top"] + p["head_h"]
    p["total_h"] = p["head_top"] + p["antenna_h"]
    return p


def get():
    """Convenience: loaded + derived parameter dict."""
    return derive(load_raw())


if __name__ == "__main__":
    p = get()
    for k in sorted(p):
        print(f"{k:24s} {p[k]:.3f}")
