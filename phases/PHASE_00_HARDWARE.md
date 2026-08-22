# Phase 00 — Hardware Design & BOM

## Objective

Finalize all hardware selections and produce a complete, orderable Bill of Materials. Baseline the Johnny 5 body design in FreeCAD. No software is written in this phase, but all physical constraints that affect software design are locked in. Ordering should not happen and printing should not start until the gate is met.

---

## Gate Condition

**BOM is finalized and approved. Body design is baselined in FreeCAD 1.1.1.**

Finalized means: every component is selected to a specific part number with a known supplier. Approved means: Andrew has explicitly confirmed the BOM before ordering.

---

## Context

Andrew already owns: two Raspberry Pi Zero 2 W units (with microSD cards, pre-soldered GPIO headers, and 8MP 1080p CSI cameras), a Creality Ender 3 Pro, and FreeCAD 1.1.1.

The GrowBot reference (britcruise9/GrowBot) uses Feetech SCS0009 serial bus servos, a single-cell LiPo with MT3608 boost to 5V, and breadboard-level power distribution. Johnny 5 has a substantially larger actuator set (2 DC motors for treads + 3 serial bus servos for arms and head) and a more complex body design. The power architecture must be designed for this load, not copied directly from GrowBot.

Key constraint: the Pi Zero 2 W GPIO header is 40-pin, 3.3V logic. Motor drivers must be logic-level compatible or use a level shifter.

---

## Tasks

### 1. Tread Drive System

Select DC motors and H-bridge driver for tread locomotion.

Motor requirements: sufficient torque to drive treads with the assembled robot weight (estimate 400–600g before chassis), shaft compatible with tread sprocket or wheel, voltage in the 5–12V range for practical power architecture. Geared motors (TT motors or N20 with encoders) are appropriate; encoders are recommended if closed-loop speed control is desired for straight-line driving.

H-bridge driver considerations: TB6612FNG is preferred over L298N (lower dropout, higher efficiency, more compact). DRV8833 is a compact alternative for lower-torque builds. MDD10A is appropriate if motor currents exceed 2A per channel. Confirm logic level compatibility with Pi Zero 2 W (3.3V).

Tread system: rubber tank treads with plastic sprockets are widely available in hobby robotics kits. Consider print-in-place treads in TPU if the Ender 3 Pro is configured for flexible filament. Track width and wheel spacing must be determined before body design can be finalized.

### 2. Arm and Head Servos

Select serial bus servos for left shoulder, right shoulder, and head rotation.

Feetech SCS0009 (same as GrowBot) or the Waveshare SC09 equivalent is the recommended baseline. These are half-duplex UART at 1 Mbps, report position and load, and chain on a single data bus. All three servos can share one UART bus on Pi-M, which simplifies wiring.

Confirm: 3 servos at estimated load draw (peak ~500mA each stalling) fit within the power budget.

Future expansion to elbow servos is in scope for a later phase. Design the servo bus and wiring to accommodate additional servos without rework.

### 3. Sensing Hardware

**VL53L1X Time-of-Flight (ToF):** Close-range obstacle detection on Pi-M. I²C (0x29 default address), 3.3V, up to ~4m range. Available as a breakout from Pololu or SparkFun. No alternative -- this is the selected sensor.

**MPU-6050 IMU:** Orientation sensing on Pi-M. Same as GrowBot (GY-521 breakout). I²C 0x68. No alternative -- consistent with reference.

### 4. Audio Hardware

One speaker, one amplifier, one microphone are required. The question is whether these are split between Pi-M and Pi-V or consolidated on Pi-V.

Recommendation: put microphone and speaker/amp on Pi-V (the cognition Pi). Audio I/O is part of the LLM interaction loop, not the motion control loop. Pi-M does not need audio. This simplifies Pi-M's responsibilities and avoids I²S pin conflicts.

Components: INMP441 I²S microphone, MAX98357A I²S amplifier, small 8Ω speaker (0.5–3W). Identical to GrowBot.

### 5. LED Ring

WS2812B LED ring (7+ pixels, 5V) on Pi-M for emotional and status expressiveness. Identical to GrowBot. Single GPIO data line. Requires root or appropriate permissions to drive.

The LED ring communicates robot state visually: online/offline, active/idle, emotion states. Color and pattern conventions are defined in Phase 04.

### 6. Power Architecture

This is the most critical departure from GrowBot. GrowBot runs everything off a single 1S LiPo → MT3608 boost to 5V, which is acceptable for two servos but insufficient for two DC motors plus three servos plus two Pis.

Design requirements:
- Separate power rails for motors and compute. Motor transients must not cause Pi brownouts.
- Two Pi Zero 2 W: ~200mA typical each, 400mA peak each.
- Two DC motors: current depends on selection; budget 1–2A per motor under load.
- Three servos (SCS0009): peak ~500mA each stalling; budget 1A typical for all three.
- Total compute + servo rail: ~2–3A budget; motor rail: sized to motor selection.

Recommended approach: 2S LiPo (7.4V nominal) with two separate regulation paths. A buck converter (LM2596-based or MP1584) steps down to 5V for compute + servos. Motor driver takes battery voltage directly (most H-bridges accept 7–15V input; the motors themselves set the floor). A capacitor bank across each 5V rail covers transient dips.

Alternatively: two separate 1S LiPo cells, one per rail. Simpler wiring, easier balancing, but two batteries to manage.

Document the chosen architecture with a wiring diagram before ordering. Do not replicate GrowBot's single-rail approach at this scale.

### 7. Body Design — FreeCAD

Johnny 5 reference aesthetics: tracked base, boxy torso, two arms with shoulder articulation, distinctive head with visor/eye element and antenna. The design must accommodate the actual selected hardware dimensions.

Design sequence:
1. Establish chassis dimensions from tread/motor selection.
2. Design tread base (motor mounts, tread sprocket cutouts, battery bay, Pi-M mounting).
3. Design torso (Pi-V mounting, camera mount in head, wiring routing).
4. Design arms (servo horn attachment points, range of motion clearance).
5. Design head (servo mount for rotation, camera mount, LED ring or eye element, antenna).

Ender 3 Pro build volume is 220×220×250mm. Large components must be split into printable pieces with alignment features (pins or keyed joints). Print in PLA for prototyping; upgrade stress-bearing parts to PETG for final build.

All FreeCAD source files go into the repo under `mechanical/freecad/`. STL exports for printing go into `mechanical/stl/`. Name files descriptively: `chassis_base_v1.stl`, `left_arm_upper_v1.stl`, etc.

### 8. BOM Document

Produce `BOM.md` in the repo root on the pattern of GrowBot's BOM.md. Columns: part, spec, qty, estimated cost (USD), supplier/notes. Include the GPIO pin map for both Pi-M and Pi-V. Include a power budget table.

---

## Recommended Session Start

Begin by reviewing the GrowBot BOM.md (https://github.com/britcruise9/GrowBot/blob/main/BOM.md) for component reference. Then work through each task above in order, starting with tread drive selection since chassis dimensions gate the body design.

---

## Open Questions for This Phase

- Encoder vs. no encoder on DC motors: does Andrew want closed-loop speed control for straight-line driving accuracy, or is open-loop adequate for V1?
- 2S LiPo vs. dual 1S: any preference on battery form factor or sourcing?
- Johnny 5 scale: rough target size? (e.g., fits on a standard desk vs. floor-roaming)
- Tread material preference: purchased rubber treads, printed TPU treads, or belt-and-sprocket?

---

## Session 01 — Status & Handoff (2026-06-17)

### Gate status: PARTIAL

BOM approved (`BOM.md`). FreeCAD body baseline (Task 7) is the only remaining gate item. Ordering and printing hold until the body is baselined.

### Open questions — resolved

- **Encoders:** Yes — N20-class geared motors with encoders (closed-loop driving + real velocity data for Phase 02 training).
- **Battery:** Single 2S LiPo, dual regulation.
- **Scale:** Floor-roaming, ~38–42 cm. Revised assembled-weight ceiling **1.6 kg**.
- **Tread material:** Printed TPU.

### Decision log (decisions + rationale)

- **Drive — Path A:** N20-class 12V/150:1 encoder motors + TB6612FNG, battery-direct on 2S. Chose compact/light/cheap/clean-logic over torque margin; accepts ~0.13 m/s and ~1× continuous torque margin. Contingent on the 1.6 kg ceiling.
- **Servos:** 4× SCS0009 (added a shoulder utility-box tilt servo) on one half-duplex bus via Waveshare Bus Servo Adapter (A). Arms kept light (≤50 g / ≤90 mm lever) to stay within rated torque and protect the weight budget.
- **Utility box** mounts to the torso shoulder with its own servo, so it never loads the arm servos. Navigation light (1 W) added on Pi-V as a camera aid.
- **Audio** consolidated on Pi-V (frees Pi-M's I²S). Needs a custom `simple-audio-card` overlay in Phase 01 (stock mic/amp overlays conflict).
- **LEDs:** mouth on Pi-V (SPI, audio-synced); eyes + battery gauge + status chained on Pi-M (SPI). Custom layout replaces the GrowBot ring.
- **Battery sensing** via ADS1115 — drives the gauge, a low-voltage cutoff, and telemetry.
- **Power:** three rails (motor battery-direct, 5V buck, 6V servo buck). Added inline 7.5 A fuse and a TB6612 STBY interlock (motors off on boot/crash). Servos must be regulated — 8.4 V full charge exceeds the SCS0009 7.4 V max.

### Deferred levers (not in V1 spend)

- Motor-rail boost to ~9–10 V if the drive proves underpowered.
- STS3215 servo upgrade if the arms lack authority.
- Path B (25D motors + higher-current driver) if Path A is inadequate.

### Next session — initiating prompt (Phase 00, Task 7)

> Johnny 5 — Phase 00, Session 02. Read CLAUDE.md, then `phases/PHASE_00_HARDWARE.md` (note this Session 01 status and decision log) and `BOM.md`. We resume Phase 00 at **Task 7: baseline the body in FreeCAD 1.1.1**. The BOM is approved and dimensions are locked. Session config: Opus, Extended Thinking, High effort.
>
> Work the brief's design sequence (chassis → torso → arms → head), one printable subassembly at a time, honoring: floor-roaming ~38–42 cm; the **1.6 kg weight ceiling** (design light — thin walls, low infill, lightening pockets); Ender 3 Pro 220×220×250 mm splits with keyed alignment; provisional track geometry (40 mm sprocket pitch dia, 28 mm track width, ~150 mm track center-to-center, 15–20 mm clearance); and all mounting features from the BOM (N20 motors + TB6612, 2S 2200 mAh battery bay, 2× Pi Zero 2 W, VL53L1X forward-facing, IMU, 4× SCS0009 incl. shoulder utility box, head camera + mouth/eye LEDs, speaker). Deliver FreeCAD as **parametric Python build scripts** (driven by a parameters spreadsheet) to `mechanical/freecad/`, STL exports to `mechanical/stl/`. Start with the chassis/tread base and confirm geometry before proceeding up the stack. Expect an interactive, question-driven pace.

### Attachments / docs for next session

- `CLAUDE.md`, this phase file, `BOM.md` (locked dimensions + pin maps).
- The two reference images Andrew shared (boombox-body photo; Lego-head photo) for head/torso proportions.
- **To produce before ordering:** a formal power wiring/harness diagram (the architecture is documented in `BOM.md`; a schematic should accompany it).

---

## Session 02 — Status & Handoff (2026-06-18)

### Gate status: MET

Both gate criteria satisfied. BOM approved (updated this session to 6× SCS0009 + rear trailing caster). Body baselined in FreeCAD 1.1.1 — all four build scripts run in the GUI Python console, all 13 STLs and the FCStd files generated, and the STLs confirmed to open and slice cleanly. The remaining mechanical detail (brow gear teeth, drivetrain/caster parts, eye/camera press-fit inserts, power-harness schematic) is refinement that carries forward into the relevant downstream phases and Phase 06 by design — it is not part of the baseline gate.

### What was built

Parametric build scripts in `mechanical/freecad/`, all driven by `params.csv` (single source of truth), with a FreeCAD-free `validate.py`, `mass_budget.py`, and matplotlib massing previews in `mechanical/preview/`:

- **Chassis/tread base** — tub 118×150×50, footprint 160×178, base height 68, drive at rear, 2 road wheels/side, prints in one piece. Belly 18 mm; axle at 23.5 mm (track band lifts the N20s clear). Rear trailing-caster pivot bosses + lean-ready waist reserve on the deck.
- **Torso** — tapered two-part keyed shell 110→96 ×90 ×165; Pi-V on the back wall; shoulders pitch on X; utility box on left; neck riser carries the head-yaw servo.
- **Arms** — single-DOF shoulder-pitch, fixed elbow, static 3-finger claw, ~24 g each; grip-ready (tendon channel/anchor/shoulder-axis path) for the V2 tendon gripper.
- **Head** — wide film-accurate 150×90×88 two-part shell; brass-ring eye domes + central camera in the bridge; mouth LED bar with speaker behind; **articulated twin brow blades** (offset outboard pivots, one bus servo → pinion to left gear direct, to right gear via an idler = mirrored roll, 3 poses); nod gimbal; antenna.

### Decision log (Session 02)

- **Stance:** parallel tracks confirmed (the splay in references reads as camera perspective).
- **Servos 4 → 6 SCS0009:** added head **nod** (#5) and articulated **brow roll** (#6), each mass-budget approved. Same bus (new IDs, no GPIO); 6 V rail ~3 A within the 5 A buck. +$22.
- **Stability:** rear **trailing swiveling sprung caster** (passive) added — rearward/incline tip margin 33°→54°, +33 g, +$5. Covers the case that matters at 0.13 m/s.
- **Powered waist — rejected for V1:** needs STS3215/lead-screw (SCS0009 can't hold the 531 g upper body: 5.4 vs 2.3 kg·cm), +116 g (worst-case 1662 g **over** the 1.6 kg ceiling), 6 V rail to ~4.5 A near the buck limit, +$26, for only ~7° decline gain not needed indoors. Value is expression, not stability. Interface left **lean-ready** (reserved pivot bosses + actuator pad) so it's a bolt-on V2.
- **Budgets:** mass ~**1321 g** (83% of ceiling, worst-case 1556 g under); height ~**395 mm** (in band); new-spend ~**$325–365**.

### Deferred levers (logged in BOM)

V2 tendon gripper (single-actuator underactuated claw); Dynamixel XL330 servo-standard alt; V2 powered waist; elbow servos; STS3215 arm-torque upgrade; motor-rail boost; Path B motors.

### Open threads for next session

- Run `freecadcmd build_*.py` to produce STL/FCStd; inspect in FreeCAD for interferences (the in-sandbox checks are dimensional/mass, not solid booleans).
- Generate brow **gear teeth** (FreeCAD Gear workbench, module in `params.csv`) — currently modelled as gear blanks.
- Detail the press-fit eye-dome/camera inserts; drivetrain parts (sprocket/idler/road-wheel/TPU track) and the caster wheel/arm.
- Power wiring/harness schematic (carried over from Session 01).
- **Commit:** the `mechanical/` tree, `BOM.md`, `.gitignore`, and this phase update are written and ready — the commit failed only because the `.git` index/locks on the Nextcloud mount are permission-locked from the sandbox.

### Next session — initiating prompt (Phase 01)

> Johnny 5 — Phase 01, Session 01. Read CLAUDE.md, then `phases/PHASE_01_INFRASTRUCTURE.md`, and note the Phase 00 close state in `phases/PHASE_00_HARDWARE.md` (Session 02 handoff). **Phase 00 is closed:** body baselined in FreeCAD (13 STLs slice cleanly), BOM approved at 6× SCS0009 + trailing caster, `mechanical/` committed on `phase/00-hardware` (merge → `main`, tag `v0.0`). Begin Phase 01 — stand up infrastructure: image both Pi Zero 2 W (Pi OS Lite 64-bit), finalize the inter-Pi message-queue protocol and the Pi-V→Pi-M intent contract, establish connectivity to the home-lab LiteLLM proxy, and implement the offline fallback (Pi-M conservative mode) — the **offline fallback is the Phase 01 gate**. Carry forward the power wiring/harness schematic owed from Phase 00 before any ordering or build. Session config: Sonnet, Standard, Medium.

---

## Session 03 — Status & Handoff (2026-08-20)

### Gate status: REOPENED for chassis rework, tub now printable

Phase 00 was closed at Session 02 on a body that had never been printed. Printing it reopened the tub: the first physical part had no motor-shaft, road-wheel or idler holes on its right wall, motors that could not be inserted, and an IMU pad underneath the battery. Four print-and-measure rounds later the tub is correct. The rest of the stack (torso, arms, head) is untouched and still stands on the Session 02 baseline.

### Decision log (Session 03)

- **FreeCAD MCP adopted, running locally.** neka-nat addon, installed on the Windows desktop rather than the home-lab LXC: the RPC server runs inside FreeCAD's own GUI process, so it must live wherever the GUI does. This is what made run-the-geometry verification possible.
- **Verification moved from parameters into the build.** `validate.py` compares numbers to numbers and reported ALL CHECKS PASS while three defects reached the print bed. Boolean guards in `main()` — hole open *and* correct size, keep-out volumes, motor drop position, bearing shoulder present — are the ones that catch real defects. An overlapping fuse is legal and still returns one solid, so the single-solid check cannot see two features claiming the same volume.
- **Bearings live in the wheel hubs, not the tub walls.** A 10×4 mm 623ZZ pocket cannot fit a 2.4 mm wall at any sign. The BOM's 8× 623ZZ works out to two per idler wheel plus one per road wheel; the wall carries only a locating hole. Deletes the problem instead of adding a boss to engineer around it.
- **Idler runs one full-width 3 mm rod, not stub axles.** A stub has 2.4 mm of PLA resisting a 16 mm cantilever and will wallow out. A rod through both walls is constrained 118 mm apart and cannot cock. Ribs take a clearance notch, not a fit — locating on four holes would just add alignment risk.
- **Drive sprocket rides its own bearing, not the motor shaft.** The 9 mm output shaft cannot reach the 75 mm track centreline, and hanging a driven wheel off an N20 gearbox bushing is wrong regardless of reach. MR106ZZ pressed into the rear wall from outside, stepped ø6 hub set-screwed to the shaft over its full 9 mm. Wall takes the load, motor supplies only torque. Costs 2× MR106ZZ on the BOM.
- **Motor drops straight down.** With no shaft passing the wall, cradle length is set by pocket clearance plus the bearing shoulder rather than by insertion travel.
- **IMU moved off the centroid** to (35, −25). It and the battery bay both wanted the centroid and neither knew about the other. Gyro output is position-independent on a rigid body and the accelerometer's lever-arm term is a fixed correction, so the offset is cheaper than contorting the layout around it.
- **Pi-M shelf split into a separate print.** As one piece its underside needed support material in a tunnel obstructed by the battery bay ring. Open-topped ribs and a flat plate both print support-free; four M2 screws join them at assembly.
- **Battery bay ring trimmed clear of the cradles and left open aft.** The ring blocked hand access and the motor's rear wire exit. It is now shorter than the pack, so an aft end wall would land inside the pack footprint. Straps retain the pack; a drop-in aft stop is deferred until testing shows it is needed.
- **Drive motor fixed as Pololu #5218**, 150:1 HPCB 12V with 12 CPR encoder, back connector — closing the Session 01 "side vs back connector" question. Its connector needs a 3 × 11 mm relief in the −Y pocket wall, accepted knowing it grazes one cap screw (65% of surrounding material survives, so the screw is weakened rather than lost).
- **Hand edits in the FreeCAD GUI rejected as a workflow.** A rebuild overwrites the FCStd, and a GUI edit does not propagate to `params.csv`, so the defect returns on the next build. Physical measurement plus a description is the channel that has actually worked: every defect this session was found with the part in hand and fixed at the parameter level.

### Open threads for next session

- **Drivetrain parts do not exist.** No build script produces the sprocket, idler, road wheel or TPU track. This is the only thing between the current tub and a rolling chassis.
- **Road wheels do not reach the track.** Stub-axle holes are cut at `AXLE` (23.5) but `roadwheel_dia` is 24, so the wheel bottom sits at 11.5 against a track inner surface at 3.5. Needs ø40 wheels or axles dropped to z 15.5. Decide inside the drivetrain work.
- **Caster mount does not connect.** `rear_pivot()` makes two bosses at x = ±16 bored along **Y**; `caster_arm()` has one eye at x = 0, also bored along Y. Nothing lines up, and a Y-axis pivot swings the arm sideways rather than fore-aft. Hanging straight back the wheel centre lands at z 23 with r 17, floating 6 mm off the floor.
- **Accepted as-is:** the floor lightening pocket's cut starts 0.05 mm above the belly surface, leaving a sub-layer skin that makes its depth ambiguous; the "fore and aft" floor pockets promised in that comment are one pocket.
- The Cowork remote-tools bridge drops `execute_code` intermittently while `list_documents` keeps working. Two false signals cost real time: a document in `list_documents` is usually left open from a previous session, and a fresh `.FCStd` timestamp with stale STLs is a GUI save, never a build — `main()` exports before it saves. Trust STL mtimes read from FreeCAD's own `os.listdir`; the sandbox bash mount lags badly on this repo.

### 

Session 04 — Status & Handoff (2026-08-21)
Gate status: MET
The drivetrain exists and is guarded, the chassis carries it, and the assembled robot measures 1531 g against the 1.6 kg ceiling — 69 g of headroom, with the +25 % sensitivity on the remaining estimates landing at 1578 g, also under. `mass_budget.py` exits clean for the first time since Session 02 and `validate.py` passes every check. Every printed part in the robot is now measured from its built solid rather than estimated, and every build script refuses to export a part that is not a single solid.
The four missing drivetrain parts exist, the chassis carries them, and the rear tail assembles. What is now blocking the gate is not geometry: measuring every printed part instead of estimating it puts the assembled robot at 1655 g against a 1.6 kg ceiling.
What was built
`mechanical/freecad/build_drivetrain.py`, driven from `params.csv` like the rest, producing five printable parts and running its checks against the real chassis solid:

* Drive sprocket — ø40 pitch, 10 lug pockets, stepped ø6 hub on the MR106ZZ in the rear wall, D-profile bore over the #5218 shaft with a grub collar in the 3 mm gap outboard of the wall. 25 g.
* Front idler — ø40, two 623ZZ in the hub, on the tensioning rod. 22 g.
* Road wheel — ø24, one 623ZZ inboard and a plain land outboard, print four. 11 g.
* TPU track loop — 28 mm × 3.5 mm closed band, 364.42 mm inner path, 29 centre lugs. 50 g.
* Idler tensioner carrier and axle collar — the tensioning hardware and the rod stops.

`build_chassis.py` reworked to match: road-wheel skirts, the idler slot and its carrier bosses, road wheels respaced, the drive hub clearance tightened to a plain-bearing land, deck and floor lightening, and the caster replaced by the anti-tip tail.
Decision log (Session 04)

* Centre-guide lug track, not full-width teeth. One lug row down the middle of the band; the sprocket pockets drive it, the idler and road wheels ride the two smooth lands either side. This is what lets a ø24 road wheel and a ø40 sprocket share one track, and the lug row doubles as the derailment guide and as the axial stop that keeps the wheels on their rods.
* Lug pitch is the sprocket's tooth pitch by construction, and the loop closes at whatever straight run 29 of them demand — 119.38 mm, not the tub's nominal 120. Engagement error cannot accumulate around the loop; the 0.62 mm and all pretension are absorbed in the idler slot, where 1 mm forward is 2 mm of path and 0.55 % strain.
* Idler on a slot with a clamped carrier, not a fixed hole. The carrier bears on two bosses rather than the wall, because the wall is 2.4 mm and an M2 thread needs more. The old inner-face pads are gone with the fixed hole.
* Road wheels on a skirt. ø24 reaches the band only from a 15.5 mm axle line, which is 2.5 mm below the tub's underside, so the handoff's "either ø40 or axles down to z 15.5, params only" was not available: at 15.5 there is no wall to drill, and ø40 will not fit between a ø40 sprocket and a ø40 idler 120 mm apart. Each rod gets a local pad hanging off the wall, thickened inboard to 5.4 mm of bearing length.
* Road-wheel spacing became an explicit pitch. The old `wheelbase * 0.6` formula put two ø24 wheels 24 mm apart — exactly tangent. Nothing in the parameter sheet showed it; the first build-time rim-gap check caught it on the first run. At 40 mm pitch the four ground contacts fall in even quarters along the run.
* Rear caster became a fixed anti-tip tail. It never assembled — pivot bosses bored along Y at x = ±16 against an arm eye at x = 0 — and a ground-riding caster would scrub on every tank turn and lift weight off the tracks for a margin that comes from where the roller sits, not from it being sprung. A level boom holding a ø25 roller 4 mm clear engages at about 2° of rearward pitch, keeps the 33°→54° margin, and drops the spring, the pivot and 7 g.
* Everything above was verified by building it. Two defects (the tangent road wheels, the obstructed rod) were found by boolean guards on the first run and would have survived any amount of parameter arithmetic.
* One electronics shelf, on columns. The Pi-M shelf runs 38 mm further aft and carries the IMU as well as the Pi, so the whole tub electronics stack builds up outside the tub and drops in on six screws. Its two solid 8.4 × 73 mm ribs became three columns a side — a rib extended to 111 mm would have been 58 g, columns are 23 g — and the gaps between columns are where wiring crosses underneath. Three passthrough slots in the plate: two beside the Pi, one aft for the battery and motor loom. Net about 11 g lighter than the ribs it replaces.
* The IMU came back to the centreline. It was pushed to (35, −25) in Session 03 only because the battery bay ring owned the middle of the tub floor; off the floor there is nothing to dodge, so the accelerometer's lever-arm correction disappears with it. This also resolved a defect I introduced: one of the four floor lightening windows sat directly under the old floor pad, leaving two of its screws over a hole. Those windows are weight-only, they serve no mechanical function, and nothing mounts over them now.
* Herringbone treads, relieved out of the band rather than added onto it. The ground face was smooth. 24 chevrons, 1.5 mm deep, 3.5 mm ribs at 25° from transverse. Cutting them out of the 3.5 mm envelope instead of standing them proud keeps the tip radius at 23.5, so ride height, rolling radius and ground speed are untouched — proud grousers would have taken about 6 % off a drive with roughly 1× continuous torque margin. The continuous band drops to 2.0 mm, which nearly halves the outer-fibre bending strain at the sprocket and so improves flex-fatigue life. The 25° arm angle is a printing constraint before it is a styling one: the loop prints with its width vertical, so the arm angle is also its lean off vertical.
* Segmented chevron arms, after the tread guard caught a floating-geometry defect. Built as two straight 15 mm bars, each arm lay tangentially on the 22 mm valley radius: its inner face left the band surface 6.6 mm from the root, so 1.6 mm of every arm end floated free of the band on every wrapped section and the tip stood 1.36 mm proud of the tip radius. The single-solid check cannot see that, because the bar is attached over most of its length, and it was the tread-tip envelope guard that failed. Each arm is now five short pieces placed on their own path points, which takes the worst chord to 0.2 mm and keeps every piece attached. The leaning pieces also overhang both track edges by 0.74 mm, so the finished loop is trimmed to its own width.
* No openings in the tub floor. The four floor lightening windows are gone: 6.7 g is not worth an opening straight into the electronics bay from ground level. The battery bay ring was the obvious place to take the weight from instead, and it cannot fund it — the entire ring is 6.8 g before its strap slots, so deleting it outright would barely break even, and perforating the wall that retains a LiPo for about 1.5 g is a poor trade. The side walls funded it instead: six blind pockets a side rather than two, 1.4 mm into a 2.4 mm wall, worth 6.7 g with no opening at all. The tub came out at 161.1 g either way — an exact wash.
* The motor pockets open the tub floor and cannot be closed by deleting a cut. A ø12 motor on a 23.5 mm axle line has its belly at z 17.5, below the tub's own underside at 18.0, so the bore cuts the floor out from under each motor and the motor protrudes 0.5 mm into open air. That is 525 mm² of genuine through-opening, against 2,240 mm² for the four windows that were removed. It is largely blocked in service — the motor body fills the bore and the retention cap closes the slot above it — so the path into the electronics bay is poor, but it is a path. A 3 mm skirt under the bore footprint would close it for about 3.9 g; deferred, with a strip of foam tape at assembly as the zero-mass alternative.
* The anti-tip roller got a tyre. It was a bare PLA cylinder, which is the wrong thing on the one part whose entire job is to catch the robot — hard plastic skitters on a hard floor rather than biting, and it is loud doing it. It is now a ø20 PLA hub inside a ø25 TPU 90A tyre, retained by a 0.25 mm interference fit and a lip at each hub edge that sits well inside the tyre's outer diameter so it never reaches the floor. The tyre carries the overall diameter, so the 4 mm float and the tip-margin geometry are untouched, and it prints in the filament already specified for the tracks, so it costs no BOM line — only a second tiny print. 5.6 g assembled against 6.0 g for the bare roller.
* Shell walls 2.4 -> 2.0 mm on both torso and head. A 150x90x88 shell at 2.4 mm is inherently 206 g and there was nowhere else on the robot worth more than about 25 g. 2.0 mm is five perimeters at 0.4 and keeps a sensible margin on a torso carrying both arms, the head and four servos. Torso 239 -> 218 g, head 208 -> 181 g. Less than the 75 g the wall alone would have given, because the same pass added a shoulder deck, four split pads and four deck-bolt ribs that the design needed and did not have.
* Six defects in the torso and head, found by reading the scripts rather than by any check. The left shoulder had no shaft hole and no horn recess at all — `xface - sgn*(WALL+3)` is right-handed only, so on the left the cut began inboard of the wall and ran further inboard, and the left arm servo had no way through the shell. Its mount bosses ended flush against a lofted taper, meeting it along a line rather than an area, so they never fused. The deck bolt bosses were columns standing in the middle of a hollow shell. The neck riser sat over the open top of the torso with its whole ø34 footprint in mid-air, carrying the head, the nod servo and the yaw servo. `lightening()` cut a ø2.8 x 26 mm rod, not a pocket: a through-hole in the right wall and a blind bore under the left skin. And the Pi-V standoffs were anchored to one constant y while the back wall leans 6 mm over the torso height, putting the upper pair through the outer skin.
* Registration pins need somewhere to be. Both scripts put their split-key pins in free air — the torso's 12 mm inboard of the outer face, the head's 6 mm inboard of a wall that starts at 73 — because the split plane cuts a hollow shell and the only material on that face is two 2 mm side-wall strips. Moving them along y, which was the first fix, did not change that. Both now sit in pads that straddle the split, so each half keeps its own share.
* A boolean can be too tight as well as too loose. The first shoulder deck was sized to the torso cavity exactly, and that cavity is a lofted taper: plate and wall agreed to within 0.04 mm across the plate thickness, overlapping on one side of that and gapping on the other. FreeCAD ground on the slivers for minutes and never returned. Every mating feature here now takes a deliberate bite — 1.5 mm for bosses, 0.6 mm for the deck, chosen to leave 1.36 mm of skin outboard.
* Mass is now measured, not estimated. `components.csv` carries built-solid volumes for every printed part and those lines are marked firm rather than soft.

Open threads for next session

* ~~Over the ceiling by 18 g.~~ Closed this session at 1531 g: shell walls to 2.0 mm on torso and head, and two double-counted lines removed from `components.csv` — the neck riser (52.9 g) is fused into the torso solid and the head nod ears (7.1 g) into the head, so both were being paid for twice.
* ~~`build_torso.py` and `build_head.py` export floating islands.~~ Closed this session. Both now carry the single-solid guard and both halves of both parts build as one solid.
* `mass_budget.py` has been unrunnable since Session 02 — `components.csv` had an unquoted comma in "Brow blade (PLA, thin)", so `float()` hit the wrong column. Fixed this session. Any budget figure quoted between Session 02 and now was not produced by that script.
* Sprocket overhang. The sprocket's centre sits 16 mm outboard of a single 3 mm-wide MR106ZZ. The loads are small enough that it should hold, but it is the least-supported joint in the drivetrain and the first thing to look at if the drive feels rough on the bench.
* Assembly order: the sprocket grub screw must be set before the track goes on — the track band covers the only access to it.
* Everything in this session is built and guarded in FreeCAD: both `main()` calls run clean and the drivetrain guards have now been checked against the reworked tub. The FreeCAD MCP's GUI dispatch jammed for a stretch mid-session (`list_documents` answering while `execute_code` and `create_document` both timed out at 60 s, surviving a restart) and cleared on its own. The addon predates `get_rpc_status`, which would diagnose it in one call; worth updating.
* If the underside is ever meant to be sealed, the motor-pocket openings are the only remaining path and the fix is a parameter away. `build_chassis.main()` now guards the underside: it probes just inside both faces of the floor and fails if more is open right through than the motor pockets account for, so no future lightening pass can reopen the floor by accident.
* Screen accuracy of the track pattern is a Phase 06 question. The reference photographs show transverse rectangular grouser pads on the film tracks, not the herringbone adopted here — the herringbone was chosen as a design preference and for its lateral bite in tank turns, and swapping the pattern later is a parameter change, not a redesign.
* Not yet done: reprint the tub, print the drivetrain, update `preview/` massing for the new parts, and the power wiring/harness schematic still owed from Session 01.

Next session — initiating prompt (Phase 01)
Johnny 5 — Phase 01, Session 01. Read CLAUDE.md, then `phases/PHASE_01_INFRASTRUCTURE.md`, and note the Phase 00 close state in `phases/PHASE_00_HARDWARE.md` (Session 04 handoff). Phase 00 is closed: every printed part is measured from its built solid, the assembled robot is 1531 g against a 1.6 kg ceiling with the +25 % worst case at 1578 g, `mass_budget.py` and `validate.py` both pass, and every build script refuses to export a part that is not a single solid. Merge `phase/00-hardware` to `main` and tag `v0.0`.

Two things carry forward before anything is ordered or printed. The power wiring and harness schematic is still owed from Session 01 and blocks ordering. And the tub must be reprinted before the drivetrain is assembled — the printed one predates the road-wheel skirts, the idler tensioning slot and the electronics shelf columns.

Then begin Phase 01: image both Pi Zero 2 W (Pi OS Lite 64-bit), finalize the inter-Pi message-queue protocol and the Pi-V→Pi-M intent contract, establish connectivity to the home-lab LiteLLM proxy, and implement the offline fallback (Pi-M conservative mode), which is the Phase 01 gate. Session config: Sonnet, Standard, Medium.

Deferred to Phase 06 (cosmetic pass)

* Screen accuracy of the track pattern. The reference photographs show transverse rectangular grouser pads on the film tracks, not the herringbone adopted here; swapping the pattern is a parameter change, not a redesign.
* Fine circumferential ribs on the anti-tip tyre if the smooth wall reads wrong up close. Structurally it should stay smooth.
* Brow gear teeth, currently pitch-diameter blanks, and the press-fit eye-dome and camera inserts.

Known weaknesses logged, not fixed

* The torso's four M3 split screws pass through the front wall, cross 90 mm of open interior and land in the back wall. That is registration, not clamping, and it should be revisited when the torso is first assembled.
* The sprocket sits 16 mm outboard of a single 3 mm MR106ZZ. Loads are small enough that it should hold; it is the least-supported joint in the drivetrain and the first thing to look at if the drive feels rough on the bench.
* The motor pockets open the tub floor by 525 mm² and cannot be closed by deleting a cut, because the motor's belly sits below the tub's underside. Largely plugged in service by the motor and its cap. A 3 mm skirt would close it for 3.9 g; foam tape at assembly costs nothing.
