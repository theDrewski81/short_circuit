#!/usr/bin/env python3
"""Guard for the power wiring and harness definition.

Parses the net table out of docs/HARDWARE_power_harness.md, the two GPIO pin maps,
the Power Budget and section 6 out of BOM.md, and the net names out of
docs/diagrams/power_harness_schematic.svg, then asserts six things. Every check is
written so that a real defect makes it raise. Comparing numbers to numbers and
printing a pass is the failure mode this project has already had.

Run from the repository root:  python scripts/check_harness_nets.py
Or from anywhere:              python check_harness_nets.py --root <repo>
"""
import argparse
import os
import re
import sys

# Assumptions that are not stated in BOM.md, declared here so they are arguable.
BUCK_EFFICIENCY = 0.90          # synchronous buck, nominal
VBAT_NOMINAL_V = 7.4            # 2S LiPo nominal, the conservative case for input current
PI_3V3_PIN_LIMIT_A = 0.25       # conservative ceiling for a Pi Zero 2 W 3.3 V header pin
RAIL_HEADROOM_A = 0.25          # how far the net table may exceed the Power Budget

RAIL_PREFIXES = {"VBAT_": "VBAT", "5V_": "5V", "6V_": "6V", "3V3M_": "3V3", "3V3V_": "3V3"}
NON_RAIL_PREFIXES = ("SIG_", "OUT_", "GND_")
RAIL_NOMINAL_V = {"VBAT": VBAT_NOMINAL_V, "5V": 5.0, "6V": 6.0, "3V3": 3.3}


class CheckFailure(Exception):
    pass


def fail(check, message):
    raise CheckFailure("%s: %s" % (check, message))


def read(path):
    if not os.path.isfile(path):
        fail("input", "missing file %s" % path)
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def table_rows(text, width):
    """Every pipe-table row of exactly `width` cells, separators dropped."""
    out = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != width or cells[0].startswith("---"):
            continue
        out.append(cells)
    return out


# --------------------------------------------------------------------------- parse

def parse_nets(doc):
    nets = []
    for cells in table_rows(doc, 6):
        if not re.match(r"^[A-Z0-9_]+$", cells[0]):
            continue
        net, src, dst, gauge, conn, notes = cells
        nets.append({"net": net, "src": src, "dst": dst,
                     "gauge": gauge, "conn": conn, "notes": notes})
    if not nets:
        fail("input", "no net rows parsed out of the harness document")
    seen = set()
    for n in nets:
        if n["net"] in seen:
            fail("input", "net %s is listed twice" % n["net"])
        seen.add(n["net"])
        for field in ("src", "dst", "gauge"):
            if not n[field]:
                fail("input", "net %s has an empty %s cell" % (n["net"], field))
    return nets


def parse_pin_maps(bom):
    """{'Pi-M': {gpio: function}, 'Pi-V': {...}} from the two GPIO Pin Map sections."""
    maps = {}
    for pi, heading in (("Pi-M", "GPIO Pin Map — Pi-M"), ("Pi-V", "GPIO Pin Map — Pi-V")):
        start = bom.find(heading)
        if start < 0:
            fail("input", "BOM.md has no %s section" % heading)
        nxt = bom.find("\n## ", start + 1)
        section = bom[start:nxt if nxt > 0 else len(bom)]
        pins = {}
        for cells in table_rows(section, 3):
            if cells[1].startswith("GPIO"):
                continue
            for raw in re.findall(r"\d+", cells[1]):
                gpio = int(raw)
                if gpio in pins:
                    fail("pin map", "GPIO %d appears twice in the %s pin map (%r and %r)"
                         % (gpio, pi, pins[gpio], cells[0]))
                pins[gpio] = cells[0]
        if not pins:
            fail("input", "no GPIO rows parsed out of the %s pin map" % pi)
        maps[pi] = pins
    return maps


def parse_power_budget(bom):
    """{rail_key: peak_amps} from the Power Budget table."""
    start = bom.find("## Power Budget")
    if start < 0:
        fail("input", "BOM.md has no Power Budget section")
    nxt = bom.find("\n## ", start + 1)
    section = bom[start:nxt if nxt > 0 else len(bom)]
    budget = {}
    rows = 0
    for cells in table_rows(section, 4):
        if cells[1] == "Rail":
            continue
        # A row naming two rails, "3.3 V / 5 V", is charged to the first one named,
        # so its current is not counted on both.
        rail = normalise_rail(cells[1].split("/")[0].strip())
        amps = parse_amps(cells[3])
        if amps is None:
            continue
        budget[rail] = round(budget.get(rail, 0.0) + amps, 3)
        rows += 1
    if rows < 5:
        fail("input", "only %d Power Budget rows parsed; the table shape has changed" % rows)
    return budget


def normalise_rail(cell):
    low = cell.lower()
    if "battery-direct" in low:
        return "VBAT"
    if low.startswith("3.3"):
        return "3V3"
    if low.startswith("5 v"):
        return "5V"
    if low.startswith("6 v"):
        return "6V"
    return cell


def parse_amps(cell):
    m = re.search(r"([0-9]*\.?[0-9]+)\s*A", cell.replace("~", ""))
    return float(m.group(1)) if m else None


def parse_section6_ratings(bom):
    """{'buck': A, 'fuse': A} from BOM.md section 6."""
    start = bom.find("## 6. Power")
    if start < 0:
        fail("input", "BOM.md has no section 6")
    nxt = bom.find("\n## ", start + 1)
    section = bom[start:nxt if nxt > 0 else len(bom)]
    ratings = {}
    for cells in table_rows(section, 5):
        part = cells[0].lower()
        amps = parse_amps(cells[1])
        if amps is None:
            continue
        if "buck converter" in part:
            ratings["buck"] = amps
        elif part.startswith("fuse"):
            ratings["fuse"] = amps
    for key in ("buck", "fuse"):
        if key not in ratings:
            fail("input", "no %s rating found in BOM.md section 6" % key)
    return ratings


def parse_bom_items(bom):
    """Text of every BOM parts-table line item.

    Only the five-column parts tables in sections 1 to 7 count. The GPIO pin maps and
    the Power Budget are deliberately excluded: a pin map row is not a line item, and
    letting one satisfy this check would let a part be wired that nobody can order.
    """
    items = []
    for cells in table_rows(bom, 5):
        if cells[0] == "Part":
            continue
        items.append(" ".join(cells))
    if len(items) < 20:
        fail("input", "only %d BOM line items parsed; BOM.md shape has changed" % len(items))
    return items


def parse_svg_nets(svg):
    return set(re.findall(r"\b(?:VBAT|5V|6V|3V3M|3V3V|SIG|OUT|GND)_[A-Z0-9_]+\b", svg))


# --------------------------------------------------------------------------- checks

def rail_of(net):
    for prefix, rail in RAIL_PREFIXES.items():
        if net.startswith(prefix):
            return rail
    if not net.startswith(NON_RAIL_PREFIXES):
        fail("net naming", "net %s starts with no recognised prefix; a net is either "
                           "rail-prefixed (%s) or one of %s"
             % (net, ", ".join(sorted(RAIL_PREFIXES)), ", ".join(NON_RAIL_PREFIXES)))
    return None


def net_peak(net):
    """(amps, is_reflected) for a rail-prefixed net. Raises if the tag is missing."""
    peak = re.search(r"\[peak\s+([0-9]*\.?[0-9]+)\s*A\]", net["notes"])
    reflected = "[reflected]" in net["notes"]
    if peak and reflected:
        fail("current tags", "net %s declares both a peak and [reflected]" % net["net"])
    if peak:
        return float(peak.group(1)), False
    if reflected:
        return 0.0, True
    fail("current tags", "net %s is on a rail but declares neither [peak N A] nor "
                         "[reflected], so its current would silently count as zero"
         % net["net"])


def endpoints(net):
    out = []
    for cell in (net["src"], net["dst"]):
        for piece in cell.split(" + "):
            piece = piece.strip()
            if piece:
                out.append(piece)
    return out


def normalise(text):
    return re.sub(r"[^a-z0-9#+\- ]", " ", text.lower())


def longest_bom_prefix(endpoint, items_blob):
    words = endpoint.split()
    for length in range(min(4, len(words)), 0, -1):
        candidate = " ".join(words[:length])
        norm = normalise(candidate).strip()
        if len(norm.replace(" ", "")) < 3:
            continue
        if re.sub(r"\s+", " ", norm) in items_blob:
            return candidate
    return None


def check_gpio(nets, pin_maps):
    """1. Every GPIO a net references exists in that Pi's map.
       2. No GPIO is claimed by two different nets."""
    claimed = {}
    referenced = 0
    for net in nets:
        for endpoint in endpoints(net):
            gpios = [int(g) for g in re.findall(r"GPIO\s*(\d+)", endpoint)]
            if not gpios:
                continue
            pis = [p for p in ("Pi-M", "Pi-V") if p in endpoint]
            if len(pis) != 1:
                fail("gpio ownership", "endpoint %r on net %s names %d Pis, so the pin map "
                                       "to check against is ambiguous" % (endpoint, net["net"], len(pis)))
            pi = pis[0]
            for gpio in gpios:
                referenced += 1
                if gpio not in pin_maps[pi]:
                    fail("gpio exists", "net %s uses %s GPIO %d, which is in no %s pin map row"
                         % (net["net"], pi, gpio, pi))
                key = (pi, gpio)
                if key in claimed and claimed[key] != net["net"]:
                    fail("gpio uniqueness", "%s GPIO %d is claimed by both %s and %s"
                         % (pi, gpio, claimed[key], net["net"]))
                claimed[key] = net["net"]
    if referenced < 20:
        fail("gpio parse", "only %d GPIO references found; the net table is not being read"
             % referenced)
    return claimed


def check_rails(nets, budget, ratings):
    """3. Rails exist in the Power Budget, and summed peaks stay inside the ratings."""
    totals = {}
    for net in nets:
        rail = rail_of(net["net"])
        if rail is None:
            continue
        amps, reflected = net_peak(net)
        if rail not in budget:
            fail("rail exists", "net %s is on rail %s, which appears in no Power Budget row"
                 % (net["net"], rail))
        if not reflected:
            totals[rail] = round(totals.get(rail, 0.0) + amps, 3)
    limits = {"VBAT": ratings["fuse"], "5V": ratings["buck"],
              "6V": ratings["buck"], "3V3": PI_3V3_PIN_LIMIT_A}
    for rail in sorted(totals):
        drawn, allowed, planned = totals[rail], limits[rail], budget[rail]
        if drawn > allowed + 1e-9:
            fail("rail rating", "rail %s sums to %.2f A against a %.2f A rating"
                 % (rail, drawn, allowed))
        if drawn + 1e-9 < planned:
            fail("rail reconciliation", "rail %s sums to %.2f A in the net table but the "
                                        "Power Budget plans %.2f A, so a load is missing"
                 % (rail, drawn, planned))
        if drawn > planned + RAIL_HEADROOM_A + 1e-9:
            fail("rail reconciliation", "rail %s sums to %.2f A against a planned %.2f A, "
                                        "over the %.2f A fine-grain allowance"
                 % (rail, drawn, planned, RAIL_HEADROOM_A))
    for rail in budget:
        if rail not in totals:
            fail("rail coverage", "the Power Budget carries rail %s but no net supplies it" % rail)
    return totals, limits


def check_fuse(totals, ratings):
    """Battery-side worst case, reflected through the converters, against the fuse."""
    at_fuse = totals.get("VBAT", 0.0)
    detail = [("motor rail, direct", totals.get("VBAT", 0.0))]
    for rail in ("5V", "6V"):
        if rail not in totals:
            continue
        reflected = totals[rail] * RAIL_NOMINAL_V[rail] / (VBAT_NOMINAL_V * BUCK_EFFICIENCY)
        at_fuse += reflected
        detail.append(("%s buck input" % rail, reflected))
    if at_fuse > ratings["fuse"] + 1e-9:
        fail("fuse margin", "worst-case battery-side draw is %.2f A against a %.2f A fuse"
             % (at_fuse, ratings["fuse"]))
    return at_fuse, detail


def check_endpoints(nets, items):
    """4. Every part referenced as a net endpoint is a BOM line item."""
    blob = re.sub(r"\s+", " ", " ".join(normalise(i) for i in items))
    matched = {}
    for net in nets:
        for endpoint in endpoints(net):
            part = longest_bom_prefix(endpoint, blob)
            if part is None:
                fail("endpoint in BOM", "endpoint %r on net %s matches no BOM.md line item"
                     % (endpoint, net["net"]))
            key = re.sub(r"\s+", " ", normalise(part)).strip()
            matched[key] = matched.get(key, 0) + 1
    return matched


def check_component_values(nets, items):
    """5. Every passive value called out on a net is a BOM line item too."""
    blob = re.sub(r"\s+", " ", " ".join(items))
    values = set()
    for net in nets:
        for cell in (net["src"], net["dst"], net["notes"]):
            for value in re.findall(r"\d+(?:\.\d+)?\s*(?:k|M)?(?:Ω|µF)", cell):
                values.add(re.sub(r"\s+", " ", value).strip())
    if not values:
        fail("component values", "no passive values found on any net; the notes are not being read")
    for value in sorted(values):
        if value not in blob:
            fail("component value in BOM", "%s is called out on a net but is on no BOM.md line item"
                 % value)
    return values


def check_svg(nets, svg_nets):
    """6. The drawing and the document carry the same nets."""
    doc_nets = {n["net"] for n in nets}
    missing = sorted(doc_nets - svg_nets)
    extra = sorted(svg_nets - doc_nets)
    if missing:
        fail("drawing parity", "%d net(s) in the document but not in the SVG: %s"
             % (len(missing), ", ".join(missing)))
    if extra:
        fail("drawing parity", "%d net(s) in the SVG but not in the document: %s"
             % (len(extra), ", ".join(extra)))
    return len(doc_nets)


# --------------------------------------------------------------------------- main

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.path.dirname(here),
                        help="repository root (default: the parent of this script's directory)")
    args = parser.parse_args()
    root = args.root

    doc = read(os.path.join(root, "docs", "HARDWARE_power_harness.md"))
    bom = read(os.path.join(root, "BOM.md"))
    svg = read(os.path.join(root, "docs", "diagrams", "power_harness_schematic.svg"))

    nets = parse_nets(doc)
    pin_maps = parse_pin_maps(bom)
    budget = parse_power_budget(bom)
    ratings = parse_section6_ratings(bom)
    items = parse_bom_items(bom)

    print("harness net check")
    print("  root                %s" % root)
    print("  nets                %d" % len(nets))
    print("  pin maps            Pi-M %d GPIO, Pi-V %d GPIO"
          % (len(pin_maps["Pi-M"]), len(pin_maps["Pi-V"])))
    print("  BOM line items      %d" % len(items))
    print("")

    claimed = check_gpio(nets, pin_maps)
    per_pi = {}
    for (pi, _), _net in claimed.items():
        per_pi[pi] = per_pi.get(pi, 0) + 1
    print("  [1] gpio exists     OK   %d GPIO references, all in their Pi's pin map"
          % len(claimed))
    print("  [2] gpio unique     OK   %s"
          % ", ".join("%s %d claimed" % (pi, n) for pi, n in sorted(per_pi.items())))

    totals, limits = check_rails(nets, budget, ratings)
    print("  [3] rails           OK")
    print("        rail   net table   budget   rating")
    for rail in sorted(totals):
        print("        %-6s %7.2f A %8.2f A %7.2f A" % (rail, totals[rail], budget[rail], limits[rail]))
    at_fuse, detail = check_fuse(totals, ratings)
    for label, amps in detail:
        print("        %-24s %5.2f A" % (label, amps))
    print("        %-24s %5.2f A of %.2f A fuse (%.0f %% margin)"
          % ("worst case at the fuse", at_fuse, ratings["fuse"],
             100.0 * (ratings["fuse"] - at_fuse) / ratings["fuse"]))

    matched = check_endpoints(nets, items)
    print("  [4] endpoints       OK   %d endpoint references resolve to %d BOM line items"
          % (sum(matched.values()), len(matched)))
    print("        %s" % ", ".join(sorted(matched)))

    values = check_component_values(nets, items)
    print("  [5] passive values  OK   %s" % ", ".join(sorted(values)))

    count = check_svg(nets, parse_svg_nets(svg))
    print("  [6] drawing parity  OK   %d nets, document and SVG identical" % count)

    print("")
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CheckFailure as exc:
        print("CHECK FAILED -- %s" % exc, file=sys.stderr)
        sys.exit(1)
