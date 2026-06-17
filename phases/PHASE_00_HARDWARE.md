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
