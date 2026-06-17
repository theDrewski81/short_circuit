# Phase 05 — Integration & Hardening

## Objective

Validate the full stack under realistic operating conditions, resolve integration issues surfaced by end-to-end testing, harden the system against known failure modes, profile and tune performance, and produce a documented, tagged v1.0 release. This phase does not add new capabilities -- it makes the existing capabilities reliable.

---

## Gate Condition

**The robot operates continuously for 30 minutes under mixed interaction (voice prompts, autonomous navigation, expressive behaviors) without a crash, unexpected stop, or unhandled exception. Offline resilience test passes (see Task 3). All known integration defects from the Phase 04 integration test are resolved. `v5.0` is tagged on `main`.**

---

## Context

All Phase 00–04 gates are met. The full stack is functional but has only been tested in controlled, short-duration scenarios. This phase subjects the system to duration testing, stress testing, and adversarial conditions that short tests miss.

The primary risks entering this phase are: memory leaks on Pi-V from the agent loop, thermal throttling on either Pi under sustained load, MQTT message ordering issues under high trigger rates, and power rail instability under simultaneous motor + servo load.

---

## Tasks

### 1. Integration Defect Resolution

Pull the defect list from the Phase 04 integration test log. Address each item before proceeding to duration testing. Common categories:

- **Response format parsing failures:** The LLM does not always follow the `SPEAK/ACTION/EXPRESSION` format. Improve the system prompt and add a robust parser with fallback behavior (if parsing fails: speak an apology, publish a neutral idle intent, do not crash).
- **Motor/servo conflicts:** Concurrent locomotion and arm behavior commands that cause physical interference. Add safety checks in the motion loop.
- **Audio pipeline issues:** Buffer underruns, playback cutoffs, microphone feedback when speaker is active. Add appropriate audio routing and buffering.
- **Camera capture failures:** `picamera2` occasionally fails to capture under memory pressure. Add retry logic with a 3-attempt limit before logging and skipping the frame.

### 2. Duration and Stress Testing

**30-minute continuous operation test:**
Run the robot in a cleared space. Send voice prompts every 2–3 minutes. Let the robot navigate autonomously between prompts. Monitor:
- CPU temperature on both Pis (`vcgencmd measure_temp` via SSH, log to file)
- Memory usage on Pi-V (agent loop is the primary suspect for leaks)
- Motion loop tick rate jitter on Pi-M (log tick timestamps, compute variance)
- MQTT message latency (time between Pi-V publishing intent and Pi-M consuming it)
- Battery voltage over time (confirm power architecture sustains 30 minutes)

Log all metrics to a time-series file during the test. Review after.

**High-trigger rate test:**
Send voice prompts back-to-back with no pause. Verify the agent loop queues and processes them in order without dropping prompts or crashing. Implement a simple debounce: if a new trigger arrives while the LLM call is in flight, queue it and process it after the current call completes. Do not send concurrent LLM calls.

**Tread stress test:**
Command maximum-speed forward motion for 60 seconds, then immediate reverse. Repeat 5 times. Monitor motor temperature (if thermistors are present) and H-bridge temperature. Verify power rail stability with a multimeter on the 5V rail during the test.

### 3. Offline Resilience Validation

Formal test procedure:

1. Start the robot in ONLINE state with a voice interaction in progress.
2. Mid-interaction: pull the home lab WiFi (or firewall the Pi subnet) to simulate outage.
3. Verify: Pi-V detects the outage within 5 seconds (via LiteLLM timeout). Pi-M receives the offline signal. Treads stop. Servos hold position. LED ring enters OFFLINE state. `espeak-ng` (or equivalent offline TTS) acknowledges the offline condition verbally.
4. Hold offline for 3 minutes.
5. Restore connectivity.
6. Verify: Pi-V detects reconnect. Publishes ONLINE signal to Pi-M. Pi-M exits fallback state. LED ring returns to IDLE. Robot resumes normal operation on next voice prompt.

Document pass/fail against each step. If any step fails, trace the fault and fix before tagging.

**Partial connectivity test:**
Simulate a degraded connection (high latency, packet loss) rather than full outage. Confirm the LLM client timeout fires correctly and does not hang the agent loop indefinitely. A 30-second stuck LLM call should be treated as an outage, not waited on.

### 4. Performance Profiling

**Motion loop timing (Pi-M):**  
Instrument the motion loop to log tick start, each subsystem execution time, and total tick duration. Run with all subsystems active (tread policy, servo telemetry, LED, MQTT publish) and report the P50, P95, and P99 tick durations. Target: P99 under 18ms to stay within the 20ms budget at 50Hz. If the loop is overrunning, identify the slowest subsystem and optimize or reduce its frequency.

**LLM round-trip latency (home lab):**  
Log every LLM call from query send to response receive. Report P50, P95, P99. If P95 exceeds 3 seconds, investigate: is the inference queue backed up? Is the model too large for the use case? Consider using a smaller or faster model for real-time interaction and reserving larger models for more deliberate reasoning.

**Memory profile (Pi-V):**  
Run the duration test with `tracemalloc` active in the agent loop. Dump a snapshot at 5-minute intervals. Compare snapshots to identify growing allocations. The conversation history buffer is the most likely leak source -- confirm it is enforcing its bounded length.

**Policy inference latency (Pi-M):**  
Log ONNX inference call duration in the locomotion policy runner. Confirm P99 is under 5ms. If not, profile the ONNX runtime execution and consider quantizing the model (INT8) to reduce compute.

### 5. Behavioral Tuning

With the system stable from Tasks 1–4, evaluate the robot's behavior as a user experience rather than a technical system.

Questions to address:
- Does the Johnny 5 personality read consistently across different types of interactions?
- Are the arm behaviors expressive enough? Does WAVE look like a wave, or like a servo twitch?
- Does the head rotation feel attentive, or mechanical?
- Is the speech cadence appropriate? Too fast? Too robotic (or not robotic enough)?
- Do the LED states add expressiveness, or are they distracting?

Tune the system prompt (`src/vision/prompts/system.txt`), behavior keyframe sequences (`src/motion/behaviors/`), LED animation parameters (`led_states.yaml`), and TTS configuration. These are text/config file changes -- they do not require retraining or redeployment of the code.

Document behavioral tuning changes in `TUNING_LOG.md` at the project root with date and description of each change and the observed effect.

### 6. Documentation Finalization

Before tagging v5.0:

- `README.md`: complete project description, architecture overview, setup instructions, and demo video placeholder.
- `BOM.md`: confirm reflects final purchased components, not Phase 00 selections. Update any substitutions made during build.
- `CLAUDE.md`: update any architectural decisions that changed during implementation.
- Phase coordinator documents: mark gate status on each.
- `simulation/chassis/TUNING.md` and `simulation/full_body/TUNING.md`: document any reality-gap corrections applied.
- `scripts/`: all deployment scripts confirmed working and documented.
- `policies/README.md`: document each policy file, training configuration, and performance metrics.

### 7. v5.0 Release Tag

With all gate conditions met and documentation finalized:

```bash
git checkout main
git pull
git tag -a v5.0 -m "Phase 05 gate: full stack integration, hardening complete"
git push origin v5.0
```

---

## Post-Phase 05 Roadmap (Out of Scope for Current Project)

The following are natural next phases not in the current scope:

- **Elbow servos (Phase 03 expansion):** Add servo IDs 4 and 5, extend arm MJCF model, train elbow behaviors.
- **Stereo vision (Phase 04 expansion):** Arducam CSI multiplexer on Pi-V, stereo depth perception for obstacle avoidance.
- **Trained arm policies (Phase 03 upgrade):** Replace keyframe behaviors with MuJoCo-trained policies for more natural arm motion.
- **Persistent memory:** Give the robot memory of previous interactions via a vector store on the home lab.
- **Autonomous navigation:** Replace direct intent-to-motion with a navigation stack (obstacle map, goal-directed movement).

---

## Recommended Session Start

Begin by running the Phase 04 integration test one more time from scratch and compiling a clean defect list. Address defects in Task 1 before any duration testing. Duration testing with unresolved defects wastes time.
