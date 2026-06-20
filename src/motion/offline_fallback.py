"""Offline fallback state machine for Pi-M.

Must never raise out of update() -- a broken state machine in the motion loop
is a safety hazard, not just a bug. Errors are logged and the last stable
state holds.

This module has no MQTT or hardware dependencies of its own; it is driven by
inputs the motion loop collects (offline signal, heartbeat age, latest intent)
and produces outputs the motion loop applies (stop treads, hold servos, LED
pattern). Keeping it pure makes it unit-testable without a broker or hardware.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("johnny5.motion.offline_fallback")

HEARTBEAT_TIMEOUT_S = 30.0


class State(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    RECOVERING = "RECOVERING"


@dataclass
class FallbackOutput:
    """What the motion loop should do this tick, per the current state."""

    stop_treads: bool
    hold_servos: bool
    led_pattern: str  # "normal" | "offline_amber_pulse"


_OUTPUTS = {
    State.ONLINE: FallbackOutput(stop_treads=False, hold_servos=False, led_pattern="normal"),
    State.OFFLINE: FallbackOutput(stop_treads=True, hold_servos=True, led_pattern="offline_amber_pulse"),
    State.RECOVERING: FallbackOutput(stop_treads=True, hold_servos=True, led_pattern="offline_amber_pulse"),
}


class OfflineFallbackStateMachine:
    def __init__(self, heartbeat_timeout_s: float = HEARTBEAT_TIMEOUT_S):
        self._state = State.ONLINE
        self._heartbeat_timeout_s = heartbeat_timeout_s
        self._last_vision_heartbeat: float | None = None
        self._offline_signal: bool = False

    @property
    def state(self) -> State:
        return self._state

    def on_vision_heartbeat(self, timestamp: float | None = None) -> None:
        self._last_vision_heartbeat = timestamp if timestamp is not None else time.monotonic()

    def on_offline_signal(self, offline: bool) -> None:
        self._offline_signal = offline

    def update(self, now: float | None = None) -> FallbackOutput:
        """Evaluate transitions for this tick and return the output to apply.
        Never raises -- any internal error is logged and the prior state holds.
        """
        try:
            now = now if now is not None else time.monotonic()
            self._evaluate_transition(now)
        except Exception:
            logger.exception(
                "Offline fallback state machine error; holding state %s", self._state.value
            )
        return _OUTPUTS[self._state]

    def on_intent_received(self) -> None:
        """Call when Pi-M receives a valid intent message from Pi-V.
        Drives RECOVERING -> ONLINE.
        """
        if self._state == State.RECOVERING:
            logger.info("Valid intent received while RECOVERING -- transitioning to ONLINE")
            self._state = State.ONLINE

    def _evaluate_transition(self, now: float) -> None:
        heartbeat_stale = (
            self._last_vision_heartbeat is not None
            and (now - self._last_vision_heartbeat) > self._heartbeat_timeout_s
        )

        if self._state == State.ONLINE:
            if self._offline_signal or heartbeat_stale:
                reason = "offline_signal" if self._offline_signal else "heartbeat_timeout"
                logger.warning("ONLINE -> OFFLINE (%s)", reason)
                self._state = State.OFFLINE

        elif self._state == State.OFFLINE:
            if not self._offline_signal:
                logger.info("OFFLINE -> RECOVERING")
                self._state = State.RECOVERING

        elif self._state == State.RECOVERING:
            # ONLINE transition happens via on_intent_received(), not here.
            # But if the offline signal flips back on while recovering, drop
            # back to OFFLINE rather than waiting on a stale recovery.
            if self._offline_signal:
                logger.warning("RECOVERING -> OFFLINE (offline signal reasserted)")
                self._state = State.OFFLINE
