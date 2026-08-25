# Power Wiring and Harness — Johnny 5

Companion document to `docs/diagrams/power_harness_schematic.svg`. Together they are the
formal power and harness definition for the whole robot, from the XT60 pack lead to every
load, and they close blocker B5. Nothing in the power architecture should be ordered
against anything else.

The drawing is the picture; this file is the data. Where a figure appears in both, this
file is the one `scripts/check_harness_nets.py` parses, and the guard asserts that the two
carry the same set of net names.

---

## 1. Architecture

One 2S LiPo feeds one fused, switched trunk into a distribution board that carries the star
ground and three rails. The motor rail is battery-direct, roughly 7.4 V nominal and 8.4 V at
full charge, and goes only to the TB6612FNG VM pin, so motor transients never reach anything
else. A 5 V synchronous buck carries both Pi Zero 2 W units, both WS2812B strings with their
level shifters, the MAX98357A amplifier and the navigation light. A 6 V synchronous buck
carries the Waveshare Bus Servo Adapter and through it all six SCS0009 servos; the servos are
regulated rather than battery-direct because 8.4 V exceeds the SCS0009 7.4 V maximum and would
damage them on a freshly charged pack.

Two derived 3.3 V supplies come from the Pi header pins rather than from a converter. Pi-M's
3.3 V pin carries the I²C sensors, both motor encoders and the TB6612 logic supply, which is
what keeps every logic and encoder output GPIO-safe. Pi-V's 3.3 V pin carries the INMP441
microphone.

The fuse sits between the pack and the master switch, so the switch itself is protected. The
switch is the only thing between a charged pack and a live harness, and everything downstream
of it, telemetry included, is dead when it is open.

## 2. Reading the drawing

Power conductors are drawn thick and solid and coloured by rail: orange for battery-direct
VBAT, red for 5 V, purple for 6 V, pink for the two derived 3.3 V supplies, black for ground.
Signal conductors are drawn thin and dashed in slate. A filled dot is a junction; two
conductors crossing without a dot are not connected.

Ground is drawn as a bus in the lower band and as ground symbols in the upper band. Both mean
the same thing: every return lands on one star point on the distribution board. The symbols
are used where a routed line would have to cross most of the drawing to say the same thing.

## 3. Net table

Net names carry their rail as a prefix. `VBAT_`, `5V_`, `6V_`, `3V3M_` and `3V3V_` are rails;
`SIG_`, `OUT_` and `GND_` are not. Every rail-prefixed net declares either `[peak N A]`, the
worst-case current that net carries, or `[reflected]`, meaning it is an inter-rail feed whose
current is accounted for on the rail it supplies rather than on the rail it draws from. The
guard rejects a rail-prefixed net that declares neither, so a forgotten figure fails loudly
instead of summing to zero.

Passive components are properties of the net they sit in rather than endpoints of their own.
A series resistor or a bulk capacitor does not terminate a conductor, and modelling them as
endpoints would have forced an exemption into the endpoint check. Their values are called out
in the Notes column and every value is a line item in `BOM.md` section 6.

Where a net reaches more than one device, the endpoints are separated by a plus sign, so that a
comma inside a single endpoint stays unambiguous to a reader and to the guard.

Conductor lengths are not specified. The harness is cut to fit at assembly; the build order in
section 7 says when.

| Net | Source | Destination | Gauge | Connector | Notes |
|---|---|---|---|---|---|
| VBAT_PACK | Battery XT60 (+) | Fuse holder, line side | 18 AWG silicone | XT60 pair | [reflected] The only conductor upstream of the fuse. Keep it as short as the battery bay allows. |
| VBAT_FUSED | Fuse holder, load side | Master switch, terminal 1 | 18 AWG silicone | 6.35 mm insulated spade | [reflected] 7.5 A inline blade fuse. Fuse before switch, so a switch fault is also protected. |
| VBAT_SW | Master switch, terminal 2 | Distribution board VBAT pad | 18 AWG silicone | 6.35 mm insulated spade | [reflected] Everything downstream is dead with the switch open. |
| VBAT_VM | Distribution board VBAT pad | TB6612 VM | 18 AWG silicone | soldered to breakout pad | [peak 2.00 A] 1000 µF electrolytic plus 0.1 µF ceramic across VM to GND at the breakout. Electrolytic polarity is critical. |
| VBAT_BUCK5_IN | Distribution board VBAT pad | Buck converter (5 V) IN+ | 18 AWG silicone | screw terminal | [reflected] Set the output to 5.0 V on the bench before any load is connected. |
| VBAT_BUCK6_IN | Distribution board VBAT pad | Buck converter (6 V) IN+ | 18 AWG silicone | screw terminal | [reflected] Set the output to 6.0 V on the bench before any servo is connected. |
| VBAT_SENSE | Distribution board VBAT pad | ADS1115 sense divider, 100 kΩ upper leg | 26 AWG | soldered on the distribution board | [peak 0.00 A] 57 uA at 8.4 V. Downstream of the switch, so telemetry reads zero when the robot is off, which is intended. |
| 5V_PI_M | Buck converter (5 V) OUT+ | Pi-M 5 V (pin 2) | 20 AWG silicone | 2-pin JST-XH 2.54 | [peak 0.40 A] 1000 µF electrolytic across the 5 V rail at the distribution board. |
| 5V_PI_V | Buck converter (5 V) OUT+ | Pi-V 5 V (pin 2) | 20 AWG silicone | 2-pin JST-XH 2.54 | [peak 0.40 A] Runs up through the torso. Keep it clear of the servo bus cable. |
| 5V_LED_M | Distribution board 5 V pad | WS2812B eye pixels and battery gauge + 74AHCT125 (Pi-M) VCC | 22 AWG | 3-pin JST-XH 2.54 (5 V, DIN, GND) | [peak 0.23 A] Seven pixels, two eyes plus a five-pixel gauge. 0.1 µF ceramic at the shifter VCC. |
| 5V_LED_V | Distribution board 5 V pad | WS2812B mouth array + 74AHCT125 (Pi-V) VCC | 22 AWG | 3-pin JST-XH 2.54 (5 V, DIN, GND) | [peak 0.27 A] Eight pixels. 0.1 µF ceramic at the shifter VCC. |
| 5V_AMP | Distribution board 5 V pad | MAX98357A VIN | 22 AWG | 2-pin JST-XH 2.54 | [peak 1.00 A] Largest transient on the rail. 0.1 µF ceramic at the amplifier. |
| 5V_NAVLIGHT | Distribution board 5 V pad | Navigation light LED module, anode | 22 AWG | 2-pin JST-XH 2.54 | [peak 0.30 A] Switched on the low side. The module carries its own current-setting resistor. |
| 6V_SERVO_BUS | Buck converter (6 V) OUT+ | Waveshare Bus Servo Adapter V+ | 18 AWG silicone | screw terminal | [peak 3.00 A] 1000 µF electrolytic at the adapter input. Never battery-direct: 8.4 V exceeds the SCS0009 7.4 V maximum. |
| 3V3M_SENSORS | Pi-M 3.3 V (pin 1) | VL53L1X VIN + MPU-6050 VCC + ADS1115 VDD | 26 AWG | 4-pin JST-XH 2.54 per device | [peak 0.05 A] Three devices on one supply and one I²C bus. |
| 3V3M_ENC | Pi-M 3.3 V (pin 17) | Drive gearmotor left encoder Vcc + Drive gearmotor right encoder Vcc | 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | [peak 0.02 A] 3.3 V so both encoder outputs are GPIO-safe. |
| 3V3M_TB_VCC | Pi-M 3.3 V (pin 17) | TB6612 VCC | 26 AWG | soldered to breakout pad | [peak 0.01 A] Logic supply only. 5 V here would damage Pi-M GPIO, and the TB6612 reverse protection covers VM, not VCC. |
| 3V3V_MIC | Pi-V 3.3 V (pin 1) | INMP441 VDD | 26 AWG | 5-pin JST-XH 2.54 | [peak 0.01 A] L/R strapped to GND for the left channel. |
| GND_BATT | Battery XT60 (-) | Distribution board star ground | 18 AWG silicone | XT60 pair | The star point is the only place returns meet. |
| GND_MOTOR | TB6612 GND | Distribution board star ground | 18 AWG silicone | soldered to breakout pad | Own conductor, so motor return never shares a path with logic return. |
| GND_SERVO | Waveshare Bus Servo Adapter GND | Distribution board star ground | 18 AWG silicone | screw terminal | Own conductor, for the same reason. |
| GND_BUCK5 | Buck converter (5 V) IN- and OUT- | Distribution board star ground | 18 AWG silicone | screw terminal | Input and output returns are common inside the module. |
| GND_BUCK6 | Buck converter (6 V) IN- and OUT- | Distribution board star ground | 18 AWG silicone | screw terminal | Input and output returns are common inside the module. |
| GND_PI_M | Pi-M GND (pin 6) | Distribution board star ground | 20 AWG | in the 5V_PI_M connector shell | Pi-M power return. |
| GND_PI_V | Pi-V GND (pin 6) | Distribution board star ground | 20 AWG | in the 5V_PI_V connector shell | Pi-V power return. |
| GND_SIG_M | Pi-M GND (pin 9) | TB6612 GND + VL53L1X GND + MPU-6050 GND + ADS1115 GND | 26 AWG | in each device connector shell | Signal return local to Pi-M. Reaches the star through GND_PI_M. |
| GND_ENC | Drive gearmotor left encoder GND + Drive gearmotor right encoder GND | Pi-M GND (pin 14) | 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | Encoder return follows its signal pair back to the Pi, not to the motor return. |
| GND_LED_M | WS2812B eye pixels and battery gauge + 74AHCT125 (Pi-M) GND | Distribution board star ground | 22 AWG | in the 5V_LED_M connector shell | |
| GND_LED_V | WS2812B mouth array + 74AHCT125 (Pi-V) GND | Distribution board star ground | 22 AWG | in the 5V_LED_V connector shell | |
| GND_AMP | MAX98357A GND | Distribution board star ground | 22 AWG | in the 5V_AMP connector shell | |
| GND_NAV | MOSFET source | Distribution board star ground | 22 AWG | 2-pin JST-XH 2.54 | Low-side switch return. |
| GND_MIC | INMP441 GND | Pi-V GND (pin 9) | 26 AWG | in the INMP441 connector shell | |
| OUT_MOT_L | TB6612 AO1, AO2 | Drive gearmotor left, M1 and M2 | 22 AWG to the connector, 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | Bench-verified crossover: RED to AO2, BLK to AO1. Recorded 2026-07-12 in `simulation/chassis/TUNING.md`. Do not undo it in software; `MotorDriver` stays at `invert_*=False`. |
| OUT_MOT_R | TB6612 BO1, BO2 | Drive gearmotor right, M1 and M2 | 22 AWG to the connector, 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | RED to BO1, BLK to BO2, uncrossed. |
| OUT_SERVO_BUS | Waveshare Bus Servo Adapter servo port | SCS0009 servo chain, six units daisy-chained | 22 AWG in the supplied 3-wire lead | Feetech 3-pin 1.25 mm | 6 V, GND and half-duplex data in one chain. IDs 1 to 6: left shoulder, right shoulder, head yaw, head nod, utility-box tilt, brow roll. |
| OUT_SPK | MAX98357A OUT+ and OUT- | Speaker | 22 AWG | 2-pin JST-PH 2.0 | Bridge-tied output. Neither leg is ground. Tying the minus leg to the star will damage the amplifier. |
| OUT_NAV_LED | Navigation light LED module, cathode | MOSFET drain | 22 AWG | 2-pin JST-XH 2.54 | Switched on the low side so the gate stays referenced to Pi-V ground. |
| OUT_SENSE_TAP | ADS1115 sense divider midpoint, 100 kΩ over 47 kΩ | ADS1115 A0 | 26 AWG | soldered on the distribution board | 8.4 V divides to 2.685 V, inside both the 3.3 V VDD and the 4.096 V full-scale range. 0.1 µF ceramic across the 47 kΩ leg. |
| OUT_LED_M_DATA | 74AHCT125 (Pi-M) Y1 | WS2812B eye pixels and battery gauge, DIN | 24 AWG | in the 5V_LED_M connector shell | 330 Ω in series at the shifter output. |
| OUT_LED_V_DATA | 74AHCT125 (Pi-V) Y1 | WS2812B mouth array, DIN | 24 AWG | in the 5V_LED_V connector shell | 330 Ω in series at the shifter output. |
| SIG_PWMA | Pi-M GPIO12 (pin 32) | TB6612 PWMA | 26 AWG | 2.54 mm IDC or Dupont | Hardware PWM0, about 20 kHz. |
| SIG_AIN1 | Pi-M GPIO5 (pin 29) | TB6612 AIN1 | 26 AWG | 2.54 mm IDC or Dupont | Left channel direction. |
| SIG_AIN2 | Pi-M GPIO6 (pin 31) | TB6612 AIN2 | 26 AWG | 2.54 mm IDC or Dupont | Left channel direction. |
| SIG_PWMB | Pi-M GPIO13 (pin 33) | TB6612 PWMB | 26 AWG | 2.54 mm IDC or Dupont | Hardware PWM1, about 20 kHz. |
| SIG_BIN1 | Pi-M GPIO16 (pin 36) | TB6612 BIN1 | 26 AWG | 2.54 mm IDC or Dupont | Right channel direction. |
| SIG_BIN2 | Pi-M GPIO26 (pin 37) | TB6612 BIN2 | 26 AWG | 2.54 mm IDC or Dupont | Right channel direction. |
| SIG_STBY | Pi-M GPIO20 (pin 38) | TB6612 STBY | 26 AWG | 2.54 mm IDC or Dupont | 100 kΩ pull-down to the star fitted at the TB6612 end. Motors are off on boot, after a crash and whenever the GPIO floats. This is the primary fail-safe. |
| SIG_ENC_L_A | Drive gearmotor left encoder A, yellow | Pi-M GPIO17 (pin 11) | 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | |
| SIG_ENC_L_B | Drive gearmotor left encoder B, white | Pi-M GPIO27 (pin 13) | 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | |
| SIG_ENC_R_A | Drive gearmotor right encoder A, yellow | Pi-M GPIO23 (pin 16) | 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | Bench-verified crossover: A and B are swapped on this motor only, recorded 2026-07-12 in `simulation/chassis/TUNING.md`. The `BOM.md` pin map entry "Encoder M2 A/B = 22/23" names the Pi-side channel pair, not the wire colours. |
| SIG_ENC_R_B | Drive gearmotor right encoder B, white | Pi-M GPIO22 (pin 15) | 28 AWG in the supplied motor cable | 6-pin JST SH 1.0 mm | Second half of the crossover above. |
| SIG_I2C_SDA | Pi-M GPIO2 (pin 3) | VL53L1X SDA + MPU-6050 SDA + ADS1115 SDA | 26 AWG | 4-pin JST-XH 2.54 per device | One bus, three addresses: 0x29, 0x68, 0x48. |
| SIG_I2C_SCL | Pi-M GPIO3 (pin 5) | VL53L1X SCL + MPU-6050 SCL + ADS1115 SCL | 26 AWG | 4-pin JST-XH 2.54 per device | Bus pull-ups are on the carrier boards. |
| SIG_TOF_XSHUT | Pi-M GPIO24 (pin 18) | VL53L1X XSHUT | 26 AWG | in the VL53L1X connector shell | Reset control. Held low keeps the sensor off the bus. |
| SIG_TOF_INT | Pi-M GPIO25 (pin 22) | VL53L1X INT | 26 AWG | in the VL53L1X connector shell | Optional data-ready interrupt. Fit the wire even if unused. |
| SIG_SERVO_TX | Pi-M GPIO14 (pin 8) | Waveshare Bus Servo Adapter RXD | 26 AWG | 2.54 mm IDC or Dupont | PL011 on /dev/serial0. `dtoverlay=disable-bt` must be present in /boot/firmware/config.txt or this lands on the mini-UART and drifts with CPU frequency. |
| SIG_SERVO_RX | Pi-M GPIO15 (pin 10) | Waveshare Bus Servo Adapter TXD | 26 AWG | 2.54 mm IDC or Dupont | Half-duplex bus; the adapter handles direction. |
| SIG_LED_M_DATA3V3 | Pi-M GPIO10 (pin 19) | 74AHCT125 (Pi-M) A1 | 26 AWG | 2.54 mm IDC or Dupont | SPI0 MOSI. Shifter OE1 to GND; unused inputs to GND and unused OE pins to VCC. |
| SIG_I2S_BCLK | Pi-V GPIO18 (pin 12) | INMP441 SCK + MAX98357A BCLK | 26 AWG | in each device connector shell | Shared bit clock, one CPU DAI and two codec DAIs. |
| SIG_I2S_LRCLK | Pi-V GPIO19 (pin 35) | INMP441 WS + MAX98357A LRC | 26 AWG | in each device connector shell | Shared frame sync. |
| SIG_I2S_DIN | Pi-V GPIO20 (pin 38) | INMP441 SD | 26 AWG | in the INMP441 connector shell | Microphone into the Pi. |
| SIG_I2S_DOUT | Pi-V GPIO21 (pin 40) | MAX98357A DIN | 26 AWG | in the MAX98357A connector shell | Pi into the amplifier. |
| SIG_LED_V_DATA3V3 | Pi-V GPIO10 (pin 19) | 74AHCT125 (Pi-V) A1 | 26 AWG | 2.54 mm IDC or Dupont | SPI0 MOSI. Same shifter tie-off as the Pi-M side. |
| SIG_NAV_PWM | Pi-V GPIO13 (pin 33) | MOSFET gate | 26 AWG | 3-pin JST-XH 2.54 | Hardware PWM to a logic-level gate. The module carries its own gate pull-down. |

---

## 4. Per-rail current summary, reconciled against BOM.md

Peak column is the sum of the `[peak N A]` tags on that rail's nets. Budget column is the sum
of the matching rows in the `BOM.md` Power Budget. Rating is the converter or protection
rating stated in `BOM.md` section 6.

| Rail | Nets summed | Peak from net table | BOM Power Budget | Rating | Source of the rating |
|---|---|---|---|---|---|
| VBAT (battery-direct, 7.4 V nom) | 2 | 2.00 A | 2.0 A | 7.5 A | Inline blade fuse, section 6 |
| 5 V | 6 | 2.60 A | 2.6 A | 5 A | Buck converter, section 6 |
| 6 V | 1 | 3.00 A | 3.0 A | 5 A | Buck converter, section 6 |
| 3.3 V (Pi-derived, both Pis) | 4 | 0.09 A | 0.05 A | 0.25 A | Not in BOM. Declared in the guard as a conservative limit for a Pi Zero 2 W 3.3 V header pin. |

Two reconciliation rules make those columns comparable, and the guard applies both.

The Power Budget lists sensors on a rail cell reading "3.3 V / 5 V". That row is assigned to
the first rail named, 3.3 V, so the 0.05 A is not counted twice. Without this rule the 5 V
budget reads 2.65 A against a net table that legitimately totals 2.60 A.

The net table is finer-grained than the Power Budget, so a rail's net-table peak is allowed to
exceed its budget but not to fall below it, and the excess is capped at 0.25 A. The only rail
where this bites is 3.3 V, where the net table pays for the encoder supplies and the TB6612
logic supply that the Power Budget rolls into other rows. A missing load makes the net table
fall below the budget and fails; an invented one blows the cap and fails.

## 5. Battery-side worst case and fuse margin

Reflected current is computed at 7.4 V nominal with 90 % converter efficiency, which is a
stated assumption rather than a measured figure.

| Path | Calculation | Current |
|---|---|---|
| Motor rail, direct | 2.00 A | 2.00 A |
| 5 V buck input | 2.60 A x 5.0 V / (7.4 V x 0.90) | 1.95 A |
| 6 V buck input | 3.00 A x 6.0 V / (7.4 V x 0.90) | 2.70 A |
| **Total at the fuse** | | **6.65 A** |

That leaves 0.85 A, about 11 %, under the 7.5 A fuse. It is a synthetic number: every load
peaking at once is not an operating point the robot reaches, because a servo stall and a motor
stall and speech at full volume do not coincide. It is still the tightest margin in the power
architecture and it is worth knowing before the fuse is bought. Two things could make it real
rather than synthetic. A blade fuse is slow enough to ride out the inrush of three bulk
capacitors charging at switch-on, but a fast-blow fuse in the same holder would not be, so
specify the blade type and not a glass fast-blow. And if the deferred motor-rail boost to
9–10 V is ever taken up, this calculation must be redone before it is wired.

## 6. Worked trace: battery positive to the amplifier

Every component, gauge and connector between the pack and one load, without opening another
file. The load chosen is the MAX98357A, because it is the furthest thing from the battery and
crosses two rails on the way.

Battery XT60 positive terminal, out on 18 AWG silicone through the XT60 pair, into the line
side of the inline fuse holder carrying a 7.5 A blade fuse. Out of the fuse holder on 18 AWG
silicone to a 6.35 mm insulated spade on terminal 1 of the SPST master switch. Out of terminal
2 on 18 AWG silicone, again on a 6.35 mm spade, to the VBAT pad of the distribution board,
which is also where the star ground sits. From the VBAT pad on 18 AWG silicone into the screw
terminal of the 5 V buck converter input, which draws 1.95 A at worst case. Out of the buck
converter output at 5.0 V into the distribution board 5 V pad, where a 1000 µF electrolytic
sits across the rail. From the 5 V pad on 22 AWG through a 2-pin JST-XH 2.54 connector to the
MAX98357A VIN pin, with a 0.1 µF ceramic at the amplifier, carrying 1.00 A at peak.

The return is the mirror image: MAX98357A GND, 22 AWG in the same connector shell, to the star
ground point on the distribution board, and out to the battery XT60 negative terminal on
18 AWG silicone. The speaker is not part of that return. The MAX98357A output is bridge-tied
and neither of its two legs is ground.

## 7. Harness build order

Build it in this order and nothing is ever live when it should not be.

Start with the pack out of the robot and the master switch open, and leave it that way until
step 8. Build the distribution board first: the star ground point, the VBAT pad, the 5 V pad,
the three 1000 µF electrolytics, the sense divider and its 0.1 µF, and the 100 kΩ STBY
pull-down if it is boarded rather than fitted at the TB6612. Nothing is connected to it yet.

Second, build the trunk as a subassembly on the bench, XT60 through fuse holder through master
switch to the distribution board VBAT pad, and confirm with a meter that the switch open reads
open circuit and the switch closed reads short, before the pack has ever been near it.

Third, set both buck converters on a bench supply at 7.4 V with no load. Set one to 5.00 V and
one to 6.00 V, mark them, and only then wire their inputs to the VBAT pad and their returns to
the star. Setting a buck under load is how a servo bus sees 8 V.

Fourth, wire ground before power for every remaining block. Every return listed in the net
table lands on the star, and the returns that do not, GND_SIG_M, GND_ENC and GND_MIC, land on
their Pi and reach the star through that Pi's power return.

Fifth, wire the 5 V rail loads, then the 3.3 V loads from the Pi header pins, then the signal
harness. The TB6612 logic supply is 3.3 V and the amplifier supply is 5 V; confirm each with a
meter at the connector before the connector is mated, because the TB6612 reverse protection
covers VM only.

Sixth, wire the motor rail last on the power side: VBAT pad to TB6612 VM, with the 1000 µF and
the 0.1 µF fitted before the motor leads. Fit the STBY pull-down and confirm with a meter that
STBY reads low with the Pi off.

Seventh, wire the 6 V rail to the servo adapter and the servo chain, having already confirmed
6.00 V at the buck output in step three.

Eighth and last, connect the pack. First power-up is staged: switch on with both Pis powered
and the motor rail fused but the TB6612 VM lead left off, confirm 5.00 V and 6.00 V and a sane
ADS1115 reading, then power down, fit the VM lead and repeat. Keep fingers clear of the
sprockets and treads from this point on.

## 8. What this document does not settle

Conductor lengths, because the harness is cut to fit. The physical routing of the trunk through
the tub, which waits on the electronics shelf being printed and the pack strapped in. The
6-pin JST SH motor cables, which Pololu sells separately from the motors and which are not yet
a `BOM.md` line item. And whether the 11 % fuse margin in section 5 should be spent on a
larger fuse, which is a decision for whoever owns the ordering rather than for this drawing.
