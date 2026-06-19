"""Massing preview of the chassis from params.csv (matplotlib, no FreeCAD).

Renders front + side + iso orthographic views so the packaging can be eyeballed
before opening FreeCAD. Output: chassis_massing_v1.png
"""

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
    f = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
         [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
    return [[v[i] for i in face] for face in f]


def cyl_x(cx, cy, cz, r, length, n=24):
    """Cylinder with axis along X, centred-x at cx, length along X."""
    t = np.linspace(0, 2 * np.pi, n)
    yc, zc = cy + r * np.cos(t), cz + r * np.sin(t)
    x0, x1 = cx - length / 2, cx + length / 2
    faces = []
    for i in range(n - 1):
        faces.append([[x0, yc[i], zc[i]], [x0, yc[i + 1], zc[i + 1]],
                      [x1, yc[i + 1], zc[i + 1]], [x1, yc[i], zc[i]]])
    return faces


def add(ax, faces, color, alpha=1.0, ec="k", lw=0.3):
    pc = Poly3DCollection(faces, facecolor=color, edgecolor=ec, linewidths=lw, alpha=alpha)
    ax.add_collection3d(pc)


def draw(ax):
    W, Lg, H = P["tub_width"], P["tub_len"], P["tub_height"]
    Z0, AXLE = P["ground_clearance"], P["axle_z"]
    r = P["wheel_outer_r"]
    yb = P["wheelbase"] / 2

    # tub
    add(ax, box_faces(0, 0, Z0, W, Lg, H), "#c7cbd1", 0.55, ec="#555")
    # deck
    add(ax, box_faces(0, 0, Z0 + H, W, Lg, P["deck_wall"]), "#aeb3ba", 0.8, ec="#555")
    # tracks (both sides): represented as long boxes wrapping the wheels
    for sgn in (-1, 1):
        xc = sgn * P["track_cc"] / 2
        add(ax, box_faces(xc, 0, 0, P["track_width"], P["footprint_len"], 2 * r),
            "#454b54", 0.30, ec="#222")
        # drive sprocket (rear) + idler (front) + road wheels
        ys = [-yb, yb] + [(-yb * 0.6 + (i + 1) / (P["roadwheels_per_side"] + 1) * (1.2 * yb))
                          for i in range(int(P["roadwheels_per_side"]))]
        for y in ys:
            wr = r if abs(abs(y) - yb) < 1 else P["roadwheel_dia"] / 2
            add(ax, cyl_x(xc, y, AXLE, wr, P["track_width"]), "#6b7280", 0.9, ec="#222", lw=0.2)
    # motors (rear, inside tub)
    for sgn in (-1, 1):
        x_out = sgn * (W / 2 - P["tub_wall"])
        cx = x_out - sgn * (P["motor_body_len"] / 2)
        add(ax, cyl_x(cx, -yb, AXLE, P["motor_dia"] / 2, P["motor_body_len"]),
            "#b06a00", 0.95, ec="#5a3600", lw=0.2)
    # battery
    add(ax, box_faces(0, -6, Z0 + P["tub_wall"], P["battery_w"], P["battery_l"], P["battery_h"]),
        "#2e7d32", 0.8, ec="#1b4d20")
    # Pi-M shelf board
    add(ax, box_faces(0, yb - 28 + 0, Z0 + P["tub_wall"] + P["pi_shelf_z"] + P["pi_standoff_h"],
                      P["pi_w"], P["pi_l"], 1.6), "#1f6feb", 0.9, ec="#0b3")
    # ground
    gx, gy = np.meshgrid([-110, 110], [-110, 110])
    ax.plot_surface(gx, gy, np.zeros_like(gx), color="#eee", alpha=0.25)


def style(ax, elev, azim, title):
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, 0.8))
    ax.set_xlim(-110, 110); ax.set_ylim(-110, 110); ax.set_zlim(0, 90)
    ax.set_xlabel("X"); ax.set_ylabel("Y (fwd)"); ax.set_zlabel("Z")
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])


fig = plt.figure(figsize=(15, 5))
for i, (e, a, t) in enumerate([(8, -90, "Front  (+Y toward viewer)"),
                               (8, 0, "Right side  (drive at rear)"),
                               (24, -50, "Iso")]):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d")
    draw(ax); style(ax, e, a, t)

fig.suptitle("Johnny 5 - Chassis / Tread Base v1  (massing preview, parallel stance)",
             fontsize=12, y=0.98)
out = os.path.join(HERE, "chassis_massing_v1.png")
plt.tight_layout(); plt.savefig(out, dpi=110, bbox_inches="tight")
print("wrote", out)
