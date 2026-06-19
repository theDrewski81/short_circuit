"""Johnny 5 running mass budget vs the 1.6 kg ceiling.

Totals every component line in components.csv, broken down by option group
(base = 4-servo build; nod = head-nod 5th servo; brow = articulated-brow 6th
servo; wheel = rear trailing caster), and tests the assembled total against the
ceiling with a +25% sensitivity margin on the soft (printed/estimated) items.

Run: python3 mass_budget.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "freecad"))
import j5_params

HERE = os.path.dirname(os.path.abspath(__file__))
CEILING = j5_params.get()["weight_ceiling"]

rows = []
with open(os.path.join(HERE, "components.csv"), newline="") as f:
    for r in csv.DictReader(f):
        name = (r.get("item") or "").strip()
        if not name or name.startswith("#"):
            continue
        rows.append({"cat": r["category"], "qty": float(r["qty"]), "unit": float(r["unit_g"]),
                     "opt": r["option"], "est": int(r["est"])})

total = sum(x["qty"] * x["unit"] for x in rows)
soft = sum(x["qty"] * x["unit"] for x in rows if x["est"])
worst = total + 0.25 * soft

opts = {}
for x in rows:
    opts[x["opt"]] = opts.get(x["opt"], 0) + x["qty"] * x["unit"]

label = {"base": "base build (4 servos)", "nod": "head nod (5th servo)",
         "brow": "brow roll (6th servo)", "wheel": "trailing caster"}
print(f"\n  Johnny 5 mass budget   (ceiling {CEILING:.0f} g)")
print("  " + "-" * 50)
for o in ("base", "nod", "brow", "wheel"):
    if o in opts:
        print(f"    {label.get(o, o):26s} {opts[o]:7.0f} g")
print("  " + "-" * 50)
print(f"  ASSEMBLED TOTAL              {total:7.0f} g   ({total / CEILING * 100:4.1f}% of ceiling)")
print(f"  headroom                     {CEILING - total:7.0f} g")
print(f"  worst-case (+25% printed)   {worst:7.0f} g   {'UNDER' if worst < CEILING else 'OVER'} ceiling")
print("  " + "-" * 50)
ok = total < CEILING and worst < CEILING
print("  VERDICT: " + ("within ceiling with margin" if ok else "OVER tolerance") + "\n")
sys.exit(0 if ok else 1)
