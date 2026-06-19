# Johnny 5 — Bill of Materials (Phase 00)

**Status:** Approved by Andrew, 2026-06-17. BOM half of the Phase 00 gate is met.
**Target:** Floor-roaming, ~38–42 cm tall, assembled-weight ceiling **1.6 kg**.
**Battery architecture:** Single 2S LiPo, three rails (motor battery-direct, regulated 5V, regulated 6V).

Costs are estimates in USD, parts only, excluding shipping and items Andrew already owns.

---

## 1. Tread Drive

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| Drive gearmotor | 150:1 Micro Metal Gearmotor HPCB 12V w/ 12 CPR encoder (N20-class, 12 mm) | 2 | $46 | Pololu — confirm side vs back connector variant. ~1800 counts/output-rev. Run battery-direct at ~7.4 V (≈62% of 12 V rating). |
| Motor driver | TB6612FNG dual H-bridge breakout | 1 | $7 | SparkFun ROB-14451 or equiv. 3.3 V logic; VM from 2S pack. STBY → Pi-M GPIO (defaults off). |
| Treads | Printed TPU tank treads, Shore 90A | — | (filament) | Track width 28 mm. 90A chosen for flex-fatigue life + grip (direct-drive Sprite Pro removes the printability constraint). Revisit toward 95A if Task 7 adopts segmented rigid-link treads. |
| Sprockets / idlers | Printed PLA/PETG | — | (filament) | Drive sprocket pitch dia 40 mm. |
| Bearings | 623ZZ (3×10×4) for idlers/road wheels | 8 | $5 | Generic. |
| Rear trailing caster | Swiveling sprung caster, ~34 mm wheel, ~90 mm trail | 1 | $5 | Passive fore-aft stabilizer; raises rearward/incline tip margin 33°→54°. Printed arm + wheel, preload spring, pivot pins. Swivels to avoid scrub on tank turns. Added Session 02. |

## 2. Arms & Head Servos

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| Serial bus servo | Feetech SCS0009 (6V, 2.3 kg·cm stall, 0.75 kg·cm rated, 1 Mbps) | 6 | $66 | L shoulder, R shoulder, head yaw, head nod, shoulder utility-box tilt, brow-blade roll. Chain on one bus. (5th = head nod, 6th = articulated brow; both added Session 02, mass-budget approved.) |
| Bus adapter | Waveshare Bus Servo Adapter (A) — SC/ST half-duplex UART | 1 | $8 | WS-25514. Pi-M UART ↔ bus; reads angle/load/voltage. Fed from 6V servo rail. |

Arm design budget: ≤50 g and ≤90 mm effective lever per arm (keeps shoulder load within rated torque). Utility box mounts to torso shoulder structure (own servo, does not load arm servos). Bus reserves IDs for future elbow servos. STS3215 (19.5 kg·cm, native 7.4 V) documented as upgrade lever if arms lack authority — costs ~+140 g against the weight ceiling.

## 3. Sensing

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| ToF distance | VL53L1X carrier, 400 cm, regulated + level-shifted | 1 | $13 | Pololu #3415. I²C 0x29. XSHUT → Pi-M GPIO. |
| IMU | MPU-6050 (GY-521) | 1 | $4 | I²C 0x68. 3.3 V. |

## 4. Audio (all on Pi-V)

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| Microphone | INMP441 I²S MEMS mic | 1 | $5 | 3.3 V. L/R → GND. |
| Amplifier | MAX98357A I²S class-D | 1 | $6 | 5 V. SD_MODE sets gain/channel. |
| Speaker | 8 Ω, 3 W | 1 | $4 | Placed away from mic. |

Integration dependency (Phase 01): mic + amp share the I²S bus; stock `max98357a` / `googlevoicehat` overlays conflict — a **custom combined `simple-audio-card` overlay** is required (one CPU DAI, two codec DAIs). Half-duplex turn-taking; mic gated during playback (Phase 04). No AEC in V1.

## 5. Expressive LEDs & Light

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| Mouth array | WS2812B 8-pixel stick | 1 | $5 | **Pi-V**, SPI (GPIO10). Center-out animation during speech. |
| Eye pixels | WS2812B single | 2 | $2 | **Pi-M**. Expression + status color. Diffuser behind each. |
| Battery gauge | WS2812B 5-pixel strip | 1 | $3 | **Pi-M**. Green→yellow→red by charge. |
| Navigation light | 1 W neutral-white LED + lens | 1 | $3 | **Pi-V**, GPIO13 PWM via MOSFET. Camera aid in dim rooms. |
| MOSFET | Logic-level N-ch (nav light) | 1 | $1 | e.g., AO3400 module. |
| Level shifter | 74AHCT125 (3.3→5 V WS2812B data) | 2 | $2 | One per data line (Pi-M chain, Pi-V mouth). |
| Battery-sense ADC | ADS1115 16-bit I²C ADC + divider | 1 | $5 | **Pi-M** I²C 0x48. Drives gauge, low-voltage cutoff, telemetry. |

Pi-M LED groups (eyes + gauge + status) chain on one SPI data line. WS2812B on SPI, not PWM, because PWM channels are taken by the motors.

## 6. Power

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| Battery | 2S LiPo 2200 mAh, ≥10C, XT60 | 1 | $18 | ~7.4 V nom / 8.4 V full. ~60–90 min runtime. ~130 g. |
| Buck converter | Adjustable synchronous, 5 A | 2 | $16 | One set 5.0 V (compute), one set 6.0 V (servos). |
| Master switch | SPST toggle/rocker, ≥10 A | 1 | $3 | Main positive, after fuse. |
| Fuse + holder | Inline blade, 7.5 A | 1 | $3 | LiPo short/overcurrent protection. |
| Connectors / wire | XT60 pair, silicone 18–20 AWG | — | $6 | |
| Capacitor bank | 1000 µF electrolytic + assorted ceramic | 3+ | $5 | One per rail + across motor VM. Star ground. |
| Distribution board | Perfboard / PDB | 1 | $3 | |
| Balance charger | 2S LiPo balance charger | 1 | $25 | Off-board accessory. Skip if owned. |

Servos **must** be regulated (6 V) — 8.4 V full-charge exceeds the SCS0009 7.4 V max. Motors are 12 V-rated, so battery-direct is safe and keeps motor transients off the compute rail.

## 7. Compute & Mechanical (mostly owned)

| Part | Spec | Qty | Est. cost | Supplier / notes |
|---|---|---|---|---|
| SBC | Raspberry Pi Zero 2 W | 2 | owned | Pi-M (motion), Pi-V (vision). |
| microSD | — | 2 | owned | |
| Camera | 8 MP 1080p CSI | 1 (2 owned) | owned | On Pi-V head; one spare. |
| Filament — PLA | Shell prototyping | — | ~$20 | Likely owned. |
| Filament — PETG | Stress-bearing parts | — | ~$25 | |
| Filament — TPU | Treads, Shore 90A | — | ~$25 | Polymaker PolyFlex TPU90, NinjaTek Cheetah (95A) or Armadillo as firmer fallback. Dry before printing; enable pressure advance. |
| Fasteners | M2/M3 screws, heat-set inserts | — | $15 | |

**Estimated new-spend total: ~$325–365** (excl. owned items, incl. balance charger; includes 5th + 6th servos and rear trailing caster).

---

## GPIO Pin Map — Pi-M (Motion)

40-pin header, 3.3 V logic.

| Function | GPIO (BCM) | Notes |
|---|---|---|
| I²C1 SDA / SCL | 2 / 3 | VL53L1X 0x29, MPU-6050 0x68, ADS1115 0x48 |
| Servo bus UART TXD / RXD | 14 / 15 | → Bus Servo Adapter (A) |
| Motor PWMA / PWMB | 12 / 13 | Hardware PWM0 / PWM1 |
| Motor AIN1 / AIN2 | 5 / 6 | Motor 1 direction |
| Motor BIN1 / BIN2 | 16 / 26 | Motor 2 direction |
| Motor STBY | 20 | Pull-down → motors off on boot/crash |
| Encoder M1 A / B | 17 / 27 | Quadrature |
| Encoder M2 A / B | 22 / 23 | Quadrature |
| VL53L1X XSHUT / INT | 24 / 25 | Reset control / optional interrupt |
| WS2812B chain (eyes+gauge+status) | 10 | SPI0 MOSI, via level shifter |

## GPIO Pin Map — Pi-V (Vision)

40-pin header, 3.3 V logic.

| Function | GPIO (BCM) | Notes |
|---|---|---|
| CSI camera | (ribbon) | Not GPIO |
| I²S BCLK / LRCLK | 18 / 19 | PCM clock / frame-sync (shared) |
| I²S DIN (mic SD) | 20 | INMP441 → Pi |
| I²S DOUT (amp DIN) | 21 | Pi → MAX98357A |
| WS2812B mouth array | 10 | SPI0 MOSI, via level shifter |
| Navigation light | 13 | Hardware PWM → MOSFET gate |

Inter-Pi messaging runs over the WiFi LAN (message queue, protocol finalized Phase 01); no GPIO cross-link reserved (Pi-M UART is committed to the servo bus). Optional GPIO UART cross-link deferred.

---

## Power Budget

| Load | Rail | Typical | Peak |
|---|---|---|---|
| 2× drive motor | Battery-direct ~7.4 V | 0.4 A | ~2.0 A |
| 2× Pi Zero 2 W | 5 V | 0.4 A | 0.8 A |
| WS2812B LEDs (mouth/eyes/gauge) | 5 V | 0.1 A | 0.5 A |
| Navigation light (1 W) | 5 V | — | 0.3 A |
| MAX98357A amp | 5 V | 0.1 A | 1.0 A |
| Sensors (ToF/IMU/ADC) | 3.3 V / 5 V | 0.03 A | 0.05 A |
| 6× SCS0009 servo | 6 V | 0.6 A | ~3.0 A |

Rail sizing: 5 V buck ≥5 A (peak ~2.6 A + headroom); 6 V buck (peak ~3.0 A with 6 servos, within the 5 A buck already specified); motor rail peak ~2 A. Battery-side average ~1.2 A.

---

## Decisions, Levers & Open Items

**Locked this session**

- Path A drive: N20-class 12V/150:1 encoder motors + TB6612FNG, battery-direct on 2S. Accepts ~0.13 m/s and ~1× continuous torque margin in exchange for compact, light, cheap, clean-logic drive.
- 6× SCS0009 on one bus (utility-box tilt + head nod + brow-blade roll). Head is yaw+nod with articulated twin brow blades (offset outboard pivots, one servo driving a pinion → left gear direct, → right gear via an idler so the blades mirror; roll-only, 3 poses). All extra servos share the half-duplex bus (new IDs, no extra GPIO); the 6 V rail at ~3 A stays within the 5 A buck. Arms held light to stay in rated torque.
- All audio consolidated on Pi-V (frees Pi-M I²S pins).
- Custom LED layout: mouth (Pi-V), eyes + battery gauge + status (Pi-M).
- Three-rail power; fuse + STBY interlock + ADS1115 voltage monitoring added for safety.

**Deferred levers (not in V1 spend)**

- Motor-rail boost to ~9–10 V if bench testing shows the drive underpowered.
- STS3215 servo upgrade if arms lack authority.
- 25D-class motors + higher-current driver if Path A proves inadequate (Path B).
- **V2 grasping (tendon gripper):** single-actuator underactuated 3-finger claw with synchronous tendon routing (one winch servo + return spring, à la Yale OpenHand "Model M"). V1 arms built grip-ready — tendon channel up the forearm, claw anchor boss, cable path crossing the shoulder pitch axis, plus a reserved bus ID and a torso winch-servo mount pad — so V2 is a bolt-on, not a redesign. Investigated multiplexing the joints onto one multi-tendon actuator (SIMO clutch banks / SISO time-division); rejected for V1 because independent simultaneous joint motion is needed for Phase 04 and the only one-motor-many-tendon hardware is research-grade. Decided Session 02.
- **Smart-servo standard alt:** Dynamixel XL330-M288 (~18 g, ~5.3 kg·cm, current-based compliant control) if the servo bus is ever re-worked. Different protocol/bus from the Feetech adapter, so not mixable — a clean-sheet swap, not an incremental add.
- **V2 powered waist (body lean):** the signature J5 fore-aft lean at the base-to-torso pivot. Rejected for V1 — needs an STS3215-class servo or a self-locking lead-screw (SCS0009 can't hold the 531 g upper body: ~5.4 kg·cm demanded vs 2.3 kg·cm stall), adds ~116 g pushing worst-case weight to ~1662 g (over the 1.6 kg ceiling), puts the 6 V rail at ~4.5 A near the buck limit, and costs ~+$26, all for only ~7° of decline margin not needed indoors. Its value is expression, not stability. V1 base-to-torso interface built **lean-ready** (reserved pivot-axle bosses + actuator mount pad) so it's a bolt-on, not a redesign. Decided Session 02; rear trailing caster covers the incline/rearward case passively instead.

**Open items**

- Pin exact Pololu motor connector variant (side/back) at order.
- Confirm TPU tread + sprocket geometry in FreeCAD (Task 7).
- Phase 01: custom `simple-audio-card` overlay for mic + amp coexistence.

---

## Gate Condition Status

**Partial — BOM met, body outstanding.** BOM approved by Andrew 2026-06-17. FreeCAD body baseline (Task 7) is the remaining gate item. Full gate is met when the body is baselined in FreeCAD 1.1.1. Ordering and printing hold until then.
