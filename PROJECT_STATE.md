# Johnny 5 — Project State

**Authority: this file.** It is the single source of truth for where the project stands.
Phase documents in `/phases/` say what the work *is*; this file says where the work
*stands*. When a session's report and this file disagree, the repository decides.

Owner: the orchestrator session. No worker session edits this file. A worker that
believes it is wrong reports that to the orchestrator.

**Last verified: 2026-08-26 (night, local) against `main` @ `248a41d`.**

**Reconciliation flag for the next turn.** `248a41d` is where `main` stood while this turn ran,
and S22's deliverable is already on it — the S20-O ordering rule working as intended for the
second consecutive cycle. The only thing `main` will not carry is this turn's own state commit.
The working tree is **not clean**, and for the first time the reason has nothing to do with a
session: FreeCAD was open on Andrew's desktop while this turn ran and saved
`mechanical/freecad/drivetrain_v1.FCStd` at 21:08 local, which also rotated its `.FCBak`
sidecars. Section 6 records what that looks like in `git status` and why one line of it reads
as a deletion. Re-derive the header, section 6 and section 4's `pending` row from
`git for-each-ref` and `git log` before relying on any of them.

**One item in section 7 needs action before the next push and is not a session: O22.**
`.env.example` carries a live LiteLLM virtual key as a literal value, the GitHub remote was
confirmed public on 2026-08-26, and the key has been in that repository's history since
`22ad422` on 2026-06-20.

---

## 1. Position

**Phase 02 — Locomotion. Task 6b, Floor Integration Test. Blocked on physical work.**

Tasks 1, 2, 3, 4, 5 and 6a are complete. Task 6b is the only task between the project
and the Phase 02 gate, and no agent session can advance it.

**Ordering is no longer gated.** B5, the power wiring and harness schematic, closed on
2026-08-25 with S17, and the two threads it raised that looked like order gates — the fuse
margin and the encoder cable line item — were both settled the same day. Everything in
`BOM.md` can now be bought. Ordering is Andrew's to do and is not a dispatchable item.

**Nothing on the Phase 02 critical path is dispatchable, and the documentation queue behind it
is spent.** S18 closed the documentation debt this file carried against the critical path; S19
delivered the Pi-M bringup salvage that was D3; S20 stopped correctly at a precondition that
S19-O's half-landed handover had left false; S21 did D7 in full once Andrew's corrected block
cleared it; and **S22 did D8**, giving Pi-V the runtime document it had never had. All of it is
on `main`. What S22 found while writing is worth more than what it wrote: an exposed credential
(O22), and the fact that **Pi-V has never had a bringup session at all** (O24), which is a real
gap in the project rather than a documentation one and which nobody had stated before.

One session's worth of remediation now exists behind that — **D9**, which is small and which the
queue would not otherwise have. Everything that moves Task 6b
is a printer or a bench job.

Gate condition, verbatim from `phases/PHASE_02_LOCOMOTION.md`:

> The robot drives forward, backward, and executes left and right turns on command.
> Motion is governed by a trained policy deployed from the simulation environment, not
> hand-coded PWM values. The offline fallback (Phase 01) continues to function correctly
> when the tread control stack is active.

The single thing that would close it: the drivetrain printed and assembled, motors
bolted into the chassis, drive wiring off breadboard, then a floor run with the deployed
policy and a live offline-fallback test, logged in `simulation/chassis/TUNING.md`.

---

## 2. Blockers

| # | Blocker | Blocks | Who can clear it | Since |
|---|---|---|---|---|
| B1 | **Physical.** `chassis_tub_v1.stl` and `chassis_deck_v1.stl` must be reprinted. The printed tub predates the road-wheel skirts, the idler tensioning slot and the electronics shelf columns; the deck's rim bosses moved, so an existing deck's holes no longer line up. | Phase 02 Task 6b | Andrew (printer) | 2026-08-21 |
| B2 | **Physical.** The drivetrain has never been printed: 2× `drive_sprocket_v1`, 2× `front_idler_v1`, 4× `road_wheel_v1`, 2× `track_loop_v1` (TPU), 2× `idler_carrier_v1`, 6× `axle_collar_v1`, 2× `motor_cap_v1`, `pi_shelf_v1`, `tail_boom_v1`, `tail_roller_v1`, `tail_tyre_v1`. | Phase 02 Task 6b | Andrew (printer) | 2026-08-21 |
| B3 | **Physical.** Motors seated in their cradles and caps screwed down. M2 thread-forming into the columns, no heat-sets. | Phase 02 Task 6b | Andrew (bench) | 2026-07-16 |
| B4 | **Physical.** Drive wiring moved off breadboard — soldered or a secured connector. Breadboard jumpers work loose under tread vibration, which turns a real bug into a connection fault hunt. | Phase 02 Task 6b | Andrew (bench) | 2026-07-16 |

B1 through B4 are physical-world blockers. **No agent session can clear any of them.**
Dispatching a Phase 02 session before they are done is dispatching it to wait.

**Nothing new blocks the build, but section 7 gained an item that is urgent without being a
blocker.** O22, the LiteLLM virtual key committed as a literal value in `.env.example` on a
public GitHub remote, blocks no task and should be acted on today anyway. It is recorded there
rather than here because this section is about what stops work, and that entry does not.

**B5 closed 2026-08-25 (S17), and its deliverables are now on `main`.** It was the oldest
live debt in the project, owed since S01. `docs/diagrams/power_harness_schematic.svg`,
`docs/HARDWARE_power_harness.md` and the `scripts/check_harness_nets.py` guard were verified
against the repository on 2026-08-25 and reached `main` the same day as `9e5191f` and
`678c68a`; the branch has been deleted. The guard was re-run from `main` on 2026-08-25 and
exits 0, reproducing all six checks and every figure. Every physical blocker that remains is
a printer or bench job, so there is nothing left that a dispatched session can clear on the
Phase 02 critical path.

---

## 3. Phase ledger

| Phase | Name | Gate condition (abbreviated) | State | Since | Evidence |
|---|---|---|---|---|---|
| 00 | Hardware Design & BOM | BOM finalized and approved; body design baselined in FreeCAD | **MET** (re-met after reopening) | 2026-08-21 | `c88033b` — drivetrain built and guarded, 1531 g against a 1.6 kg ceiling, `mass_budget.py` and `validate.py` both clean. **The mass has since moved: 1542 g at `ecb244f`** (see below) |
| 01 | Infrastructure & Repository | Both Pis communicate with each other and with home lab LiteLLM; offline fallback functional | **MET** | 2026-06-22 | `0b13d84`, tagged `v1.0`. See caveat below. |
| 02 | Locomotion | Robot drives forward, backward and turns on command via a trained policy | **ACTIVE** | 2026-06-22 | Tasks 1–5, 6a complete; 6b blocked on B1–B4 |
| 03 | Manipulation | Shoulder and head servos respond to commanded positions with position/load feedback; home, wave and attention behaviors execute | Not started | — | — |
| 04 | Cognition | Voice prompt → transcription → LLM with camera context → coordinated speech, motion and LED response, under 4 s | Not started | — | — |
| 05 | Integration & Hardening | 30 minutes continuous mixed operation with no crash or unhandled exception; offline resilience passes; `v5.0` tagged | Not started | — | — |
| 06 | Form & Finish | Whole-robot form review signed off; cosmetic geometry finalized, re-exported and reprinted | Not started | — | Carries a deferred-cosmetics list fed by Phase 00 |

**Phase 00 was closed twice.** Gate met at Session 02 on 2026-06-18 against a body that
had never been printed. Printing it reopened the phase at Session 03 on 2026-08-20 when
the first physical tub proved unbuildable. Re-closed at Session 04 on 2026-08-21. The
lesson is recorded in the decision record: a gate met against an unbuilt artifact is not met.

**The Phase 00 mass figure moved on 2026-08-26 and the gate still holds.** Andrew's two CAD
commits that evening — `23157ef`, the IMU carrier breadboard, and `ecb244f`, the circular track
loop print — added mass. `mechanical/preview/mass_budget.py` run from `248a41d` now prints
**`ASSEMBLED TOTAL 1542 g (96.4% of ceiling)`**, 58 g of headroom, 1597 g at +25 % on the
printed parts, still under the 1.6 kg ceiling in both cases; `mechanical/preview/validate.py`
still reports `ALL CHECKS PASS` across all 16 checks. Both were run by the orchestrator on
2026-08-26 rather than taken from a document. The gate is unaffected. **`BOM.md` was not
updated and still states 1531 g in two places**, which is O23.

**Phase 01 gate caveat.** Clause 3, offline fallback, was satisfied as unit-tested pure
logic — 8/8 in `tests/test_offline_fallback.py`, covering all three state transitions plus
the never-raises guarantee. It has **not** been exercised live against a real LiteLLM
endpoint going down, because `src/motion/main.py`'s MQTT wiring was still a Phase 01 stub
by design. The live test is folded into Phase 02 Task 6b.

---

## 4. Session ledger

Sessions are numbered **globally** (S01, S02, …), not per phase. Per-phase numbering is
how Phase 00 ended up with two "Session 01"s in different eras and is not used here.

**Orchestrator turns take the suffix `-O` on the worker session they close out**, so `S17-O`
is the turn that verified S17 and dispatched S18. Convention adopted 2026-08-25 because the
turn that produced `06783fe` and `769c618` had no row and its commits were being read as
S17's. Numbering orchestrator turns in the main sequence would double the ledger for a cycle
that alternates by design; leaving them out loses the commits.

**Reconstruction caveat:** S01–S14 are reconstructed from decision-log entries, phase
handoffs and commit dates. The boundaries of S03–S06 in particular are inferred from
breaks in the Phase 01 decision log, not from any recorded session marker. Commit dates
mix the authoring machine's local time and UTC; both are shown as git records them.

| ID | Date | Phase | Scope | Outcome | Commits |
|---|---|---|---|---|---|
| S01 | 2026-06-17 | 00 | Hardware selection, BOM, pin maps, power budget | Gate PARTIAL. BOM approved; body baseline outstanding. Power harness schematic first owed here. | `2c1ba9b` `59e8ada` `491301c` `d831a1e` |
| S02 | 2026-06-18/19 | 00 | Task 7 — baseline the body in FreeCAD | **Gate MET** (later reopened). 13 STLs, four parametric build scripts, `validate.py`, `mass_budget.py`. | `73ce4a0` `a6af03a` `428d53f` (tag `v0.0`) |
| S03 | 2026-06-20 | 01 | Infra kickoff — LiteLLM endpoint, broker selection, README | Mosquitto chosen over RabbitMQ; LXC runbook written; README created. | `7d54eb7` |
| S04 | 2026-06-20 | 01 | Mosquitto LXC deploy | Broker live and verified end to end on `sn-mosquitto` / `192.168.1.227`. | — |
| S05 | 2026-06-20/21 | 01 | Pi OS flash, static IPs, per-Pi interface setup | Both Pis on Trixie, static `.217` / `.218`, I2C/SPI/UART configured on Pi-M. | `83954a5` `22ad422` |
| S06 | 2026-06-22 | 01 | Phase 01 gate close | **Gate MET.** MQTT Pi-to-Pi round trip, LiteLLM 8.94 s round trip, fallback 8/8. | `0b13d84` (tag `v1.0`) |
| S07 | 2026-06-22/26 | 02 | Tasks 3–5 — MuJoCo chassis env, PPO training, ONNX policy runner | Env stable; 3 seeds trained; best exported to `policies/locomotion_v3.onnx`; `execute_intent()` seam staged. | `857834c` `3e3bf6a` `9d848be` `c814255` `ded303d` `d48d838` `696c3d9` |
| S08 | 2026-06-26/27 | 02 | Task 1 — `MotorDriver`, `EncoderReader`, bench wiring schematic | TB6612FNG driver and encoder reader with test suite; full drive-bench schematic in `docs/diagrams/`. | `bd4f5cb` `a5c7290` |
| S09 | 2026-07-12/16 | 02 | Task 2 — policy into the motion loop; Task 6 split | `MotionHardware` injection, MPU-6050 fusion, `PROTOCOL.md` finalized. 48/48 tests. Task 6 split into 6a/6b on the mechanical blocker. | `53092a6` `23d5b80` `4ea5100` |
| S10 | 2026-08-09/10 | 02 | Task 6a — encoder calibration under power; motor retention cap | **6a complete**, 450.6 counts/rev measured, 1× decode confirmed. Motor cap designed; tub geometry changed. | `14d30e3` `b09b061` `5898b85` `efe8eaf` `3864e5c` |
| S11 | 2026-08-11/13 | 02/00 | Chassis rebuilt for real in FreeCAD via MCP | Two pre-existing tub defects found: bosses building as five solids, no pilot bores. Build-time boolean guards introduced. | `baf646c` `1a47b43` `03410e1` |
| S12 | 2026-08-20 | 00 | **Phase 00 REOPENED** — tub rework after first print | Four print-and-measure rounds. Bearings moved into hubs, idler on a full-width rod, sprocket on its own bearing. | `7d8c30a` |
| S13 | 2026-08-21 | 00 | Drivetrain design; Phase 00 re-close | **Gate MET** at 1531 g. `build_drivetrain.py` with five printable parts; chassis reworked to carry them; shells to 2.0 mm. | `c88033b` |
| S14 | 2026-08-22 | 00 → orchestration | Handoff authoring | **Failed.** Wrote a Phase 01 initiating prompt for a phase closed two months earlier. Caught only because Andrew ran it. Then authored `ORCHESTRATOR_PROMPT.md`, creating this role. | — |
| S15 | 2026-08-23 | Orchestration | Verify state, reconcile git, create this file | Git topology collapsed to one branch; policy artifact tracked; repo migrated to `C:\dev\johnny5`; this file created; the competing state documents demoted to pointers. | `da6e1fa` `049494b` `31073ac` `d1d4c2b` |
| S16 | 2026-08-24 | Orchestration | Distil the orchestration protocol; retire `ORCHESTRATOR_PROMPT.md` | `docs/ORCHESTRATION.md` created and archived predecessor frozen; turn opener, close-out report convention and section references added. The session logged nothing itself; this row is reconstructed from commit contents on 2026-08-25. | `8bfc0d9` `344c8b7` |
| S17 | 2026-08-25 | 00 (paid off late) | D1 — power wiring and harness schematic | **B5 closed, O6 closed.** 64-net schematic and companion document, a net-consistency guard with a mutation suite, and three `BOM.md` corrections. Report at `docs/reports/J5-S17.md`; verified against the repository 2026-08-25 and merged to `main` the same day. | `9e5191f` `678c68a` |
| S17-O | 2026-08-25 | Orchestration | Verify S17, update state, dispatch D2 | S17 verified with nothing failing; B5 and O6 closed; S16 and S17 logged; O12–O14 opened; the PowerShell line-ending check recorded in `docs/ORCHESTRATION.md`. Not previously logged. | `06783fe` `769c618` |
| S18 | 2026-08-25 | Orchestration/repo | D2 — repository hygiene and documentation corrections | **O7, O8, O12, O13, O14 closed; O10 closed on its index half.** `pyproject.toml` pytest config, `src/vision/requirements-vision.txt`, the `#5219` corrections in three files, and two `BOM.md` corrections. Report at `docs/reports/J5-S18.md`; verified against the repository 2026-08-25. On `docs/repo-hygiene` @ `f31e687`, unmerged. | `f31e687` |
| S18-O | 2026-08-25 | Orchestration | Verify S18, update state, dispatch D3 | S18 verified with nothing failing; five open items closed, four opened; queue renumbered and D3 added. | `7a5f827` |
| S19 | 2026-08-25 | 02 (off the critical path) | D3 — Pi-M bringup salvage, motion requirements, root-note removal | **O16 and O18 addressed; O15 fixed in the repository but unproven on Pi-M.** `scripts/setup_motion_pi.sh` takes `gpiozero` and `lgpio` from apt and targets `~/johnny5-env`; `src/motion/requirements-motion.txt` and `docs/HARDWARE_pi_m_runtime.md` added; the six root notes salvaged and queued for `git rm`. Report at `docs/reports/J5-S19.md`; verified against the repository 2026-08-25. No branch was created and nothing was committed by the session; **Andrew ran the corrected block on 2026-08-26** and both commits are on `main`. O16 and O18 close with them. | `382ee10` `a1f0111` |
| S19-O | 2026-08-25 | Orchestration | Verify S19, update state, dispatch D7 | This row's own turn. S19 verified with nothing failing and no factual error found in it; one judgement call overruled in part. O16 and O18 closed against Andrew's command block, O15 held open until Pi-M runs it, O19 opened, D7 queued, and the queue's numbering frozen. | `ebdea9e` |
| S20 | 2026-08-26 | 02 (off the critical path) | D7 — documentation and drawing maintenance | **Stopped at preconditions; nothing in scope was done.** `main` carried the S19-O state commit and neither of S19's two commits, so the brief's own stop test failed. O19, O17 and O4 untouched; the only file the session wrote is its report. Report at `docs/reports/J5-S20.md`; verified against the repository 2026-08-26 with every claim in it confirmed and nothing found wrong. | — (report committed by S20-O as `91aab43`) |
| S20-O | 2026-08-26 | Orchestration | Verify S20, update state, re-dispatch D7 | This row's own turn. S20 verified and its stop upheld. O16 and O18 requalified as fixed-not-closed, O19 widened to a second instance found this turn, O20 opened, D7 re-dispatched as J5-S21 behind Andrew's block, and two defects in S19's command block corrected before it is run. **Andrew ran the corrected block the same evening and it worked.** | `91aab43` |
| S21 | 2026-08-26 | 02 (off the critical path) | D7 — documentation and drawing maintenance, re-dispatch | **Complete. All four scope items done.** Both `1807` instances in `docs/HARDWARE_drive_bringup.md` clarified in `BOM.md`'s O14 words; the six `#5218` row prefixes in the bench schematic's wiring key changed to `LEFT`/`RIGHT`; `.claude/` added to `.gitignore`; O4's FreeCAD probe spent and answered negatively. Report at `docs/reports/J5-S21.md`; verified against the repository 2026-08-26, nothing failed. Three files uncommitted at close; **committed by Andrew as `10650f2` on 2026-08-26**. | `10650f2` |
| S21-O | 2026-08-26 | Orchestration | Verify S21, update state, close D7 | This row's own turn. S21 verified with nothing failing and no factual error found in it. O16 and O18 closed against commits that now exist; O17, O19 and O20 closed; O4 answered and re-scoped; O21 opened on a working-tree line-ending survey S21 flagged but did not run. D7 closed, D8 queued as optional. | `38569a1` |
| S22 | 2026-08-26 | Orchestration/docs | D8 — Pi-V runtime document | **Complete.** `docs/HARDWARE_pi_v_runtime.md`, 197 lines, every fact traced to a named repository file or marked unverified. Proceeded past a precondition whose evidence form had gone stale, flagged it prominently, and was upheld at close-out. Its open threads are worth more than its deliverable: O22, O24, O25, O26. Report at `docs/reports/J5-S22.md`; verified against the repository 2026-08-26, nothing failed. | `248a41d` |
| S22-O | 2026-08-26 | Orchestration | Verify S22, update state, dispatch D9 | This row's own turn. S22 verified with nothing failing and no factual error found in it — the third close-out of which that is true. Andrew's two unlogged CAD commits reconciled below; the Phase 00 mass figure re-derived at 1542 g; O1 pointed at the document that now exists; O22 through O27 opened; D8 closed and D9 queued. | pending |

**Commits on `main` that came from no dispatched session.** Andrew works at the bench and in
FreeCAD between turns, and that work reaches `main` directly. It gets no session number, because
inventing one would imply a brief and a close-out report that do not exist, but it must be
recorded or section 6 goes stale for reasons no ledger row explains. First used 2026-08-26.

| Commit | Date | What |
|---|---|---|
| `23157ef` | 2026-08-26 19:06 | **IMU moved onto a solderable mini breadboard** aft on the Pi-M shelf, on four 5 mm standoffs, so the IMU, its pull-ups and its connectors solder up as one testable piece. Cost the shelf plate 24 mm of length (111 → 135 mm, +3 g net) and about 8 g of FR-4. 11 files: `BOM.md`, `build_chassis.py`, `chassis_assembly_v1.FCStd`, `j5_params.py`, `params.csv`, `preview/` massing, components and `validate.py`, and the `chassis_tub_v1` and `pi_shelf_v1` STLs. **Touches three integration-lock files** — `params.csv`, `j5_params.py`, `validate.py` |
| `ecb244f` | 2026-08-26 20:38 | **The TPU track loop is now printed as a circle rather than in its running shape**, r 58.0 mm inner, 123 mm across. A printed part is stress-free in the shape it was printed, so the print shape sets the curvature each band element is relaxed at; built oval an element swings the full 0.0500 mm⁻¹ around the loop, built round the worst swing is 0.0328, taking outer-fibre bending strain through a rib from 8.75 % to 5.73 %. Mean curvature is 2π/path for any closed curve, so the circle is optimal and its radius is not free. One per plate at 123 mm where the oval fitted two. 7 files including `build_drivetrain.py`, `j5_params.py`, `validate.py` and `track_loop_v1.stl` |

Both were verified by `git show --stat` on 2026-08-26 and both guards re-run from `248a41d`.
Neither touches `docs/`, `src/`, `scripts/`, `phases/` or this file, which is why S22's scope
was untouched by them. The mass consequence is in section 3; the `BOM.md` consequence is O23.

---

## 5. Dispatch queue

What to dispatch next, in order, with preconditions. **Read only this section on a busy day.**

**Numbers are allocation order and do not move.** D3 was inserted on 2026-08-25 and the former
D3–D5 became D4–D6. That was the last renumber: a new item takes the next free number and the
order to dispatch in is stated in prose below, because a queue whose numbers shift invalidates
every document that cites one. Anything citing a number below D4 and dated before 2026-08-25
predates the renumber.

**Ready now:** **D9**, remediation of what S22 turned up. **Blocked:** D4, D5 and D6 on the
physical work behind them. **Deferred:** the Pi-V bringup session (O24), which needs the box and
the audio hardware and sits behind the same physical work as everything else.
**Not a session, and not D9:** rotating the exposed LiteLLM key (O22) is Andrew's and should
happen before the next push, independently of whether D9 is ever dispatched. Editing
`.env.example` forward does not remove the value from git history; rotation is the remediation
and the file edit is hygiene that follows it.
**Not a session:** B1 and B2, the two print jobs, are the whole of what stands between the
project and the Phase 02 gate. D7 closed at S21 and D8 at S22, both on 2026-08-26.

**D1 — Power wiring and harness schematic.** **COMPLETE (S17, 2026-08-25).**
Delivered on `docs/power-harness-schematic` and merged to `main` the same day as `9e5191f`
and `678c68a`; the branch has been deleted. Kept in the queue rather than removed so this
section reads as a history as well as a plan.

**D2 — Repository hygiene and documentation corrections.** **COMPLETE (S18, 2026-08-25).**
Delivered on `docs/repo-hygiene` @ `f31e687` and verified against the repository the same
day. Closed O7, O8, O12, O13 and O14, and closed O10's index half. Report at
`docs/reports/J5-S18.md`. Fast-forwarded into `main` as `f31e687` on 2026-08-25 and the branch
deleted.

**D3 — Pi-M bringup salvage, motion requirements, and root-note removal.**
**COMPLETE (S19, 2026-08-25); landed on `main` 2026-08-26 as `382ee10` and `a1f0111`.** `scripts/setup_motion_pi.sh` fixed,
`src/motion/requirements-motion.txt` and `docs/HARDWARE_pi_m_runtime.md` added, six root notes
salvaged and queued for removal. Verified against the repository the same day. The three files
are **uncommitted in the working tree**; the two-commit block that lands them, and the `git rm`
block that removes the notes, are in `docs/reports/J5-S19.md` section 6. O16 and O18 close with
those commits. **O15 does not** — the script has never run on Pi-M, and it closes when Andrew
re-runs it there.

**Closed out 2026-08-26.** The original block had two defects, found at S20-O: its first commit
message claimed it closed O15, which no commit can close, and it created `fix/pi-m-bringup`
without ever merging it, so running it verbatim would have left `main` unchanged. Andrew ran the
corrected block the same evening. `382ee10` carries the Pi-M fix and the two new files; `a1f0111`
removes the five root notes and `MEMORY.md`. O16 and O18 close with them. **O15 does not** — the
script still has not run on Pi-M.

**D4 — Phase 02 Task 6b, Floor Integration Test.** *Blocked on B1–B4. Was D3.*
Do not dispatch until the tub and drivetrain are printed, motors are bolted in and the
drive wiring is off breadboard. When those are done: floor run, verify straight-line
travel and turn direction, live offline-fallback test, and log sim-vs-real deltas in
`TUNING.md` including the `WHEEL_RADIUS_M` bench-vs-floor delta. Session config: Sonnet,
Standard, Medium — the code exists, this is procedure and tuning capture. Escalate to
Opus if the sim-to-real deltas are large enough to force revisiting reward shaping.

**D5 — Phase 02 gate close and `v2.0` tag.** *Blocked on D4. Was D4.*

**D6 — Phase 03 kickoff, Manipulation.** *Blocked on D5. Was D5.*

**D7 — Documentation and drawing maintenance.** **COMPLETE (S21, 2026-08-26).** *Added
2026-08-25; attempted and stopped as S20 2026-08-26; done in full as S21 the same evening.* Three carried items that have accumulated to about a session's worth between them
and none of which move Task 6b: O19, the `1807` counts figure in `docs/HARDWARE_drive_bringup.md`
line 16, which needs the same clarifying half-sentence O14 gave `BOM.md`; O17, the six redundant
`#5218` row prefixes in the wiring key of `docs/diagrams/bench_full_schematic.svg`, which O17
itself says to do when that drawing is next revised — this is that revision; and O4, confirming
whether the installed FreeCAD MCP addon exposes `get_rpc_status`, which decides whether O4 is
already satisfied. **This is a maintenance session and should be dispatched as one, not dressed
up as progress.** Session config: Sonnet, Standard, Medium.

**Delivered by S21.** All four items done: both `1807` instances in
`docs/HARDWARE_drive_bringup.md` carry `BOM.md`'s O14 clarification and point at
`simulation/chassis/TUNING.md`; the six `#5218` row prefixes in the bench schematic's wiring key
now read `LEFT`/`RIGHT` with the three real part labels untouched; `.gitignore` gains `.claude/`;
and O4's single FreeCAD probe was spent, returning `method "get_rpc_status" is not supported`.
Report at `docs/reports/J5-S21.md`, verified 2026-08-26. The three files land with this turn's
ordered block.

**D8 — Pi-V runtime document.** *Optional. No dependency; one session, small. Added 2026-08-26.*
`docs/HARDWARE_pi_m_runtime.md` exists because S19 wrote it; **Pi-V has no runtime document at
all**, and O1 already names `docs/HARDWARE_pi_v_runtime.md` as where the combined
`simple-audio-card` overlay belongs when it is written. The document is writable now from the
repository; the overlay is not, and stays in Phase 04. Scope is the document plus a pointer to
`src/vision/requirements-vision.txt` — the file O8 created — and the O1 gap stated plainly rather
than solved. **This is maintenance, not progress on Task 6b**, and it should be skipped rather
than dressed up if Andrew would rather leave the repository still while the printing happens.
Session config: Sonnet, Standard, Medium.

**Delivered by S22 and already on `main` as `248a41d`.** `docs/HARDWARE_pi_v_runtime.md`, 197
lines: the box and its provenance per fact, the camera enablement step with the note that no
record exists of its having been run, `src/vision/requirements-vision.txt` as the dependency
declaration, the `.env` configuration and why `LITELLM_TIMEOUT` is 60.0 against an in-code
default of 8.0, the O1 audio gap stated rather than solved with the shape the overlay section
should take, and a closing section listing every claim with no hardware witness. Report at
`docs/reports/J5-S22.md`, verified 2026-08-26. **D8 is closed and the session found more than it
was sent for** — see D9.

**D9 — Remediation of what S22 turned up.** *Ready now. One session, small. Added 2026-08-26.*
Three unrelated corrections that share nothing but their size, none of which moves Task 6b:
**O22's file half** — replace the literal `LITELLM_API_KEY` value in `.env.example` with a
placeholder in the form `MQTT_PASSWORD` already uses, and say in the comment that the value
lives in the per-Pi `.env` only; **O23** — `BOM.md` states 1531 g in two places and
`mass_budget.py` now prints 1542 g, so both need the new figure with the same "run the script"
framing O13 gave them; and **O27** — four `.FCBak` files are tracked, which is why FreeCAD's
ordinary backup rotation shows in `git status` as a deletion, so `.gitignore` gains the pattern
and the four tracked files go in a `git rm --cached` block for Andrew.
**Do not dispatch this expecting it to close O22.** The file edit is hygiene; the rotation is
the remediation and it is Andrew's. Session config: Sonnet, Standard, Medium.

---

## 6. Repository map

**Remote:** `https://github.com/theDrewski81/short_circuit.git`
**Working copy:** `C:\dev\johnny5` (moved here 2026-08-23; see the decision record).

**Dispatch hazard.** The folder connected to a Cowork session is
`C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5`, the retired copy, and it
is **empty**. Every session must request access to `C:\dev\johnny5` before doing anything
else. Every session through S22 has hit this. Say so in every brief.

**Branches — one.**

| Branch | Role |
|---|---|
| `main` | The trunk. `248a41d` at the time of this turn. Matches `origin/main` and `origin/HEAD`, both pushed. Carries all of S17 through S22, including S21's `10650f2`, the S21-O state commit `38569a1`, Andrew's two CAD commits `23157ef` and `ecb244f`, and S22's `248a41d`. **Not** this turn's state commit, which is in the block handed over with this update. |

`docs/repo-hygiene` was fast-forwarded into `main` and deleted on 2026-08-25, and
`docs/power-harness-schematic` before it on the same day.

**The S19 defect is cleared.** `fix/pi-m-bringup` was never created; the corrected block Andrew
ran on 2026-08-26 committed S19's work directly on `main` instead, as `382ee10` (the Pi-M setup
fix plus `src/motion/requirements-motion.txt` and `docs/HARDWARE_pi_m_runtime.md`, 3 files,
+187/-11) and `a1f0111` (the five root notes and `MEMORY.md` removed, 6 files, -101). Both verified
2026-08-26 by `git show --stat` and `git for-each-ref`. O16 and O18 close against them.

**Uncommitted at the time of this turn, and none of it is a session's:**

```
 D mechanical/freecad/drivetrain_v1.20260821-142329.FCBak
 M mechanical/freecad/drivetrain_v1.FCStd
?? docs/reports/J5-S22.md
?? mechanical/freecad/chassis_assembly_v1.20260826-141152.FCBak
?? mechanical/freecad/drivetrain_v1.20260826-203851.FCBak
```

`docs/reports/J5-S22.md` is S22's report and lands with this turn's state commit, per
`docs/ORCHESTRATION.md` section 4. **Everything else is FreeCAD, open on Andrew's desktop while
this turn ran.** It saved `drivetrain_v1.FCStd` at 21:08 local — two minutes before this turn
began — and rotated its backup sidecars in the same act, which is what the deletion line is:
`drivetrain_v1.20260821-142329.FCBak` is a **tracked** file that FreeCAD rotated out from under
git. The STLs are still stamped 20:38, so this was a GUI save and not a build, exactly as
`docs/ORCHESTRATION.md` section 7 says to read that pattern. Nothing here is a defect in any
session's work; the tracked `.FCBak` files are O27.

**Do not commit any of it blind.** Whether `drivetrain_v1.FCStd`'s new state is wanted is
Andrew's to say, not something to infer from a timestamp.

**The merge was a fast-forward, not a squash, and that is fine.** `CLAUDE.md` says "squash
merge to `main` via PR". S17's branch went in as its two own commits, `9e5191f` and
`678c68a`, followed by the orchestrator turn's `06783fe` and `769c618` committed directly on
`main`. Linear history held, which is what the rule protects; the PR-and-squash half of it
describes a workflow this single-operator repository does not run. Recorded here rather than
silently diverged from. `docs/repo-hygiene` was a single commit, so a fast-forward and a squash
would have produced the identical tree and history; it went in as a fast-forward on
2026-08-25.

Four branches were deleted on 2026-08-23 — `fix/chassis-tub-defects`, `feat/motor-driver`,
`sim/chassis-env`, `phase/00-hardware`. The first *was* the real trunk under a misleading
name; the other three were strictly its ancestors. `main` now carries all of their content.

**Tags.**

| Tag | Commit | Marks |
|---|---|---|
| `v0.0` | `428d53f` | Phase 00 gate, first close (S02) |
| `v1.0` | `0b13d84` (annotated `0d47b78`) | Phase 01 gate |
| `archive/runs-937311c` | `937311c` | Preserves 64 training artifacts, 7.9 MiB of locomotion_v1/v2/v3 checkpoints, dropped from the tracked tree on 2026-08-23. Not a project milestone. |

Per `CLAUDE.md`, `v2.0` is applied at the Phase 02 gate. The intra-phase iteration tags
this file previously described as "pending removal" from `CLAUDE.md` were in fact removed
from it on 2026-08-23; that sentence was stale and is corrected here.

**Deliberately untracked, and where the content lives instead.**

| Path | Why | Where it lives |
|---|---|---|
| `simulation/chassis/runs/` | Training intermediates, regenerated on the home lab | `archive/runs-937311c` in git; a copy extracted to the lab on 2026-08-23 that the orchestrator has **not** been able to verify |
| `simulation/chassis/smoke_run/*.onnx` | Smoke-test output, regenerable | Nowhere; disposable |
| `.venv/`, `.pytest_cache/` | Local environment | Rebuilt from `simulation/chassis/requirements-train.txt` plus pytest |
| `.claude/` | Session-local | Present in the working tree. **Now ignored as well as untracked** — `.gitignore` line 27, added by S21 against O20 |
| `ORCHESTRATOR_PROMPT.md` | Session-local | **Not present in this working copy at all**, contrary to what this row said until 2026-08-26. It was not carried through the migration. Its content is archived and tracked at `docs/archive/ORCHESTRATOR_PROMPT_2026-08-22.md`, so nothing is lost; there is simply no untracked copy here to ignore. Found by S21 |

`policies/locomotion_v3.onnx` **is** tracked as of `da6e1fa`. It is the Phase 02 gate
artifact and previously existed as a single 21,680-byte file on one disk while 7.9 MiB of
intermediate checkpoints were committed. That inversion is resolved.

**Line endings.** The working copy sets `core.autocrlf = input` locally. **Every blob is LF —
that half is verified and is the half that matters. The checkout is not**, and the sentence that
stood here until 2026-08-26 claiming it was is corrected: `git ls-files --eol` across the whole
tree reports `i/lf w/crlf` on **75 of 152 tracked files** and `i/crlf` on none. `git status` is
genuinely clean anyway, because `core.autocrlf = input` normalises on read and on add, so the
old conclusion held for the wrong reason. Nothing is broken and no CRLF can reach a blob through
a normal `git add`; the survey is recorded as O21 so the next reader is not misled a second time.
Do not "fix" anything here with
`.gitattributes` or a renormalize commit — both were considered and rejected. Verify after
any text commit with `git cat-file -p <ref>:<path> | tr -cd '\r' | wc -c`, which must be 0.
`git diff --ignore-cr-at-eol` **hides** this class of defect; use it to read content
changes, never to certify a commit.

---

## 7. Open items register

Carried non-blocking items. Blocking ones live in section 2.

| # | Item | Owner | Due in | Since |
|---|---|---|---|---|
| O1 | **Combined `simple-audio-card` device-tree overlay** for the INMP441 microphone plus the MAX98357A amplifier on one I²S bus on Pi-V. Stock mic and amp overlays conflict. Referenced in `BOM.md` and the Phase 00 and 04 documents; never written. Currently recorded only in prose. **The home now exists: `docs/HARDWARE_pi_v_runtime.md`, written by S22 on 2026-08-26 (`248a41d`).** It carries an audio section that states this gap rather than solving it, and specifies the shape the overlay entry should take when someone writes it, on `docs/HARDWARE_pi_m_runtime.md`'s `pwm-2chan` section as the model: the exact `config.txt` line, why each argument is load-bearing, the failure signature without it, and the one command that proves it loaded. **This item closes at a Pi-V bringup (O24), not from a session** — the overlay cannot be tested from here, and writing it blind is the mistake O15 is still paying for. | Worker | Phase 04 | 2026-06-17 |
| O2 | **SSH key auth for both Pis.** Deferred, not abandoned. Both currently use password auth via Devolutions RDM. When retrying: clear RDM's cached host key for the IP/entry first — a stale host fingerprint produced a false "public key doesn't match" error last attempt. | Andrew | Phase 05 | 2026-06-20 |
| O3 | **`.env` secrets management** — local per-Pi files versus the Agentic OS secrets manager. Unresolved; no preference stated. | Andrew | Phase 05 | 2026-06-22 |
| O4 | **FreeCAD MCP addon update. Confirmed 2026-08-26 (S21), and independently reproduced by the orchestrator the same evening — the item stands, it is not already satisfied.** Both calls returned `<Fault 1: '<class 'Exception'>:method "get_rpc_status" is not supported'>`. That is an XML-RPC fault, not a timeout: something on `127.0.0.1:9875` parsed the request, looked the method up and reported it absent, so FreeCAD was running with the addon loaded and the addon simply predates the method. **A second fact worth carrying: the Cowork bridge advertises `mcp__remote-devices__freecad__get_rpc_status` with a full schema, and the addon behind it refuses the call.** A name in the tool inventory is not evidence the addon services it. The remaining work is the addon update itself, which is Andrew's — it is a Windows FreeCAD install no session can reach. Original text: The installed neka-nat addon predates `get_rpc_status`, which would diagnose the intermittent GUI-dispatch jam in one call instead of by elimination. | Andrew | Before the next CAD session | 2026-08-21 |
| O5 | **`preview/` massing not updated** for the new drivetrain parts. | Worker | Phase 06 | 2026-08-21 |
| ~~O6~~ | **CLOSED 2026-08-25 (S17, and Andrew at the bench).** Both drive motors are Pololu **#5218**; the #5219 was bought deliberately as a fit test and does not fit the chassis cleanly. `BOM.md` corrected to $32.45 each, $65 the pair. The wrong references left behind are now O12. Original text: **Drive motor part number contradiction.** S12 fixes the motor as Pololu **#5218** (150:1 HPCB 12 V, 12 CPR encoder, back connector). The 2026-06-26 decision entry prices **#5219** at ~$32.45 each and flags BOM Section 1 as running ~$25 over. One of the two is wrong and `BOM.md` should say which. | Worker | Before ordering (with D1) | 2026-08-23 |
| ~~O7~~ | **CLOSED 2026-08-25 (S18).** `pyproject.toml` added with `[tool.pytest.ini_options] testpaths = ["tests"]` and a comment naming both offending files and why neither is a unit test. Verified: bare `python -m pytest -q` from the repository root gives `48 passed`, exit 0; the same command with `--override-ini="testpaths="` still dies with the two collection errors, so the fix is what is doing the work. Original text: **No pytest configuration.** Bare `pytest` at the repo root collects `scripts/test_llm_client.py` and `simulation/chassis/test_env.py` and fails collection. The real suite is `python -m pytest tests\ -q`, 48 tests. | Worker | D2 | 2026-08-23 |
| ~~O8~~ | **CLOSED 2026-08-25 (S18), with the item's own premise corrected.** `src/vision/requirements-vision.txt` added, pinning `httpx==0.28.1` and `python-dotenv==1.2.3`, sited beside the code it serves on the `requirements-train.txt` precedent. **`llm_client.py` imports `httpx` only**; `python-dotenv` is imported by `scripts/test_llm_client.py` and `scripts/whats_this_color.py`, the two Pi-V bench programs that drive that module. Both packages still belong in one Pi-V file, so the deliverable is unchanged. The pins are current PyPI releases and are **not** verified against Pi-V, which no agent can reach; the file says so. Pi-M's equivalent gap is O16. Original text: **`httpx` and `python-dotenv` undeclared.** Imported by `src/vision/llm_client.py`; present in no requirements file. Only `simulation/chassis/requirements-train.txt` exists. | Worker | D2 | 2026-08-23 |
| O9 | **`locomotion_v3` run extraction unverified.** A copy of `best/best_model.zip`, `vecnormalize.pkl` and the checkpoints was extracted to a lab path outside the connected folder on 2026-08-23. The orchestrator cannot see that path and has not confirmed it. Until confirmed, `archive/runs-937311c` is the only known copy. | Andrew | Next session | 2026-08-23 |
| ~~O10~~ | **CLOSED 2026-08-25 (S18) on both halves it could reach; the removal is now D3.** The index defect is fixed — `MEMORY.md` spells both `.MD` names as git tracks them, drops the reference to the deleted `sim/chassis-env` branch, and carries a header saying it is an index and not a summary, pointing at `docs/ORCHESTRATION.md` section 9. The membership question is answered: **the notes do not belong in the repository**, but `johnny5-pi-m-env.md` must be salvaged into `scripts/setup_motion_pi.sh` and `docs/` before any of them go, because it holds a live correction to a script Andrew will run again. That salvage and the `git rm` are D3. The files could not be renamed or deleted from a session in any case; the mount does neither. Original text: **Loose project-memory notes committed at the repo root** — `feedback_conciseness.md`, `johnny5-cloud-mount-quirks.MD`, `johnny5-phase02-locomotion.MD`, `johnny5-pi-m-env.md`, `sandbox-no-torch.md`. Two carry a `.MD` extension that `MEMORY.md` spells `.md`. Decide whether they belong in the repo at all and make the index match. | Worker | D2 | 2026-08-23 |
| O11 | **Phase 06 cosmetic deferral list** — track pattern screen accuracy (references show transverse grouser pads, not the herringbone adopted); optional fine circumferential ribs on the anti-tip tyre; brow gear teeth, currently pitch-diameter blanks; press-fit eye-dome and camera inserts. | Worker | Phase 06 | 2026-08-21 |
| ~~O12~~ | **CLOSED 2026-08-25 (S18).** All three corrected: `docs/HARDWARE_drive_bringup.md` line 12 to `#5218 … back connector`, five labels in `docs/diagrams/bench_full_schematic.svg`, and `simulation/chassis/TUNING.md` line 72 with the part numbers removed and `LEFT = channel A, RIGHT = channel B` kept. Verified: `grep -c 5219` returns 0 in all three; the `TUNING.md` diff touches one line and both measured crossovers on lines 65–70 are byte-identical; the SVG still parses as well-formed XML; `BOM.md`'s closing note now lists all three locations. A fourth stale reference outside the item's scope is O18. Original text: **Three `#5219` references are now plainly wrong**, not merely contradictory: `docs/HARDWARE_drive_bringup.md` line 12, five labels in `docs/diagrams/bench_full_schematic.svg`, and the "side assignment locked" line at `simulation/chassis/TUNING.md` line 72. `TUNING.md` needs the most care — that line carries two separate facts, the part numbers (wrong) and the left/right channel assignment with its lead and encoder crossovers (measured, right). Only the part numbers go. `BOM.md`'s own closing note lists two of the three locations and should be completed. | Worker | D2 | 2026-08-25 |
| ~~O13~~ | **CLOSED 2026-08-25 (S18).** The entry is struck through rather than deleted, on the file's own convention for resolved items, and now states 1531 g against the 1.6 kg ceiling with 69 g of headroom and 1578 g at +25 % on the printed parts. Verified by running `mechanical/preview/mass_budget.py` in a scratch copy: `ASSEMBLED TOTAL 1531 g (95.7% of ceiling)`. That is the script, not a document — the figure this project quoted by hand for two months came from a script that was crashing. Original text: **`BOM.md` carries a superseded mass claim.** Its open-items list still reads "the assembled total is 1655 g against a 1.6 kg ceiling". The identical paragraph was deleted from `phases/PHASE_00_HARDWARE.md` on 2026-08-23 as stale, and section 3 evidences the Phase 00 gate at 1531 g. As written, `BOM.md` says a met gate condition is breached. | Worker | D2 | 2026-08-25 |
| ~~O14~~ | **CLOSED 2026-08-25 (S18).** `BOM.md` section 1 now reads "1807 counts/output-rev at 4× quadrature, which is **not** the operative figure", names `COUNTS_PER_OUTPUT_REV` as 451.74 with 450.6 measured at S10, and points at `TUNING.md`. Clarified rather than deleted, as the item asked. Verified in place. Original text: **`BOM.md` section 1 quotes 1807 counts per output revolution.** S10 settled that `gpiozero.RotaryEncoder` decodes 1× and that the operative constant is 451.74, with 450.6 measured. 1807 is defensible as the raw 4× quadrature figure but reads as the operative one. Wants a clarifying half-sentence, not a deletion. | Worker | D2 | 2026-08-25 |
| O15 | **Fixed in the repository at S19; unverified on Pi-M, and not closed on `bash -n`.** `scripts/setup_motion_pi.sh` now installs `python3-gpiozero` and `python3-lgpio` from apt, creates the venv with `--system-site-packages`, repairs an existing `pyvenv.cfg` in place with `sed`, and defaults `JOHNNY5_VENV` to `~/johnny5-env`. None of it has been executed on Pi-M; no agent session can reach `192.168.1.217`. The apt route and the `include-system-site-packages` flag have a witness — the 2026-07-12 bench bringup did exactly that — but the `sed` repair, the `pip install -r` path and the three added verification imports have none. **Closes when Andrew re-runs `bash scripts/setup_motion_pi.sh` on Pi-M** and the run ends with `gpiozero` and `lgpio` resolving under `/usr/lib/python3/dist-packages`. Closing it before then would be a gate met against an unbuilt artifact, which this project has already done once. While on the box: look for an orphaned `~/johnny5/venv` from a run at the old default and delete it. Original text: **`scripts/setup_motion_pi.sh` carries an install line known to fail on Pi-M, and a venv default that is not the venv.** Line 76 ran `pip install onnxruntime numpy smbus2 gpiozero lgpio rpi-hardware-pwm paho-mqtt`; `lgpio` cannot pip-build on Trixie with Python 3.13. Both corrections had lived only in the root note `johnny5-pi-m-env.md` since 2026-07-12. | Andrew | Next Pi-M contact | 2026-08-25 |
| ~~O16~~ | **CLOSED 2026-08-26.** `main` carries `src/motion/requirements-motion.txt` as of `382ee10`, which is the close test this entry set for itself; verified by `git show --stat 382ee10`. It was fixed at S19 on 2026-08-25 and spent a day requalified as fixed-not-closed because the commit had not been made. Original close text follows. `src/motion/requirements-motion.txt` added — `onnxruntime>=1.18`, `numpy<3`, `smbus2>=0.4`, `rpi-hardware-pwm>=0.2`, `paho-mqtt>=2.1` — as floors rather than exact pins, because Pi-M installs from the piwheels mirror whose versions can lag PyPI, and with `gpiozero` and `lgpio` deliberately absent under a header block naming the apt command. `setup_motion_pi.sh` now reads that file instead of carrying a second list, which is the drift that produced O15. Verified 2026-08-25: every declared package traces to a real import — `numpy` at module scope in `locomotion_policy.py`, `onnxruntime` lazily at its line 78, `smbus2` lazily in `mpu6050.py`, `rpi_hardware_pwm` lazily in `motor_driver.py` — except `paho-mqtt`, which the file itself states is not yet imported and says why. Pins are **not** verified against Pi-M. Original text: **Pi-M runtime dependencies are undeclared.** `src/motion/` imports `numpy` at module scope and `onnxruntime` inside `LocomotionPolicy`; `scripts/setup_motion_pi.sh` installs seven packages inline and no requirements file names any of them. `numpy` appears declared only because `simulation/chassis/requirements-train.txt` happens to list it, which is the training environment, not the Pi. Same class of gap as O8, which covered Pi-V only. | Worker | D3 | 2026-08-25 |
| ~~O17~~ | **CLOSED 2026-08-26 (S21).** The six row prefixes now read `LEFT` and `RIGHT`; `grep -c "#5218"` returns 3, the two motor labels on lines 81 and 88 and the retained key header on line 150, and the SVG still parses as well-formed XML. No `x`, `y`, `font-size` or `fill` attribute was touched and no replacement string is longer than the one it replaced, so nothing can have overflowed its column. Verified in place by the orchestrator. Original text: **`docs/diagrams/bench_full_schematic.svg`'s wiring key now prefixes both columns `#5218`.** Correct and redundant: with no left/right variant the column headers are the only thing telling them apart, so the per-row part number is noise. Change the six row prefixes to `LEFT`/`RIGHT` and drop the part number from the rows. Cosmetic; do it whenever that drawing is next revised, not on its own. | Worker | Next revision of that drawing | 2026-08-25 |
| ~~O18~~ | **CLOSED 2026-08-26.** `git ls-files` no longer lists `johnny5-phase02-locomotion.MD` — removed with the other four notes and `MEMORY.md` by `a1f0111`. S21 re-ran the `5219` grep outside `docs/archive/` and `docs/reports/` and found only `BOM.md`'s two deliberate corrections and this file's own history, which the orchestrator reproduced. Original close text follows. The line goes with the file rather than being corrected in place: `simulation/chassis/TUNING.md` line 72 already carries the correct `LEFT = channel A, RIGHT = channel B`, and carrying a corrected copy forward would re-create the duplication that made the error possible. Verified 2026-08-25 with `git grep 5219` excluding `docs/archive/` and `docs/reports/`: the only hits are that note, `BOM.md`'s two deliberate corrections and this file's own history. Original text: **`johnny5-phase02-locomotion.MD` still states `#5218 = LEFT (ch A) / #5219 = RIGHT (ch B)`.** The same defect O12 closed, in a fourth file. S18's definition of done scoped its grep to `BOM.md docs simulation`, and this note sits at the repository root. Closes with the file's removal in D3; if the file survives that decision, the line must be corrected instead. | Worker | D3 | 2026-08-25 |
| ~~O19~~ | **CLOSED 2026-08-26 (S21).** Both instances now carry `BOM.md`'s O14 clarification in the same words — the figure kept, named as the raw 4x quadrature count, `COUNTS_PER_OUTPUT_REV` given as 451.74 with 450.6 measured at S10, and `simulation/chassis/TUNING.md` cited. `grep -n 1807` returns exactly two lines and each carries both `451.74` and the pointer on the line itself. The file is 104 lines before and after; the diff is one table row and one re-wrapped prose paragraph. S21 also swept every other `1807` in the tree outside `docs/archive/` and `docs/reports/` — nine further hits, all of which already state 451.74 or explicitly call 1807 the raw figure — so **no further instances of this defect exist**. Verified in place by the orchestrator. Original text: **`docs/HARDWARE_drive_bringup.md` line 16 quotes “≈ **1807 counts / output rev** (quadrature)” in its Hardware table with nothing beside it saying that `COUNTS_PER_OUTPUT_REV` is 451.74.** Defensible as the raw 4× figure and reads as the operative one — the same defect O14 had `BOM.md` clarify, in a document O12 and O14 both edited for other reasons. Wants the same clarifying half-sentence and a pointer to `simulation/chassis/TUNING.md`, not a deletion. Found by S19, out of its scope. **Widened 2026-08-26 at S20-O: line 73 of the same file carries the identical figure** — “12 CPR × 150.58:1 ≈ 1807 counts/output-rev” — and pairs it directly with `gpiozero.RotaryEncoder`, the decoder S10 established returns 451.74 rather than 1807. That instance is worse than line 16's, which at least stands alone in a table. Both are in scope; `grep -n 1807 docs/HARDWARE_drive_bringup.md` returns exactly these two lines. | Worker | D7 | 2026-08-25 |
| ~~O20~~ | **CLOSED 2026-08-26 (S21).** `.gitignore` line 27 is `.claude/`, above it a comment pointing at section 6 of this file. `git --no-optional-locks status --porcelain` no longer lists it and nothing under `.claude/` was ever tracked, so the ignore removes nothing. S21 also normalised `.gitignore`'s working-tree copy from CRLF to LF in the same edit, which is what turned up O21. Verified in place by the orchestrator. Original text: **`.claude/` is untracked but not ignored.** Section 6 lists it as deliberately untracked and it has shown as `??` in every `git status` since the migration; S19 and S20 each spent a paragraph of their reports saying it should stay that way. One line in `.gitignore` ends that permanently. Cosmetic; fold into D7. | Worker | D7 | 2026-08-26 |
| O21 | **The working tree is mostly CRLF, and section 6 said for months that it was not.** `git ls-files --eol` reports `i/lf w/crlf` on **75 of 152 tracked files** and `i/crlf` on none. Every blob is LF, which is the half that matters and is unchanged; the checkout is not, and `core.autocrlf = input` has been hiding it by normalising on read. **Nothing is broken** — no CRLF can reach a blob through a normal `git add` while that config holds, which is why nothing has ever shown as modified. Two things follow. First, section 6's claim is corrected and this entry exists so the next reader does not re-derive it a third time. Second, the open question is whether to leave it: a `git add --renormalize` was considered and rejected on 2026-08-23 for the tracked side, and the working-tree side is cosmetic. **Recommendation: leave it, and never certify a commit from a working-tree CR count alone** — read the blob, as `docs/ORCHESTRATION.md` section 6 prescribes. Raised as a one-line observation by S21, surveyed and quantified by the orchestrator the same evening. | Worker | No due date; informational | 2026-08-26 |
| **O22** | **A live LiteLLM virtual key is committed in `.env.example`, and the GitHub remote is public.** `LITELLM_API_KEY=sk-ft-osuRqKu2Eldav3HgAVw` is a literal value, not a placeholder; every other secret in that file is one (`MQTT_PASSWORD=<set-on-broker-deploy>`). Found by S22, which correctly said it could not check the remote's visibility. **The orchestrator checked: `https://github.com/theDrewski81/short_circuit` loads as a public repository.** `git log -S` puts the value in the tree since `22ad422` on 2026-06-20, so it has been public for sixty-eight days. Scope, stated so this is neither under- nor over-read: the key authorises the AOS LiteLLM proxy at `192.168.1.223:4000`, an RFC1918 address, so it is not directly callable from the internet — the exposure is of a credential that is useful to anyone who reaches that LAN, and of the proxy's existence and addressing. **Rotate the key on the AOS proxy.** Editing the file forward does not remove the value from history, so rotation is the remediation and the `.env.example` edit is hygiene that follows it (D9). A history rewrite was considered and is not recommended: the value is already public, a rewrite breaks every clone and tag, and it buys nothing a rotation has not already bought. | **Andrew** | **Before the next push** | 2026-08-26 |
| O23 | **`BOM.md` states a mass the script no longer prints.** Lines 173 and 181 both say 1531 g against the 1.6 kg ceiling, 69 g headroom, 1578 g at +25 %. `mechanical/preview/mass_budget.py` run from `248a41d` prints **1542 g, 96.4 % of ceiling, 58 g headroom, 1597 g at +25 %**, because of `23157ef` and `ecb244f`. The gate still holds and section 3 records the new figure; `BOM.md` does not. Same defect class as O13, which corrected the same paragraph from 1655 g four days earlier, and the same lesson: quote the script, and re-run it when the geometry moves. | Worker | D9 | 2026-08-26 |
| O24 | **Pi-V has never had a bringup session, and nothing provisions it.** `setup_motion_pi.sh` provisions Pi-M; there is no `setup_vision_pi.sh`; `deploy_vision.sh` is deployment, not provisioning; the steps that were actually run exist only as prose in `phases/PHASE_01_INFRASTRUCTURE.md` task 2 and were performed by hand at S05 on 2026-06-20. Re-provisioning Pi-V today means re-reading that task list and repeating it manually. Two further absences belong to the same session rather than to separate items: **no `config.txt` line is recorded anywhere for hardware PWM on Pi-V**, though `BOM.md` puts the 1 W navigation light on GPIO13 as hardware PWM into a MOSFET gate and `docs/HARDWARE_power_harness.md` carries it as `SIG_NAV_PWM` — on Pi-M the equivalent needed an explicit `dtoverlay=pwm-2chan` and a reboot, and its absence looked like dead hardware; and **O1's audio overlay**, which is a `config.txt` question about the same box. **Do not write `setup_vision_pi.sh` from a session.** S22 recommended against it and the orchestrator agrees: it could be written today from Phase 01 task 2 and never tested, which is exactly where O15 has sat for two days. Write it at the bench, the way Pi-M's corrections came out of 2026-07-12. If a checklist is wanted sooner, a numbered runbook in `docs/HARDWARE_pi_v_runtime.md` is the smaller and more honest deliverable. | Andrew (bench) + Worker | Phase 04, behind the physical work | 2026-08-26 |
| O25 | **Phase 04's camera guidance names a different OS than the box runs, and a different library than the repository uses.** `phases/PHASE_04_COGNITION.md` task 2 and its Known Constraints both specify `picamera2` on Bookworm and warn that its APIs differ between OS versions; this file puts both Pis on Trixie. The only program in the repository that captures a frame, `scripts/whats_this_color.py`, uses `rpicam-still`, so the Phase 04 pipeline will be the first `picamera2` code on that box. Neither `picamera2` nor `rpicam-apps` is declared in any requirements file. Not worth a session of its own; fold into the next Phase 04 edit. Found by S22. | Worker | Phase 04 | 2026-08-26 |
| O26 | **No systemd unit exists for either Pi.** `deploy_motion.sh` and `deploy_vision.sh` both restart a unit their own comments call TBD and tolerate the failure, so neither script currently does the second half of its job. Symmetric across the two Pis, so not part of the Pi-V asymmetry. Found by S22. | Worker | Phase 05 | 2026-08-26 |
| O27 | **Four `.FCBak` files are tracked, so FreeCAD's ordinary backup rotation shows up in git as a deletion.** `chassis_assembly_v1.20260821-143150.FCBak`, `drivetrain_v1.20260821-142329.FCBak`, `head_assembly_v1.20260619-220703.FCBak`, `torso_assembly_v1.20260619-220703.FCBak`. They are FreeCAD's own snapshots of superseded document states, regenerated on every save and of no value the `.FCStd` history does not already carry. `.gitignore` has no pattern for them. The fix is one `.gitignore` line plus a `git rm --cached` block, which is Andrew's; the pattern alone would not untrack what is already tracked. Surfaced 2026-08-26 when a save from an open FreeCAD put ` D ` in `git status` for a file nobody had touched. | Worker (`.gitignore`) + Andrew (`git rm --cached`) | D9 | 2026-08-26 |

---

## 8. Known weaknesses accepted

Engineering decisions taken with eyes open. Each records what would trigger revisiting it.

**Torso split screws are registration, not clamping.** The four M3 screws pass through the
front wall, cross 90 mm of open interior and land in the back wall. *Revisit when the torso
is first physically assembled and the joint can be felt.*

**Sprocket overhang.** The drive sprocket's centre sits 16 mm outboard of a single 3 mm-wide
MR106ZZ. Loads are small enough that it should hold, but it is the least-supported joint in
the drivetrain. *Revisit first if the drive feels rough on the bench.*

**Motor-pocket floor openings.** A ø12 motor on a 23.5 mm axle line has its belly at z 17.5,
below the tub underside at 18.0, so the bore cuts through the floor: 525 mm² of genuine
through-opening into the electronics bay. Largely blocked in service by the motor body and
the retention cap. A 3 mm skirt would close it for about 3.9 g. *Deferred, with foam tape at
assembly as the zero-mass alternative. Revisit if the underside must ever be sealed.*
`build_chassis.main()` guards this: it probes both faces of the floor and fails if more is
open than the motor pockets account for, so no future lightening pass can reopen it quietly.

**Motor connector relief grazes a cap screw.** The Pololu #5218's back connector needs a
3 × 11 mm relief in the −Y pocket wall. It grazes one cap screw; 65% of the surrounding
material survives, so the screw is weakened rather than lost. *Accepted at S12.*

**Cap plate is too narrow for washers.** The cap leaves ~1.05 mm of plate around each screw
hole — enough for an M2 pan head, not for a washer. The rear tub wall sets this limit and it
cannot be widened without moving the wheelbase. *Accepted; structural, not fixable in place.*

**Floor lightening pocket depth is ambiguous.** Its cut starts 0.05 mm above the belly
surface, leaving a sub-layer skin. The comment promises "fore and aft" pockets; there is one.
*Accepted at S12, cosmetic.*

**Phase 01 offline fallback never tested live.** Verified as unit-tested pure logic only.
*Closes as part of Task 6b.*

**Fuse margin is 11 % against a synthetic worst case.** Worst-case simultaneous draw at the
7.5 A inline blade fuse computes to 6.65 A, summing a motor stall, a servo stall and
full-volume audio that do not coincide; a realistic worst case is roughly 3.5–4 A. Andrew
ruled on 2026-08-25 that nothing changes: a blade fuse carries its rating continuously and
needs roughly twice it to open in seconds, and the ~0.1 J switch-on inrush across the three
bulk electrolytics is orders of magnitude below its I²t, which makes inrush a question about
master-switch contact life rather than about the fuse. A larger fuse would only weaken
protection against a partial short. *Two standing cautions survive: never substitute a
fast-blow glass fuse into the same holder, and if the deferred motor-rail boost to 9–10 V is
ever taken up, redo the battery-side calculation in section 5 of
`docs/HARDWARE_power_harness.md` before wiring it.*

---

## 9. Decision record

Most recent first. Migrated from `INITIATING_PROMPT.md`'s decision log, which ran from
2026-06-20 to 2026-08-11, and from the four session handoffs in
`phases/PHASE_00_HARDWARE.md`, which carry Sessions 03 and 04 that the former never
received. **Never truncate this section.** Archive by year or phase if it outgrows the file.

### 2026-08-26 (night) — S22 and S22-O — the Pi-V document, and what writing it found

- **The deliverable is the smaller half of this session.** `docs/HARDWARE_pi_v_runtime.md`
  exists and is honest about being weaker evidence than its Pi-M counterpart, which is the
  point of it. What matters more is what S22 could not have found without writing it: a
  credential exposed on a public remote for sixty-eight days, and the fact that **Pi-V has
  never had a bringup session** — an absence nobody had stated, in a project that has had
  Pi-M's equivalent documented since 2026-07-12.
- **The exposed key is rotated, not rewritten.** `.env.example` has carried a literal
  `LITELLM_API_KEY` since `22ad422` on 2026-06-20 and the GitHub remote is public, confirmed
  this turn rather than assumed. The remediation is rotation on the AOS proxy, because the
  value is already in published history and editing the file forward removes nothing. A
  history rewrite was considered and rejected: it breaks every clone and tag and buys nothing
  the rotation has not. The proxy is on an RFC1918 address, which bounds the exposure without
  excusing it. O22.
- **Sources are named per fact when the file has no single witness.** The Pi-M document opens
  with one provenance sentence covering everything in it, which is honest because one bench
  session produced all of it. Nothing in the Pi-V document has that witness; its facts come
  from a 2026-06-20 configuration session, a 2026-06-22 gate close, a committed `.env.example`
  and the deploy scripts' defaults. A three-column table costs width and buys a reader the
  ability to check any single row. Adopted as the pattern for any document assembled from the
  repository rather than from hardware.
- **The system Python version was recorded as an absence rather than inferred.** 3.13 is what
  the same Trixie image gives Pi-M and is almost certainly right. It is also exactly the shape
  of claim `docs/ORCHESTRATION.md` section 9 says produced three separate failures here. The
  document says what is known, says what is expected, and says which is which.
- **`setup_vision_pi.sh` was not written and should not be.** It could be authored today from
  Phase 01 task 2 and could not be tested, which is precisely where O15 has sat since S19. A
  second untested provisioning script doubles that debt to buy a file. It gets written at a
  Pi-V bringup, against the hardware. O24.
- **A worker proceeded past a precondition and was upheld.** S22's brief tested "`main` carries
  S21's commit" by way of "`git log --oneline -3` shows it", and `main` had moved forward two
  commits, so the evidence form failed while its substance held. S22 proceeded, flagged the
  call at the top of its report and asked the orchestrator to judge it. **Upheld.** The stop
  rule guards against a repository missing commits the scope depends on, which is what S20
  correctly stopped on; here `main` was ahead, not behind, and neither new commit touched
  `docs/`. **The lesson is the brief's, not the worker's:** a precondition should state its
  substance and offer the command as an example of how to check it, not fuse the two, or every
  commit Andrew makes between turns can invalidate a brief that is still correct. Dispatch
  briefs are written that way from here.
- **Andrew's own commits now get a place in section 4.** `23157ef` and `ecb244f` landed between
  turns and had no row, which left section 6 stale for a reason no ledger entry explained.
  They get a table below the session ledger rather than a fabricated session number, because a
  session number implies a brief and a close-out report that do not exist.
- **Two design decisions came in on those commits and are recorded here rather than lost in a
  commit message.** The IMU moves onto a solderable mini breadboard on standoffs, so it can be
  built and tested off the robot, costing the Pi-M shelf 24 mm and the budget about 8 g. And
  the TPU track loop is printed as a circle rather than in its running shape: a printed part is
  stress-free in the shape it was printed, so print shape sets the curvature each band element
  is relaxed at, and a circle minimises the worst swing every element sees around the loop —
  0.0328 mm⁻¹ against 0.0500, taking outer-fibre strain through a rib from 8.75 % to 5.73 %.
  Mean curvature is fixed at 2π/path for any closed curve, so the circle is optimal and its
  radius is not a free choice. Cost: one loop per plate instead of two.
- **The mass moved and `BOM.md` did not follow.** 1531 g to 1542 g, still 58 g under the
  ceiling, gate unaffected. `BOM.md` states the old figure in two places. This is the same
  defect O13 corrected four days ago from a different stale number, which is the argument for
  quoting the script rather than the paragraph. O23.
- **The working tree was dirty for the first time from something other than a session.**
  FreeCAD, open on the desktop, saved and rotated its backups mid-turn. It also exposed that
  four `.FCBak` files are tracked, which is why a routine rotation reads as a deletion. O27.

### 2026-08-26 (late) — S21 and S21-O — D7 done, and the maintenance queue emptied

- **The ordering rule worked the first time it was used.** S20-O handed Andrew S19's corrected
  block ahead of its own state commit; he ran it, `382ee10` and `a1f0111` landed, S21's
  precondition was true when it looked, and S21 did the work. The rule taken from S19-O's
  half-landed handover is therefore not just sound in principle — it is the difference between
  S20 stopping and S21 finishing, on the same brief, one day apart. It is applied again this turn.
- **S21 is the second close-out in this project with no factual error in it**, after S19. Every
  one of its eight definition-of-done checks reproduced independently: the two `1807` lines, the
  `#5218` count of 3, well-formed XML, `.claude/` ignored and gone from porcelain status, CR count
  0 on all three files, 48 tests passing, and `check_harness_nets.py` at exit 0 with all six checks.
- **O4 is answered, and the answer is worth more than the item.** The addon returns an XML-RPC
  `Fault` saying `get_rpc_status` is not supported — not a timeout, so FreeCAD was running with the
  addon loaded and it simply predates the method. The orchestrator spent a second probe rather than
  take the claim on trust, and got the identical fault. The general lesson is the one S21 drew:
  **the Cowork bridge advertises `mcp__remote-devices__freecad__get_rpc_status` with a full schema
  and the addon behind it refuses the call.** A tool appearing in the inventory says nothing about
  whether the thing behind it implements it. O4's owner moves from Worker to Andrew, because
  updating a Windows FreeCAD addon is not something a session can do.
- **Section 6 has claimed for three months that the checkout is LF, and it is not.** S21 noticed
  it on one file while normalising `.gitignore`; the survey this turn puts the number at 75 of 152
  tracked files with `i/lf w/crlf`, and **zero** with `i/crlf`. The important half of the claim —
  every blob is LF — is true and verified. The conclusion "`git status` is genuinely clean" is also
  true, but for the wrong reason: `core.autocrlf = input` normalises on read. Recorded as O21 and
  the recommendation is to leave it alone. What it changes is a habit, not a file: **a working-tree
  CR count is not evidence about a commit.** That is already `docs/ORCHESTRATION.md` section 6's
  rule, and this is the first time this file has had a concrete count behind it.
- **`ORCHESTRATOR_PROMPT.md` is not in this working copy at all.** Section 6 listed it beside
  `.claude/` as untracked content that "lives in the working tree". It does not; it was not carried
  through the 2026-08-23 migration. Nothing is lost — the archived copy at
  `docs/archive/ORCHESTRATOR_PROMPT_2026-08-22.md` is tracked — but the row was describing a file
  that is not there, and O20's fix would have been widened to cover it if S21 had not checked.
  S21 declined to widen a cosmetic item mid-session and reported it instead, which was right.
- **D7 closed; nothing replaced it on the critical path.** D8 is queued as explicitly optional: a
  Pi-V runtime document to match the Pi-M one S19 wrote. It moves no gate and it is being written
  down as maintenance rather than dressed up, which is the standard D7 itself set. The only thing
  that moves this project is the printer.

### 2026-08-26 — S20 and S20-O — a handover that half-landed

- **S20's stop is upheld and was the right call.** Its three scope items are two text edits and
  a read-only probe, none of them touching a file S19's block touches, and it could have done
  them. Doing them would have cut `docs/drawing-and-figure-fixes` from `ebdea9e`, leaving two
  branches to land in an order nobody chose and `main` briefly carrying a documentation revision
  while still missing the Pi-M fix this file already recorded as closed. The brief said stop and
  the brief was right. S20 also declined to spend O4's single read-only FreeCAD probe past the
  stop, reasoning that carrying anything past a stop is how a stop stops meaning anything. Both
  calls stand.
- **The failure is in the handover, not in any session.** S19-O handed Andrew two things at once:
  S19's two-commit block and its own state commit. One landed. Nothing in the protocol says which
  order they go in or that the state commit depends on the other, and a state document that
  records work as done ahead of the work landing is the same shape of defect as a gate met against
  an unbuilt artifact. **The rule taken from this: an orchestrator's state commit does not go to
  Andrew ahead of the worker block it describes.** Either they are handed over as one ordered
  block with the worker's commits first, or the state entry is written as pending and corrected
  next turn — which is what section 4's `pending` column already exists to do.
- **Two defects found in S19's command block before it ran.** Its first commit message claims
  “Closes O15 and O16”; O15 cannot be closed by a commit and this file has said so since
  2026-08-25, so that message would have put a false claim into permanent history. And the block
  creates `fix/pi-m-bringup` and never merges it, so running it verbatim would leave `main`
  unchanged and D7's precondition still false. Both corrected in the block handed over this turn.
  S20 reproduced the block verbatim, correctly — it was reporting what existed, not re-authoring
  it — and verbatim reproduction is exactly how a defect survives a session that is being careful.
- **O16 and O18 requalified from CLOSED to fixed-not-closed**, on S20's recommendation. The
  strike-through convention this file uses for resolved items reads as done at a glance, and both
  were struck against a commit that does not exist. O15's phrasing was already right and is the
  model.
- **O19 widened, not re-opened.** Line 73 of `docs/HARDWARE_drive_bringup.md` carries the same
  1807 figure as line 16 and puts it beside `gpiozero.RotaryEncoder`, which is the decoder that
  makes it wrong. S19 found line 16 and O19 named only line 16; the grep that would have found
  both was not run until this turn.

### 2026-08-25 — S19 and S19-O — Pi-M bringup salvage, and the notes leaving the repository

- **O15 stays open until the script runs on Pi-M.** S19 fixed it, `bash -n` parses it, and the
  reconstructed post-commit tree passes every check in the repository — none of which is
  evidence that `python3-lgpio` installs on Trixie or that a repaired `pyvenv.cfg` is reached
  from the venv. The apt route has a witness in the 2026-07-12 bench session; the `sed` repair,
  the `pip install -r` path and the added verification imports have none. Closing it on a parse
  would be the same shape of error as a gate met against an unprinted part, which this project
  has already made once. S19 recommended exactly this and it is upheld.
- **The setup script reads `requirements-motion.txt` rather than carrying its own list.** Two
  lists drift, and that drift is precisely what produced O15: a correction sat in a root note
  for six weeks while the script kept the defect. The script now hard-depends on being run from
  a checkout and fails early with the missing path named. No inline fallback list was written,
  deliberately — a fallback list is the second list again.
- **A `--system-site-packages` venv on Pi-M is accepted with its cost named.** It exposes every
  apt Python package to the venv, not only `gpiozero` and `lgpio`. On a single-application Pi
  Zero 2 W that is small, and it is the route the bench actually proved. The alternatives are
  worse: a `.pth` into `dist-packages` is the same exposure by a less legible mechanism, and
  building `liblgpio` from source adds a compile step to a provisioning script for a package
  apt already ships.
- **Pi-M pins as floors, Pi-V pins exactly, and the difference is deliberate.** Pi-M installs
  from the piwheels mirror, whose available versions can lag PyPI, so an exact pin risks being
  unsatisfiable on the target for a reason unrelated to the project. Neither file is verified
  against its Pi and both say so.
- **`docs/HARDWARE_pi_m_runtime.md` keeps its name.** S19 flagged that venv paths and pip
  packages are not hardware and offered `docs/PI_M_RUNTIME.md` instead, asking to be overruled
  while the file was one commit old. Upheld as written: the `HARDWARE_` prefix is what groups
  the Pi-side reference documents, the file does carry the device-tree overlay and GPIO access,
  and a rename costs a git write for no function.
- **The five root notes and `MEMORY.md` leave the repository — with one thing salvaged that S19
  proposed to drop.** `sandbox-no-torch.md` carries the *mechanism* behind a rule the canonical
  documents only assert: the proxy 403-blocks `download.pytorch.org` and the default PyPI
  `torch` is a CUDA build that fails import on `libcublasLt.so`. S19 judged it not worth
  carrying and invited an overrule. Half-overruled: the mechanism is one sentence and answers
  the question a future session will actually ask — *why not just install torch* — so it is
  folded into `docs/ORCHESTRATION.md` section 7. The install list is re-derivable and goes.
- **Queue numbers are frozen.** D3 was inserted on 2026-08-25 and D3–D5 became D4–D6; two
  renumbers in three days would make every citation of a queue number unreliable. New items now
  take the next free number and the dispatch order is stated in prose. D7 is the maintenance
  session and is the only ready-now item.
- **`PROJECT_STATE.md` is stale in the same two places on every turn, and the cause is
  structural.** The header and section 6 have been wrong at three consecutive turns. It is not
  carelessness: this file is written *before* the commits it describes, because every git write
  is Andrew's and happens after the turn ends, so the SHAs it records are correct only once he
  runs the block. The countermeasure is procedural, added to `docs/ORCHESTRATION.md` section 4 —
  an orchestrator turn's first act after reading is to reconcile the previous turn's `pending`
  entries against `git log` and correct the header and section 6 from `git for-each-ref`, before
  it does anything else.
- **S19 created no branch and committed nothing, which is correct but leaves state describing a
  repository that does not exist yet.** Section 6 says so plainly rather than reading as though
  the fix has landed. If Andrew runs only part of the command block, the file is wrong in a way
  the next turn must catch — which is the reconciliation step above.

### 2026-08-25 — S18 and S18-O — Repository hygiene, and what the hygiene pass turned up

- **The two verification scripts S18 wrote are not committed, and that is now settled rather
  than left open.** `check_vision_deps.py` and `check_memory_index.py` proved two
  definition-of-done items and were both demonstrated failing on the real defect, which makes
  them defensible. They stay out. `check_memory_index.py` becomes pointless the moment D3
  removes `MEMORY.md` and the notes behind it, and `check_vision_deps.py` would enter the tree
  as a guard with no failing input and nothing invoking it — which is how `mass_budget.py`
  came to crash silently for two months. A guard earns its place by being run, not by
  existing. If Pi-M's dependencies grow past one file, revisit.
- **`pyproject.toml` deliberately carries no `[build-system]` section.** Johnny 5 is deployed
  by copying `src/` onto a Pi. A build-system table would make the repository look installable
  and invite `pip install -e .`, which nothing here supports.
- **`MEMORY.md` was made to match the files rather than the files renamed to match it.** The
  rename is tidier and impossible from a session — the mount does not rename — and it is a git
  write either way. The index now spells the names as git spells them, which is the fix that
  survives whatever happens to the files. It also gained a header saying it is an index and
  not a summary, pointing at `docs/ORCHESTRATION.md` section 9. Deleting one stale line and
  leaving the index otherwise inviting would have fixed the instance and not the shape, and
  this is the exact file that was read in place of its documents on 2026-08-21.
- **Orchestrator turns are logged with an `-O` suffix on the worker they close out.** See
  section 4. Adopted because `06783fe` and `769c618` were sitting in `main` attributable to no
  session, and S18's report read all four of the post-S17 commits as S17's work.
- **A definition of done that greps for a superseded string must exclude `docs/archive/` and
  `docs/reports/`.** Both are records of the era in which the string was correct. S18's grep
  returned twelve hits that were all correct behaviour, and the operative test had to be
  restated after the fact. Added to `docs/ORCHESTRATION.md` section 3.
- **The fast-forward merge is accepted practice and `CLAUDE.md` is the document that is
  behind.** See section 6. Not changed in `CLAUDE.md` this turn; recorded so the divergence is
  deliberate rather than drift.

### 2026-08-25 — S17 — Power harness schematic, and Andrew's rulings on the motor, cables and fuse

- **The harness is a hand-authored SVG, not KiCad.** No KiCad or KiPilot tool was exposed to
  the worker session, so the queue entry's claim that KiPilot "is already set up" did not hold
  from inside a session — it is a fact about the desktop, not about a dispatched worker. The
  brief pre-authorised the fallback and it was taken without asking. The reasoning stands
  independently: this is an interconnect drawing whose consumers are a bench and a parts
  order, and `docs/diagrams/bench_full_schematic.svg` already establishes a diffable house
  convention for exactly that.
- **Passives are properties of a net, not endpoints of their own, and `BOM.md` now carries
  them.** A series resistor or bulk capacitor does not terminate a conductor, so modelling
  them as endpoints would have forced an exemption list into the endpoint check and weakened
  it. Andrew approved adding a resistor line to `BOM.md`; the guard now asserts that every
  value called out on a net is a `BOM.md` line item. Without that line the harness could have
  been drawn, approved and ordered against with five components missing.
- **Rail names carry in the net name, and every rail-prefixed net must declare a current** —
  `[peak N A]` or `[reflected]`. A forgotten figure fails loudly instead of summing to zero.
- **Inter-rail feeds are `[reflected]`, not peaks.** Charging buck input current to VBAT as
  well as to the rail it supplies would double-count it and make the net table irreconcilable
  with the Power Budget, which models rails as loads. Reflected current is computed once, in
  the fuse check.
- **The net table may exceed the Power Budget by up to 0.25 A per rail and may never fall
  below it.** The table is finer-grained than the budget — it pays for the encoder supplies
  and the TB6612 logic supply that the budget rolls into other rows. A missing load makes the
  table fall short and fails; an invented one blows the allowance and fails.
- **Two derived 3.3 V supplies come off the Pi header pins rather than a third converter.**
  Their combined 0.09 A is checked against a 0.25 A ceiling for a Pi Zero 2 W 3.3 V pin, which
  is an assumption and is labelled as one in both the document and the guard, because `BOM.md`
  states no such rating.
- **The battery sense divider is 100 kΩ over 47 kΩ, downstream of the master switch.** 8.4 V
  divides to 2.685 V at 57 µA, inside both the 3.3 V VDD and the ±4.096 V full-scale range.
  Placing it after the switch means telemetry reads zero when the robot is off, which is
  correct behaviour; the alternative leaves a permanent load on a pack that looks disconnected.
- **Encoder returns go to Pi-M, not to the star ground,** following their own signal pair back
  in the same six-conductor cable, so a signal return is never in parallel with a motor return.
- **Ground is drawn as a bus and wired as a star,** per the bench drawing's own convention and
  labelled on the drawing so nobody builds a daisy chain from it.
- **O6 was settled at the bench, not on paper.** The Pololu catalogue fixes #5218 and #5219 as
  the same 150:1 HPCB 12 V 12 CPR motor differing only in connector orientation, both $32.45.
  `BOM.md`'s part number was right and its price was wrong; corrected to $65 the pair. Andrew
  then confirmed with the parts in hand that the #5219 was bought deliberately as a fit test,
  that the side-connector variant does **not** fit the chassis cleanly, and that **both drive
  motors are #5218 and #5218 is the only drive motor this project will use.** That converts
  the surviving `#5219` references from a contradiction into plain errors (O12).
- **The 6-pin JST SH encoder cables ship with the motors and need no `BOM.md` line.** The
  connector type is recorded in the net table so a replacement can be identified. The sentence
  S17 first added saying they are sold separately was wrong and was corrected in `678c68a`.
- **The 7.5 A inline blade fuse stands, unchanged.** See section 8; the report's framing of
  this as a decision owed before ordering overstated it, and Andrew said so.
- **A guard is only worth what its failures prove.** S17 ran nine single-edit mutations
  against copies of the three files and caught all nine. The orchestrator independently
  reproduced four of the nine on 2026-08-25 rather than taking the table on trust. This is the
  direct countermeasure to `validate.py` reporting ALL CHECKS PASS while three defects reached
  the print bed.

### 2026-08-24 — S16 — Orchestration protocol distilled

- **`docs/ORCHESTRATION.md` created and `ORCHESTRATOR_PROMPT.md` retired** to
  `docs/archive/ORCHESTRATOR_PROMPT_2026-08-22.md` behind a frozen header, its durable half
  distilled and its ground-truth section dropped as factually wrong. The standing orchestrator
  turn opener, the close-out-report-as-file convention and the proportionality rule were added.
  The session recorded none of this itself; the entry is reconstructed from commit contents.

### 2026-08-23 — S15 — Orchestration, git reconciliation, repo migration

- **`PROJECT_STATE.md` created as the sole authority.** State had been spread across five
  overlapping stores — `CLAUDE.md`, `INITIATING_PROMPT.md`, `phases/*.md`, `README.md` and
  project memory — of which only `INITIATING_PROMPT.md` had the right answer, and it sat in
  no mandatory read path and was committed per-branch, so its truth depended on which branch
  you were standing on. That is the disease that produced the S14 failure.
- **Git collapsed from five branches to one.** `main` was force-updated onto
  `fix/chassis-tub-defects`, which despite its name carried the entire project — the motor
  driver, encoder calibration, the locomotion policy in the motion loop, the MuJoCo
  environment and the whole Phase 00 rework, 22 commits and 142 differing paths ahead of
  `main`. The other three branches were strictly its ancestors and were deleted. Anyone
  opening the folder had been seeing a Phase 00-era tree.
- **`main`'s one unique commit was retired, not merged.** `937311c` committed 64 binary
  training artifacts, 7.9 MiB, that the trunk's own `.gitignore` says should not be tracked.
  Preserved as tag `archive/runs-937311c` so nothing is lost, and dropped from the tree.
- **The deployed policy is now tracked.** `policies/locomotion_v3.onnx`, 21,680 bytes, was
  gitignored while the intermediate checkpoints were committed — the gate artifact existed as
  one file on one disk. `*.onnx` and `policies/*.onnx` came out of `.gitignore`, replaced by a
  narrow `simulation/chassis/smoke_run/*.onnx` rule.
- **Commit authority granted, exercised once, and handed back.** Andrew granted
  commit-with-prior-approval on 2026-08-22. The single commit made under it produced a CRLF
  blob in an all-LF repo and stranded a lock file that blocked Andrew's own git. Reverted the
  same day on the orchestrator's recommendation: **the agent edits and verifies, Andrew runs
  every git write.** The authority cost more than it saved.
- **Line endings settled at the config level.** The chronic "whole repo shows as modified"
  noise, present in every session and worked around with `--ignore-cr-at-eol` each time, was a
  CRLF worktree against LF blobs. The new clone sets `core.autocrlf = input`; the tree is now
  genuinely clean. This is the flag that concealed the CRLF defect above, so it is now a rule
  that it may read diffs but never certify a commit.
- **Working repo moved out of Nextcloud** to `C:\dev\johnny5`. Verified by identical root tree
  SHA (`6755a6f`), 144 tracked files, all tags, 48/48 tests. **The stated reason was wrong** —
  the stale git locks were blamed on Nextcloud sync, then reproduced immediately in the new
  location, proving the cause is the Cowork device mount's inability to delete files. The move
  is still net-positive for the LF fix and for losing the space in the path, but the root-cause
  claim did not survive contact. Whether Nextcloud independently caused the older symptoms
  (commit `baf646c` "remove stale git lock", "unknown index entry format", truncated writes)
  is **unknown and should not be asserted.**
- **Orchestrator/worker split established.** One session owns state and dispatches bounded
  briefs; workers return close-out reports that are verified against the repository before any
  state update. Workers never write their own successor's brief, which is exactly how S14 failed.
- **The competing state documents were demoted the same day.** `INITIATING_PROMPT.md` moved to
  `docs/archive/INITIATING_PROMPT_2026-08-22.md` behind a frozen header; `README.md`'s Status
  section became a pointer; all seven phase documents gained a pointer and Phase 00 lost its four
  gate-status lines and all four "next session — initiating prompt" blocks. Those blocks were not
  merely stale — copying one is precisely how S14 failed, so they are gone rather than corrected.
  The Session 04 handoff's malformed headings were fixed and its stale "1655 g against a 1.6 kg
  ceiling" paragraph deleted; the measured figure is 1531 g. `PHASE_05_INTEGRATION.md`'s
  documentation task, which instructed a future session to "mark gate status on each" phase
  document, now points at `PROJECT_STATE.md` instead — it would have rebuilt the disease at Phase 05.
- **`ORCHESTRATOR_PROMPT.md` split and retired.** The document that created this role had
  become the thing it warns about: its section 2, "Ground truth as of 2026-08-22", carried
  fourteen references to facts this session had just made false — five branches, a trunk named
  `fix/chassis-tub-defects`, `937311c` on `main`, the Nextcloud path. Handed to a future session
  it would have taught stale ground truth, which is precisely the failure mode it was written to
  prevent. Its durable half — dispatch and close-out protocols, the integration lock, git
  mechanics, environment hazards, operating style, and the account of how the project fails —
  is now `docs/ORCHESTRATION.md`, which carries no project state by construction. The original is
  archived at `docs/archive/ORCHESTRATOR_PROMPT_2026-08-22.md`. Its section 10 open items were
  already in section 7 above, so nothing was dropped.
- **The orchestrator is a role, not a session.** Recorded here because it is a design decision
  with a failure mode: it is instantiated fresh from the repository each time and stops when its
  turn is done. A long-lived orchestrator accumulates beliefs that drift from the repository,
  which is the original disease wearing a badge. What the split actually depends on is narrower
  than continuity — no worker edits this file, and no worker writes its own successor's brief.
  The signal that this is not working would be a close-out report accepted without verification,
  or two consecutive sessions disagreeing about position; section 10 is where that becomes visible.
- **Session cadence fixed.** Orchestrator turns and worker turns alternate, and briefs are
  written by orchestrator turns only — the rule is that no session writes the brief for the work
  that follows its own, not that no session writes briefs. Worker close-out reports go to
  `docs/reports/J5-S<nn>.md` as files, so the orchestrator verifies an artifact against the
  repository instead of a report ferried between sessions. `docs/ORCHESTRATION.md` section 2
  carries the standing invocation that opens an orchestrator turn.
- **`CLAUDE.md` amended.** A Project State & Orchestration section names `PROJECT_STATE.md` as sole
  authority and fixes the worker read path; the agent-boundaries paragraph records why commit
  authority was returned and what the environment does to git writes; the intra-phase iteration-tag
  convention was removed rather than left standing as a rule the project has never followed.

### 2026-08-22 — S14 — the failure that created the orchestrator role

Recorded here because it is the reason for this document's existence. The session finished
Phase 00 work, was asked to write the next session's initiating prompt, opened `MEMORY.md`,
read the index line "Phase 02 locomotion — Tasks 1–5 done, 6a/6b remaining", **never opened
the file behind it**, and wrote a **Phase 01** initiating prompt for a phase that had closed
on 2026-06-22. Caught only because Andrew ran it and the receiving session pushed back.

Three conditions made it possible, all since addressed: an index was read in place of the
document it summarises; the document that had the right answer was in no read path; and truth
was per-branch. Countermeasures: read the file not the index, keep exactly one authority and
put it in every read path, verify against the repository at session start and before every
state update, and log each verification in section 10.

Related and equally worth remembering: `mass_budget.py` crashed silently on a malformed CSV
row from S02 to S13, and **every mass figure quoted in that window was produced by hand, not
by the script.** When a number appears in a report, ask which script printed it.

### 2026-08-21 — S13 — drivetrain designed, Phase 00 re-closed at 1531 g

- **Centre-guide lug track, not full-width teeth.** One lug row down the middle of the band;
  the sprocket pockets drive it, the idler and road wheels ride the smooth lands either side.
  This is what lets a ø24 road wheel and a ø40 sprocket share one track, and the lug row
  doubles as the derailment guide and the axial stop keeping wheels on their rods.
- **Lug pitch is the sprocket's tooth pitch by construction**, and the loop closes at whatever
  straight run 29 lugs demand — 119.38 mm, not the tub's nominal 120. Engagement error cannot
  accumulate around the loop; the 0.62 mm and all pretension are absorbed in the idler slot,
  where 1 mm forward is 2 mm of path and 0.55% strain.
- **Idler on a slot with a clamped carrier, not a fixed hole.** The carrier bears on two bosses
  rather than the 2.4 mm wall, which cannot take an M2 thread.
- **Road wheels on a skirt.** ø24 reaches the band only from a 15.5 mm axle line, 2.5 mm below
  the tub underside, so the earlier "either ø40 or axles down to z 15.5, params only" was not
  available: at 15.5 there is no wall to drill, and ø40 will not fit between a ø40 sprocket and
  a ø40 idler 120 mm apart. Each rod gets a local pad hanging off the wall, thickened inboard
  to 5.4 mm of bearing length.
- **Road-wheel spacing became an explicit pitch.** The old `wheelbase * 0.6` formula put two ø24
  wheels exactly tangent. Nothing in the parameter sheet showed it; the first build-time rim-gap
  check caught it on the first run. At 40 mm pitch the four ground contacts fall in even quarters.
- **Rear caster became a fixed anti-tip tail.** It never assembled — pivot bosses bored along Y
  at x = ±16 against an arm eye at x = 0 — and a ground-riding caster would scrub on every tank
  turn and lift weight off the tracks for a margin that comes from where the roller sits, not
  from it being sprung. A level boom holding a ø25 roller 4 mm clear engages at about 2° of
  rearward pitch, keeps the 33°→54° margin, and drops the spring, the pivot and 7 g.
- **One electronics shelf, on columns.** The Pi-M shelf runs 38 mm further aft and carries the
  IMU as well as the Pi, so the tub electronics stack builds up outside the tub and drops in on
  six screws. Two solid 8.4 × 73 mm ribs became three columns a side — an extended rib would
  have been 58 g, columns are 23 g — and the gaps are where wiring crosses underneath.
- **The IMU came back to the centreline.** It was pushed to (35, −25) at S12 only because the
  battery bay ring owned the middle of the tub floor; off the floor there is nothing to dodge,
  so the accelerometer's lever-arm correction disappears with it.
- **Herringbone treads relieved out of the band, not added onto it.** 24 chevrons, 1.5 mm deep,
  3.5 mm ribs at 25° from transverse. Cutting them out of the 3.5 mm envelope keeps the tip
  radius at 23.5, so ride height, rolling radius and ground speed are untouched — proud grousers
  would have taken about 6% off a drive with roughly 1× continuous torque margin. The band drops
  to 2.0 mm continuous, nearly halving outer-fibre bending strain at the sprocket. The 25° arm
  angle is a printing constraint first: the loop prints with its width vertical.
- **Segmented chevron arms, after the tread guard caught floating geometry.** Built as two
  straight 15 mm bars, each arm lay tangentially on the 22 mm valley radius, so 1.6 mm of every
  arm end floated free of the band on every wrapped section and the tip stood 1.36 mm proud. The
  single-solid check cannot see that; the tread-tip envelope guard failed instead. Each arm is
  now five short pieces on their own path points, worst chord 0.2 mm.
- **No openings in the tub floor.** The four floor lightening windows are gone: 6.7 g is not
  worth an opening straight into the electronics bay from ground level. The side walls funded it
  instead — six blind pockets a side rather than two, 1.4 mm into a 2.4 mm wall, worth the same
  6.7 g with no opening at all. The tub came out at 161.1 g either way, an exact wash.
- **The anti-tip roller got a TPU tyre.** A bare PLA cylinder is the wrong thing on the one part
  whose job is to catch the robot — hard plastic skitters rather than bites, and is loud. ø20 PLA
  hub inside a ø25 TPU 90A tyre, 0.25 mm interference fit. The tyre carries the outer diameter,
  so the 4 mm float and tip-margin geometry are untouched, and it prints in filament already
  specified for the tracks. 5.6 g assembled against 6.0 g bare.
- **Shell walls 2.4 → 2.0 mm on torso and head.** A 150×90×88 shell at 2.4 mm is inherently
  206 g and there was nowhere else worth more than about 25 g. 2.0 mm is five perimeters at 0.4.
  Torso 239 → 218 g, head 208 → 181 g.
- **Six defects in torso and head, found by reading the scripts rather than by any check.** The
  left shoulder had no shaft hole or horn recess at all — `xface - sgn*(WALL+3)` is right-handed
  only. Mount bosses ended flush against a lofted taper, meeting it along a line rather than an
  area, so they never fused. Deck bolt bosses were columns standing in a hollow shell. The neck
  riser sat over the open top of the torso with its whole ø34 footprint in mid-air, carrying the
  head and two servos. `lightening()` cut a rod, not a pocket. Pi-V standoffs were anchored to a
  constant y while the back wall leans 6 mm, putting the upper pair through the outer skin.
- **Registration pins need somewhere to be.** Both scripts put split-key pins in free air,
  because the split plane cuts a hollow shell. Both now sit in pads that straddle the split.
- **A boolean can be too tight as well as too loose.** The first shoulder deck was sized to the
  lofted torso cavity exactly: plate and wall agreed to within 0.04 mm, overlapping on one side
  and gapping on the other. FreeCAD ground on the slivers for minutes and never returned. Every
  mating feature now takes a deliberate bite — 1.5 mm for bosses, 0.6 mm for the deck.
- **Mass is measured, not estimated.** `components.csv` carries built-solid volumes for every
  printed part, marked firm rather than soft. `mass_budget.py`'s unquoted-comma crash — present
  since S02 — was fixed here.
- **Closed at 1531 g**, 69 g of headroom, +25% sensitivity landing at 1578 g. Two double-counted
  lines were removed: the neck riser (52.9 g) is fused into the torso solid and the head nod ears
  (7.1 g) into the head, so both were being paid for twice.

### 2026-08-20 — S12 — Phase 00 reopened; tub made printable

- **A gate met against an unbuilt artifact is not met.** Phase 00 closed at S02 on a body that
  had never been printed. The first physical tub had no motor-shaft, road-wheel or idler holes on
  its right wall, motors that could not be inserted, and an IMU pad underneath the battery. Four
  print-and-measure rounds fixed it.
- **Verification moved from parameters into the build.** `validate.py` compares numbers to numbers
  and reported ALL CHECKS PASS while three defects reached the print bed. Boolean guards inside
  `main()` — hole open *and* correct size, keep-out volumes, motor drop position, bearing shoulder
  present — are what catch real defects. Note an overlapping fuse is legal and still returns one
  solid, so the single-solid check cannot see two features claiming the same volume.
- **FreeCAD MCP adopted, running locally.** The neka-nat addon runs inside FreeCAD's own GUI
  process, so it must live on the Windows desktop, not the home-lab LXC. This is what made
  run-the-geometry verification possible at all.
- **Bearings live in the wheel hubs, not the tub walls.** A 10×4 mm 623ZZ pocket cannot fit a
  2.4 mm wall at any sign. Two per idler wheel plus one per road wheel; the wall carries only a
  locating hole. Deletes the problem rather than engineering around it.
- **Idler runs one full-width 3 mm rod, not stub axles.** A stub has 2.4 mm of PLA resisting a
  16 mm cantilever and will wallow out. A rod through both walls is constrained 118 mm apart and
  cannot cock.
- **Drive sprocket rides its own bearing, not the motor shaft.** The 9 mm output shaft cannot
  reach the 75 mm track centreline, and hanging a driven wheel off an N20 gearbox bushing is wrong
  regardless of reach. MR106ZZ pressed into the rear wall from outside; the wall takes the load,
  the motor supplies only torque.
- **Drive motor fixed as Pololu #5218**, 150:1 HPCB 12 V, 12 CPR encoder, back connector — closing
  the S01 side-versus-back question. See O6.
- **Pi-M shelf split into a separate print.** As one piece its underside needed support material
  in a tunnel obstructed by the battery bay ring.
- **Battery bay ring trimmed clear of the cradles and left open aft.** Straps retain the pack; a
  drop-in aft stop is deferred until testing shows it is needed.
- **Hand edits in the FreeCAD GUI rejected as a workflow.** A rebuild overwrites the FCStd and a
  GUI edit does not propagate to `params.csv`, so the defect returns on the next build. Physical
  measurement plus a description is the channel that has actually worked.

### 2026-08-11 — S11 — chassis rebuilt for real; two pre-existing tub defects

- **The tub was building as five solids, not one.** The four deck rim bosses sat at `W/2-6` /
  `Lg/2-6`, putting their outer edges 0.1 mm short of the wall inner faces, so they never fused.
  They would have sliced as four islands floating in mid-air and the deck would have had nothing
  to screw into. Pre-existing since the S02 model. Bosses now overlap the wall by 1 mm, with
  positions shared with `deck()` through `_rim_boss_xy()` so they cannot drift apart again.
- **Those bosses had no pilot bores.** `L.screw_boss()` returns `(boss, hole)` and the caller
  discarded the hole. Also pre-existing.
- **The motor cap overlapped the rear wall by 0.9 mm.** The cradle may run into that wall because
  it is fused to the tub; the cap is a separate part and may not. Cap footprint now derived
  independently of the cradle, clipped to the 12.6 mm free span behind the motor axis.
- **Two build-time guards added:** every printable part must come out as exactly one solid, and a
  cap plus motor proxy placed into the cradle must share zero volume. Both raise rather than export.
- **The deck must be reprinted too**, not just the tub — the rim bosses moved.

### 2026-08-10 — S10 — Task 6a complete; calibration method corrected

- **The 150.58:1 N20 gearbox is not backdrivable at the output shaft.** This supersedes the
  2026-07-16 description of 6a as a hand-rotation test with motors off. The wheel will not turn by
  hand and the force needed would split the gearcase first. Confirmed mechanical rather than
  electrical by detaching the motor from the TB6612 entirely and finding it still locked, ruling
  out the short-brake state that floating pins can leave after `MotorDriver.close()`.
- **`--calibrate` rewritten as a powered measurement.** One wheel at a time at low duty, Andrew
  taps Enter at each pass of a mark, the script least-squares-fits encoder count against revolution
  index. Fitting the slope rather than dividing totals is the point: a constant human reaction lag
  moves the intercept and leaves the slope untouched, so the result does not depend on Andrew's
  reflexes being fast, only consistent.
- **Result: 450.6 counts/output-rev, left/right spread 0.4%.** `COUNTS_PER_OUTPUT_REV` stays at
  **451.74** (3 quadrature cycles/motor-rev × 150.58), because that is fixed by integer tooth and
  pole counts while the measurement carries tap-timing noise. What the measurement settled is the
  question it was designed for: `gpiozero.RotaryEncoder` decodes **1×, not 4×**, killing the ~1807
  candidate. A 4× decode would have been a factor-of-four error in every speed and odometry figure.
- **Motor retention cap designed — the reason the motors were still loose.** `build_chassis.py`
  modelled each cradle as an open-top drop-in slot "retained by a cap" that was never built: no cap
  solid, no export, no fastener provision. The 16 mm cradle left 2 mm either side of the 12 mm slot,
  too thin to tap M2, so the cradle had to change with it. `cradle_w` now derives from
  `motor_cap_screw_cc + boss_od` (27 mm) with four tapped M2 columns per side. The plate is held
  `motor_cap_clamp_gap` above the cradle top so the screws preload the motor into the bore rather
  than bottoming the plate out. The drop-in slot was also exactly `motor_dia` wide — zero clearance
  against a 12 mm motor — and now carries the same `motor_fit_clear` as the bore.
- **`--dwell` added to `scripts/test_motors.py`**: a uniform multiplier on every sleep in the bench
  sequence, replacing ad-hoc long durations that had been edited directly into the Pi's working copy
  and were blocking `git pull`.

### 2026-07-16 — S09 — Tasks 1 and 2 landed; Task 6 split on the mechanical blocker

- **Task 2 activated.** Real `_read_motion_state()` on Pi-M via `src/motion/mpu6050.py` — accel plus
  gyro complementary filter for roll/pitch, gyro-z passthrough for yaw rate, I²C-backend-abstracted
  so it is unit-testable without a Pi — fused with `EncoderReader` odometry.
  `WHEEL_RADIUS_M = 0.0235` m is CAD-derived from `params.csv`, **not bench-confirmed.**
- **Hardware bundled into an injectable `MotionHardware` dataclass** so tests swap in fakes instead
  of touching GPIO, I²C or onnxruntime. MotorDriver enable/disable runs every tick, coordinated with
  the offline fallback state, independent of whether `execute_intent()` is called at all.
- **`idle` deliberately excluded from the locomotion dispatch set** (`move`/`turn`/`arc` only). It is
  a valid `command_from_intent()` input but a no-op for `execute_intent()`; forced stop-on-disconnect
  comes from the fallback state machine, not from intent-level idle.
- **Task 6 split into 6a and 6b.** 6a is a stationary bench test unaffected by the build state and
  could run immediately. 6b is blocked: loose motors have no rigid tread contact geometry, so "drives
  straight" is not measurable, and breadboard jumpers are expected to work loose under tread
  vibration — doing 6b now risks chasing a connection fault instead of a real bug.
- **Nextcloud mount truncation hit again** — the Edit tool silently truncated a test file mid-write,
  caught by a `SyntaxError` on the next run. Reinforces: author in `/tmp`, copy over, verify by md5.

### 2026-06-26 — S07/S08 — Phase 02 simulation and policy track

- **Treads modelled as four driven wheels**, front and rear per side spanning the wheelbase, **not**
  a deformable belt. A single wheel per side collapses the fore-aft contact patch and the tall robot
  nose-dives. DC motor is a torque actuator (`gear = stall/2` per wheel) plus joint
  `damping = stall/(2·no_load)` for brushed torque-speed droop.
- **Geometry is locked to `params.csv`** via `simulation/chassis/params.py`; the MJCF is generated by
  `build_mjcf.py`. **Do not hand-edit `johnny5_chassis.xml`.** Measured envelope ~0.30 m/s forward,
  ~0.34 rad/s in-place yaw (skid-steer resistance-limited); env caps V_MAX 0.28, W_MAX 0.30.
- **SB3 PPO, 2×64 MLP, command-conditioned** (forward/back/turn/arc/stop). **CPU-only on the
  desktop** — the net is too small to benefit from the 3080 and CPU skips CUDA setup. PyTorch and SB3
  cannot be installed in the agent sandbox, so training is a desktop step; `cem_smoke.py` is the
  torch-free in-sandbox check. Three seeds at ~15 min each; best exported to `locomotion_v3.onnx`.
- **Two export bugs fixed.** `VecNormalize.load(venv=None)` crashes because it needs a live venv, so
  the saved stats are read with a direct `pickle.load`; newer PyTorch defaults to the dynamo ONNX
  exporter which needs `onnxscript`, so `dynamo=False` forces TorchScript.
- **The 9-element observation MUST match `env._obs()` order and normalization exactly** — the ONNX
  bakes in VecNormalize. The sensor-to-channel map is in `TUNING.md` under "Observation
  reconstruction on Pi-M".
- **No accelerometer part needed** — the BOM's MPU-6050 is a 6-axis IMU. Roll and pitch come from
  accel/gyro fusion; no magnetometer, so yaw is rate-only, which is fine for locomotion.
- **BOM Section 1 pricing flag:** drive motors ~$32.45 each against the BOM's implied ~$23, running
  Section 1 about $25 over. See O6.

### 2026-06-22 — S06 — Phase 01 gate closed

- **LiteLLM virtual key minted** on the AOS proxy, alias `johnny5-vision`. Required standing up
  DB-backed key management on the proxy (a new Postgres DB on sn-pg-aos) — previously config-file
  only with no key store.
- **Vision model `vision-batch` → `llava:7b` on ms3** (192.168.1.225), a CPU-only Ollama node chosen
  so vision inference does not contend with desktop GPU work. Expect 15–40 s per image, longer on
  cold load; `LITELLM_TIMEOUT` raised from the 8.0 s placeholder to 60.0 s accordingly — the old
  default would have aborted every call before the model responded.
- **Gate met in full**, with the offline-fallback caveat recorded in section 3.

### 2026-06-20 — S03/S04/S05 — infrastructure stood up

- **Mosquitto chosen over the existing RabbitMQ server.** RabbitMQ lacks native retained-message
  semantics, which the `johnny5/offline` and heartbeat topics rely on, and would have required
  re-implementing that behaviour in application code. Deployed to a Proxmox LXC, not Docker, per
  preference. Broker at `192.168.1.227`.
- **LiteLLM reused, not rebuilt** — `http://192.168.1.223:4000/v1`, the existing Agentic OS server,
  per `CLAUDE.md`'s "Johnny 5 is a consumer of that infrastructure". A separate virtual key for
  usage and cost isolation.
- **Both Pis on Raspberry Pi OS Lite 64-bit (Trixie)**, user `administrator`, static IPs
  `192.168.1.217` (motion) and `192.168.1.218` (vision), set via `nmcli` inside the router's
  reservation block. Configured through NetworkManager because dhcpcd is inactive on this OS
  version. *Caveat: the profiles are netplan-managed, so a future `netplan apply` could regenerate
  them and revert the static IPs. Flag it if they mysteriously revert.*
- **SSH key auth deferred** after two failures in sequence: mDNS not resolving `johnny5-motion`
  without `.local`, then Devolutions RDM reporting "entry's public key doesn't match" — which is a
  stale **host** key cache, not a client auth-key problem. Both cards reflashed with password auth.
  See O2.
- **`dtoverlay=disable-bt` must be edited into `/boot/firmware/config.txt` directly.** A piped
  `echo … | sudo tee -a` was typed into the file as literal text rather than executed, so the
  overlay never loaded and `/dev/serial0` stayed on the mini-UART — baud drift risk under CPU
  frequency scaling, bad for Feetech servo comms. **Lesson: do not pipe shell commands as
  instructions into a file edit.**

### 2026-06-18 — S02 — body baselined in FreeCAD (Phase 00 first close)

- **Parallel tracks confirmed** — the splay in the reference photographs reads as camera perspective.
- **Servos 4 → 6 SCS0009**, adding head nod (#5) and articulated brow roll (#6). Same bus, new IDs,
  no extra GPIO; 6 V rail ~3 A within the 5 A buck. +$22.
- **Rear trailing swiveling sprung caster added** — rearward and incline tip margin 33° → 54°, +33 g,
  +$5. *Superseded at S13 by the fixed anti-tip tail.*
- **Powered waist rejected for V1.** SCS0009 cannot hold the 531 g upper body (5.4 versus 2.3 kg·cm),
  needs STS3215 or a lead screw, +116 g putting worst case at 1662 g **over** the ceiling, 6 V rail
  to ~4.5 A near the buck limit, +$26, for ~7° of decline gain not needed indoors. Its value is
  expression, not stability. Interface left **lean-ready** — reserved pivot bosses and an actuator
  pad — so it is a bolt-on V2.
- **Budgets at close:** mass ~1321 g (83% of ceiling), height ~395 mm, new spend ~$325–365. *These
  figures were not produced by `mass_budget.py`, which was already crashing — see S14.*

### 2026-06-17 — S01 — hardware selected, BOM approved

- **Scale and ceiling:** floor-roaming, ~38–42 cm, assembled-weight ceiling **1.6 kg**.
- **Drive — Path A:** N20-class 12 V 150:1 encoder motors plus TB6612FNG, battery-direct on 2S.
  Chose compact, light, cheap and clean-logic over torque margin; accepts ~0.13 m/s and ~1×
  continuous torque margin. **Contingent on the 1.6 kg ceiling holding.**
- **Encoders: yes** — closed-loop driving plus real velocity data for Phase 02 training.
- **Battery: single 2S LiPo, dual regulation.** Treads: **printed TPU.**
- **Servos: 4× SCS0009** on one half-duplex bus via a Waveshare Bus Servo Adapter, with a shoulder
  utility-box tilt servo added. Arms kept light (≤50 g, ≤90 mm lever) to stay within rated torque.
- **Utility box mounts to the torso shoulder with its own servo**, so it never loads the arm servos.
- **Audio consolidated on Pi-V**, freeing Pi-M's I²S. Needs a custom `simple-audio-card` overlay
  because stock mic and amp overlays conflict. See O1.
- **LEDs:** mouth on Pi-V (SPI, audio-synced); eyes, battery gauge and status chained on Pi-M (SPI).
  A custom layout replaces the GrowBot ring.
- **Power: three rails** — motor battery-direct, 5 V buck, 6 V servo buck — plus an inline 7.5 A fuse
  and a TB6612 STBY interlock so motors are off on boot and after a crash. **Servos must be
  regulated**: 8.4 V at full charge exceeds the SCS0009's 7.4 V maximum. Battery sensing via ADS1115
  drives the gauge, a low-voltage cutoff and telemetry.
- **Deferred levers, not in V1 spend:** motor-rail boost to ~9–10 V if the drive proves underpowered;
  STS3215 upgrade if the arms lack authority; Path B (25D motors, higher-current driver); V2 tendon
  gripper; Dynamixel XL330 alternative; elbow servos.

---

## 10. Verification log

| Date | Verified against | What was checked | What was found wrong |
|---|---|---|---|
| 2026-08-23 | `main` @ `049494b`, and the remote | Full re-derivation of project position, git topology, document inventory and the contradiction list in the orchestrator brief. Branch ancestry, tag targets, `937311c` contents and byte count, tracked-versus-ignored artifacts, `.gitignore` behaviour, worktree cleanliness, the 48-test suite, and the migrated clone's root tree SHA against the original. | The brief's claim that `INITIATING_PROMPT.md`, `README.md`, `BOM.md` and `PROTOCOL.md` were missing from `main` — all four were present. The brief's all-branch merge base (`428d53f`, tag `v0.0`, not `0b13d84`). `INITIATING_PROMPT.md`'s decision log ended at 2026-08-11 and was missing Sessions 03 and 04 entirely, so the migration into section 9 needed two sources. `docs/kipilot-mcp-setup.md` was absent from the brief's inventory. The Pololu #5218/#5219 contradiction (O6). Three repository defects not previously recorded: no pytest config (O7), undeclared vision dependencies (O8), and the loose root notes (O10). |

| 2026-08-25 | `docs/power-harness-schematic` @ `678c68a`, and `main` @ `344c8b7` | The `docs/reports/J5-S17.md` close-out report against the repository. Every claimed file present on the claimed branch by `git cat-file`, at the claimed size (the SVG at exactly 65,827 bytes); `scripts/check_harness_nets.py` md5 identical in worktree and blob to the report's `cb3f5166…`; all five text blobs CR-free; the guard rerun from the repository root, exit 0, reproducing the report's output verbatim including all six checks and every current figure; four of the report's nine mutation classes independently reproduced in a scratch tree, each failing the intended check with the intended message; the SVG parsed as well-formed XML; and every claim about `BOM.md`, `docs/HARDWARE_drive_bringup.md`, `docs/diagrams/bench_full_schematic.svg` and `simulation/chassis/TUNING.md` checked in place. Sections 1 and 6 of this file re-derived from `git for-each-ref` and `git log`. | **Nothing in the report failed verification.** Every defect found was in *this* file. The header and section 6 were four commits stale on `main` (`049494b` → `344c8b7`). Section 6 stated one branch where there are two, and did not record that S17's deliverables sit on an unmerged branch — **`main` does not carry the harness schematic.** Section 6's sentence about intra-phase iteration tags being "pending removal" from `CLAUDE.md` was stale; they were removed on 2026-08-23. Section 4 was missing S16 entirely and two of S15's four commits. The report's own list of what it could not fix was complete and is now O12–O14. |

| 2026-08-25 | `docs/repo-hygiene` @ `f31e687`, and `main` @ `769c618` | The `docs/reports/J5-S18.md` close-out report against the repository. `f31e687` touches exactly the eight claimed paths and no others; `30fef4d`, the pre-amend commit, still exists as a dangling object, so the amend the report describes happened as described. Bare `python -m pytest -q` from the repository root: **48 passed**, exit 0, no path argument — and the same run with `--override-ini="testpaths="` reproduces both collection errors, so the fix is load-bearing. `scripts/check_harness_nets.py` re-run from `main`: exit 0, all six checks, 64 nets, 38 BOM line items, 145 endpoints, 11 % fuse margin, identical to the report. `grep -c 5219` returns 0 in all three named files. `mechanical/preview/mass_budget.py` run in a scratch copy prints `ASSEMBLED TOTAL 1531 g (95.7% of ceiling)`, matching the new `BOM.md` entry. All eight blobs CR-free by a `git cat-file` CR count read from the object database, and `i/lf w/lf` by `git ls-files --eol`; `git diff --ignore-cr-at-eol` was not used. The SVG parses as well-formed XML. The `TUNING.md` diff is one line and both measured crossovers are untouched. Sections 1 and 6 re-derived from `git for-each-ref` and `git log`. | **Nothing in the report failed verification.** Two corrections to it, neither material to its deliverables. It reads the four post-S17 commits as "S17's work merged as four ordinary commits"; `06783fe` and `769c618` are the orchestrator turn's own, and that turn had no ledger row — both fixed here, and the `-O` convention adopted. Its `5219` grep was scoped to `BOM.md docs simulation`, which missed `johnny5-phase02-locomotion.MD` at the repository root still carrying `#5218 = LEFT / #5219 = RIGHT`; that is now O18. Defects in *this* file: the header and section 6 were stale again in the same two places — `main` at `344c8b7` where it is `769c618`, and a branch table naming `docs/power-harness-schematic`, which was merged and deleted. Section 6 asserted `main` does not carry the harness schematic; it does. |
| 2026-08-25 (evening, local) | `main` @ `7a5f827`, and the uncommitted S19 working tree | The `docs/reports/J5-S19.md` close-out report against the repository. Sections 1 and 6 of this file re-derived from `git for-each-ref` and `git log`: `main` at `7a5f827`, `origin/main` identical, one branch, no `.git` lock files. `bash -n scripts/setup_motion_pi.sh` exit 0. Bare `python -m pytest -q` from the repository root: **48 passed**, exit 0. `scripts/check_harness_nets.py`: exit 0, all six checks, 64 nets, 145 endpoints resolving to 24 line items, `6.65 A of 7.50 A fuse (11 % margin)` — identical to what S17 and S18 reported. The section 3(b) diff re-derived independently from `git show main:scripts/setup_motion_pi.sh` piped through `diff -u`: reproduces the report hunk for hunk with nothing extra. Every package in `requirements-motion.txt` traced to a real import in `src/motion/`, `paho-mqtt` excepted and declared as such. CR count 0 on all four new or changed text files. `johnny5-pi-m-env.md` read in full against `docs/HARDWARE_pi_m_runtime.md`: 17 lines, 8 of them frontmatter, every content fact present at the destination lines the report names, only the dead wikilink dropped. `git grep 5219` excluding `docs/archive/` and `docs/reports/`. `git grep` for references to the six notes from every other tracked file: only this file and `docs/ORCHESTRATION.md`, both narrative, no code. | **Nothing in the report failed verification and no factual error was found in it** — the first close-out in this project of which that is true without qualification. One judgement call overruled in part: `sandbox-no-torch.md`'s mechanism is preserved in `docs/ORCHESTRATION.md` section 7 rather than dropped with the file. Defects in *this* file, in the same two places as the previous two turns: the header and section 6 still had `main` at `769c618` with `docs/repo-hygiene` awaiting a merge that had already happened. Section 4's S18-O row still read `pending` for `7a5f827`. Section 9 records why this recurs and the procedural fix. |

| 2026-08-26 (evening, local) | `main` @ `ebdea9e`, and the still-uncommitted S19 working tree | The `docs/reports/J5-S20.md` close-out report against the repository. Sections 1 and 6 re-derived from `git for-each-ref` and `git log`: `main` at `ebdea9e`, `origin/main` and `origin/HEAD` identical, one branch, three tags unchanged, no `.git` lock files. `ebdea9e` shown by `--stat` to touch exactly `PROJECT_STATE.md`, `docs/ORCHESTRATION.md` and `docs/reports/J5-S19.md` and nothing else. `git ls-tree -r main` confirms `src/motion/requirements-motion.txt` and `docs/HARDWARE_pi_m_runtime.md` absent from `main` and all six root notes still tracked. `git --no-optional-locks status --porcelain` reproduces S20's output line for line. S20's copy of S19's command block diffed against `docs/reports/J5-S19.md` section 6: identical, seven lines. mtimes on all six files in play: S19's three at 2026-08-25 22:42, D7's two targets at 2026-08-25 22:34 and untouched, `docs/reports/J5-S20.md` alone at 2026-08-26 19:31 — so the report's central claim that it edited nothing else holds independently of the report. `grep -n 1807 docs/HARDWARE_drive_bringup.md` and `grep -n 5218 docs/diagrams/bench_full_schematic.svg` confirm O19 and O17 untouched. CR count 0 on the report. No test or guard was run: no code changed, so there was no figure to trace. | **Nothing in the report failed verification.** Its stop, its diagnosis and both of its recommendations about this file are correct, and its verbatim copy of S19's block is accurate. Two things it did not find, both in S19's block rather than in S20: the first commit message claims it closes O15, which this file has held open since 2026-08-25; and the block never merges `fix/pi-m-bringup`, so it cannot satisfy the precondition written against `main`. One thing beyond its scope: `grep -n 1807` returns two lines in `docs/HARDWARE_drive_bringup.md`, not the one O19 names. Defects in *this* file, in the same two places as the previous three turns: the header and section 6 had `main` at `7a5f827`; section 4's S19-O row read `pending` for `ebdea9e`. Section 7 carried O16 and O18 struck through as closed against a commit that does not exist — the first time this staleness reached the open items register rather than only the header. |

| 2026-08-26 (late evening, local) | `main` @ `91aab43`, and the uncommitted S21 working tree | The `docs/reports/J5-S21.md` close-out report against the repository. Sections 1 and 6 re-derived from `git for-each-ref` and `git log`: `main` at `91aab43`, `origin/main` and `origin/HEAD` identical, one branch, three tags unchanged, no `.git` lock files. **Andrew's corrected S19 block confirmed run**: `382ee10` shown by `--stat` to touch exactly `scripts/setup_motion_pi.sh`, `src/motion/requirements-motion.txt` and `docs/HARDWARE_pi_m_runtime.md` (+187/-11), `a1f0111` to remove exactly the five root notes and `MEMORY.md` (-101), both above `ebdea9e` and below `91aab43`. All eight of S21's definition-of-done checks reproduced independently: `grep -n 1807 docs/HARDWARE_drive_bringup.md` returns exactly two lines, each carrying `451.74` and `simulation/chassis/TUNING.md` on the line itself; `grep -c "#5218" docs/diagrams/bench_full_schematic.svg` returns 3 at lines 81, 88 and 150 with all six key rows reading `LEFT`/`RIGHT`; the SVG parses as well-formed XML; `.gitignore` line 27 is `.claude/` and `git --no-optional-locks status --porcelain` no longer lists it; `tr -cd '\r' \| wc -c` returns 0 on all three edited files and `git ls-files --eol` reports `i/lf w/lf` on each; `python -m pytest -q` gives **48 passed** (pytest absent from the session shell and installed first, as S21 also reported); `scripts/check_harness_nets.py` exits 0 with all six checks, 64 nets, 145 endpoints and the 11 % fuse margin. The three diffs read in full: `.gitignore` +3 including a blank separator, the schematic exactly six `<text>` elements with no attribute touched, `HARDWARE_drive_bringup.md` one table row and one re-wrapped paragraph, 104 lines before and after. **O4's probe spent a second time by the orchestrator** rather than taken on trust, returning the identical XML-RPC fault. `git ls-files --eol` run across the whole tree. | **Nothing in the report failed verification and no factual error was found in it** — the second close-out of which that is true, after S19. Two additions rather than corrections. Its open thread about `.gitignore` being CRLF is right and much larger than one file: 75 of 152 tracked files are `i/lf w/crlf`, which makes section 6's line-endings paragraph wrong in a clause it has carried since the migration; now O21. Its note that `ORCHESTRATOR_PROMPT.md` is absent from the working copy is also right, and section 6's untracked table was describing a file that is not there; corrected. One immaterial imprecision: the report says two lines were appended to `.gitignore` where the diff is three, the third being a blank separator. **Defects in *this* file: for the first turn in five, none in the header or section 6's branch table** — Andrew's block landed before the state commit, which is exactly what the S20-O ordering rule was written to produce. |

| 2026-08-26 (night, local) | `main` @ `248a41d` | The `docs/reports/J5-S22.md` close-out report against the repository. Sections 1 and 6 re-derived from `git for-each-ref` and `git log`: `main` at `248a41d`, `origin/main` and `origin/HEAD` identical, one branch, three tags unchanged, no `.git` lock files. **Andrew's S21 block confirmed run** — `10650f2` and `38569a1` are on `main`, filling section 4's two `pending` rows. **Two commits found that no ledger row explained**, `23157ef` and `ecb244f`, both `git show --stat`-verified and both Andrew's own CAD work. S22's deliverable checked as the object database rather than as a file: `git cat-file -e main:docs/HARDWARE_pi_v_runtime.md` present, 197 lines, blob `3c0b29bc…` and worktree md5 `c6dd6021…` both matching the report exactly, CR count 0 on the blob, `git ls-files --eol` `i/lf w/lf`. `git diff --stat ecb244f 248a41d` returns one file and 197 insertions, which is the authoritative form of the report's "no file outside the deliverable is modified". The report's grep of every IP, hostname and path in the deliverable reproduced byte for byte, same sixteen hits at the same sixteen line numbers, `192.168.1.217` absent as claimed, one em-dash and it is the empty-table-cell marker the report says it is. Every cited source opened and confirmed in place: `phases/PHASE_01_INFRASTRUCTURE.md:72`, `scripts/_common.sh:11-14`, `scripts/deploy_vision.sh:17`, `scripts/deploy_motion.sh:16`, `.env.example`, and `BOM.md` section 7 at line 81. Regression: `python -m pytest -q` **48 passed** (pytest absent from the session shell and installed first), `scripts/check_harness_nets.py` exit 0 with all six checks, 64 nets, 145 endpoints and the 11 % fuse margin. **Both mechanical guards re-run because Andrew's two commits changed geometry:** `mass_budget.py` prints `ASSEMBLED TOTAL 1542 g (96.4% of ceiling)` and `validate.py` `ALL CHECKS PASS` across 16 checks. All six of S22's open threads checked against the repository: no `setup_vision_pi.sh` in `git ls-files`; `whats_this_color.py:36` uses `rpicam-still` while `PHASE_04_COGNITION.md:69,181` specify `picamera2` on Bookworm; both deploy scripts' systemd units TBD; `BOM.md:58` and `docs/HARDWARE_power_harness.md:130` carry the Pi-V GPIO13 nav-light PWM with no `config.txt` line anywhere. **Thread 2 escalated rather than confirmed:** `git grep` finds exactly one secret-shaped literal in the tree, `git log -S` dates it to `22ad422` on 2026-06-20, and the GitHub remote was fetched and **loads as a public repository**. | **Nothing in the report failed verification and no factual error was found in it** — the third close-out of which that is true, after S19 and S21. One judgement call put to the orchestrator by the report and **upheld**: proceeding past a precondition whose evidence form had gone stale while its substance held. The finding belongs to the brief rather than the worker and section 9 records the change. **Defects in *this* file: none in the header or section 6's branch table for the second consecutive turn**, which is the S20-O ordering rule holding. What was wrong here instead was everything downstream of two commits nobody logged: section 3 evidenced the Phase 00 gate at a mass the script no longer prints, section 4 had no place to record work Andrew does between turns, and section 6 named `91aab43`. All corrected. **One finding outranks the entire session:** a live LiteLLM virtual key has been readable in a public GitHub repository since 2026-06-20. S22 found it, said plainly that it could not check the remote's visibility, and called it the most consequential thing in its report. It was right on both counts. O22. |

**Attribution note, 2026-08-25.** `d1d4c2b` is dated 2026-08-24 but its content is the
document demotion that section 9 records as S15's work on 2026-08-23. It is logged against S15
on that basis. Commit dates in this repository record when Andrew ran the git write, not when
the work was done, because every git write is his; the gap is expected and is not evidence of
a separate session. This is an inference, not a record.

**Orchestrator errors this session, recorded so they are not repeated.** A commit was certified
with `git diff --ignore-cr-at-eol`, which is precisely the flag that conceals line-ending defects,
and a CRLF blob reached the repository as a result. A repository migration was recommended on a
Nextcloud root cause that was never tested and did not survive contact — the true cause is the
Cowork device mount's inability to delete files. Both are the same failure the orchestrator role
exists to prevent: a confident claim built on a plausible correlation rather than a check.
