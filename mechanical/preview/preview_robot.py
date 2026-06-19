"""Full-stack massing preview (chassis + torso + neck + head + arms) from params.

matplotlib only, no FreeCAD. Output: robot_massing_v1.png
"""

import math
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "freecad"))
import j5_params

P = j5_params.get()
HERE = os.path.dirname(os.path.abspath(__file__))


def box_faces(cx, cy, cz, lx, ly, lz):
    x0, x1 = cx - lx / 2, cx + lx / 2
    y0, y1 = cy - ly / 2, cy + ly / 2
    z0, z1 = cz, cz + lz
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    f = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
    return [[v[i] for i in face] for face in f]


def taper_faces(cz, lz, wb, wt, d, ysh):
    z0, z1 = cz, cz + lz
    b = [[-wb / 2, -d / 2, z0], [wb / 2, -d / 2, z0], [wb / 2, d / 2, z0], [-wb / 2, d / 2, z0]]
    t = [[-wt / 2, -d / 2 + ysh, z1], [wt / 2, -d / 2 + ysh, z1],
         [wt / 2, d / 2 + ysh, z1], [-wt / 2, d / 2 + ysh, z1]]
    faces = [b, t]
    for i in range(4):
        j = (i + 1) % 4
        faces.append([b[i], b[j], t[j], t[i]])
    return faces


def cyl_z(cx, cy, z0, r, h, n=24):
    t = np.linspace(0, 2 * np.pi, n)
    xc, yc = cx + r * np.cos(t), cy + r * np.sin(t)
    return [[[xc[i], yc[i], z0], [xc[i + 1], yc[i + 1], z0],
             [xc[i + 1], yc[i + 1], z0 + h], [xc[i], yc[i], z0 + h]] for i in range(n - 1)]


def cyl_x(cx, cy, cz, r, length, n=20):
    t = np.linspace(0, 2 * np.pi, n)
    yc, zc = cy + r * np.cos(t), cz + r * np.sin(t)
    x0, x1 = cx - length / 2, cx + length / 2
    return [[[x0, yc[i], zc[i]], [x0, yc[i + 1], zc[i + 1]],
             [x1, yc[i + 1], zc[i + 1]], [x1, yc[i], zc[i]]] for i in range(n - 1)]


def add(ax, faces, color, alpha=1.0, ec="#333", lw=0.3):
    ax.add_collection3d(Poly3DCollection(faces, facecolor=color, edgecolor=ec, linewidths=lw, alpha=alpha))


def arm(ax, sgn, wsh, ty):
    px = sgn * (wsh / 2 + 8)
    sz = P["shoulder_z"]
    add(ax, cyl_x(px, ty, sz, 9, 12), "#b06a00", 0.95, lw=0.2)
    ua = P["upper_arm_len"]
    add(ax, box_faces(px, ty, sz - ua, 12, 14, ua), "#9aa0a8", 0.95)
    ez = sz - ua
    drop = P["forearm_len"] * math.cos(math.radians(P["elbow_angle"]))
    fwd = P["forearm_len"] * math.sin(math.radians(P["elbow_angle"]))
    add(ax, box_faces(px, ty + fwd / 2 + 6, ez - drop, 12, 14, drop), "#9aa0a8", 0.95)
    cyp, czp = ty + fwd + 10, ez - drop
    add(ax, box_faces(px, cyp, czp - 6, 16, 12, 6), "#7f868f", 0.95)
    for fx in (-5, 0, 5):
        add(ax, box_faces(px + fx, cyp + 2, czp - 6 - P["claw_len"], 3.5, 3.5, P["claw_len"]), "#7f868f", 1.0, lw=0.1)


def head(ax):
    hy = P["torso_lean"] + 6
    zb = P["neck_top"]
    yf = hy + P["head_depth"] / 2
    add(ax, box_faces(0, hy, zb, P["head_w"], P["head_depth"], P["head_h"]), "#c7cbd1", 0.55)
    # eyes (brass ring + iris) outboard
    for sgn in (-1, 1):
        ex = sgn * P["eye_spacing"] / 2
        add(ax, cyl_x(ex, yf, zb + P["head_h"] * 0.62, P["eye_dia"] / 2, 9), "#b08d3c", 0.95, lw=0.2)
        add(ax, cyl_x(ex, yf + 4, zb + P["head_h"] * 0.62, P["eye_dia"] / 2 - 8, 4), "#1f6feb", 1.0, lw=0.1)
    # central camera in bridge
    add(ax, cyl_x(0, yf, zb + P["head_h"] * 0.49, P["cam_aperture"] / 2, 8), "#16191d", 1.0, lw=0.1)
    # mouth bar
    add(ax, box_faces(0, yf, zb + P["head_h"] * 0.27, P["mouth_w"], 4, P["mouth_h"]), "#23272c", 0.95)
    # two brow blades (neutral), pivoting outboard
    for sgn in (-1, 1):
        cx = sgn * (P["brow_pivot_offset"] - P["brow_blade_len"] / 2)
        add(ax, box_faces(cx, yf - 4, zb + P["brow_pivot_z"], P["brow_blade_len"], 12, 4), "#2b2f35", 1.0)
    # antenna
    add(ax, cyl_z(0, hy, P["head_top"], P["antenna_dia"] / 2, P["antenna_h"]), "#454b54", 1.0, lw=0.2)


def draw(ax):
    add(ax, box_faces(0, 0, P["ground_clearance"], P["tub_width"], P["tub_len"], P["tub_height"]), "#c7cbd1", 0.5)
    add(ax, box_faces(0, 0, P["deck_top"] - P["deck_wall"], P["tub_width"], P["tub_len"], P["deck_wall"]), "#aeb3ba", 0.7)
    r = P["wheel_outer_r"]
    yb = P["wheelbase"] / 2
    for sgn in (-1, 1):
        xc = sgn * P["track_cc"] / 2
        for y in (-yb, yb):
            add(ax, cyl_x(xc, y, P["axle_z"], r, P["track_width"]), "#6b7280", 0.9, lw=0.2)
        add(ax, box_faces(xc, 0, 0, P["track_width"], P["footprint_len"], 2 * r), "#454b54", 0.25)

    add(ax, taper_faces(P["deck_top"], P["torso_h"], P["torso_w_base"], P["torso_w_top"],
                        P["torso_depth"], P["torso_lean"]), "#c7cbd1", 0.55)
    add(ax, box_faces(0, P["torso_depth"] / 2 - 1, P["deck_top"] + 70, 60, 2, 55), "#9aa0a8", 0.8)

    wsh = P["torso_w_base"] + (P["torso_w_top"] - P["torso_w_base"]) * (P["shoulder_z_off"] / P["torso_h"])
    ty = P["torso_lean"] * 0.8
    add(ax, box_faces(-wsh / 2 - 4, 0, P["shoulder_z"] + 22, 26, 30, 22), "#b4b9c0", 0.85)
    for sgn in (-1, 1):
        arm(ax, sgn, wsh, ty)

    add(ax, cyl_z(0, P["torso_lean"], P["torso_top"], P["neck_dia"] / 2, P["neck_h"]), "#aeb3ba", 0.9, lw=0.2)
    for sgn in (-1, 1):
        add(ax, cyl_z(sgn * 8, P["torso_depth"] / 2 - 6, P["torso_top"], 2.5, P["neck_h"] - 6), "#b06a00", 0.9, lw=0.1)

    head(ax)
    gx, gy = np.meshgrid([-140, 140], [-140, 140])
    ax.plot_surface(gx, gy, np.zeros_like(gx), color="#eee", alpha=0.2)


def style(ax, elev, azim, title):
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, 1.9))
    ax.set_xlim(-140, 140); ax.set_ylim(-140, 140); ax.set_zlim(0, P["total_h"] + 10)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])


fig = plt.figure(figsize=(13, 8))
for i, (e, a, t) in enumerate([(6, -90, "Front  (+Y toward viewer)"),
                               (6, 0, "Right side  (front = +Y →)"),
                               (16, -55, "Iso")]):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d")
    draw(ax); style(ax, e, a, t)
fig.suptitle(f"Johnny 5 - full stack, wide head + brows  (massing, ~{P['total_h']:.0f} mm)", fontsize=12, y=0.97)
out = os.path.join(HERE, "robot_massing_v1.png")
plt.tight_layout(); plt.savefig(out, dpi=105, bbox_inches="tight")
print("wrote", out)
