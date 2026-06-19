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

### Gate status: NEAR-COMPLETE

Body baselined in FreeCAD as **parametric Python source** (Task 7). Geometry validated (20/20 checks); STL/FCStd generation is the one remaining mechanical action and runs on Andrew's FreeCAD 1.1.1 (`freecadcmd build_*.py`) — the sandbox has no FreeCAD. Once STLs are generated and eyeballed in the GUI, the Phase 00 gate is fully met.

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

### Next session — initiating prompt (Phase 00 close / Phase 01 start)

> Johnny 5 — Phase 00 close. Read CLAUDE.md, `phases/PHASE_00_HARDWARE.md` (Session 02 handoff), and `BOM.md`. The body is baselined as parametric FreeCAD source in `mechanical/`. First confirm the git commit landed, then run `freecadcmd build_*.py` to export STLs and review them in FreeCAD for interferences. Remaining mechanical detail: brow gear teeth, eye/camera inserts, drivetrain + caster parts, and the power harness schematic. Then close the Phase 00 gate and open Phase 01 (infrastructure). Session config: Opus, Extended, High.
