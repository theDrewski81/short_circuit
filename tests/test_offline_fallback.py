import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from motion.offline_fallback import OfflineFallbackStateMachine, State  # noqa: E402


def test_starts_online():
    sm = OfflineFallbackStateMachine()
    assert sm.state == State.ONLINE
    out = sm.update(now=0.0)
    assert not out.stop_treads
    assert not out.hold_servos
    assert out.led_pattern == "normal"


def test_online_to_offline_on_offline_signal():
    sm = OfflineFallbackStateMachine()
    sm.on_offline_signal(True)
    out = sm.update(now=0.0)
    assert sm.state == State.OFFLINE
    assert out.stop_treads
    assert out.hold_servos
    assert out.led_pattern == "offline_amber_pulse"


def test_online_to_offline_on_heartbeat_timeout():
    sm = OfflineFallbackStateMachine(heartbeat_timeout_s=30.0)
    sm.on_vision_heartbeat(timestamp=0.0)
    sm.update(now=10.0)
    assert sm.state == State.ONLINE  # not stale yet

    sm.update(now=31.0)
    assert sm.state == State.OFFLINE


def test_offline_to_recovering_when_signal_clears():
    sm = OfflineFallbackStateMachine()
    sm.on_offline_signal(True)
    sm.update(now=0.0)
    assert sm.state == State.OFFLINE

    sm.on_offline_signal(False)
    sm.update(now=1.0)
    assert sm.state == State.RECOVERING


def test_recovering_to_online_on_valid_intent():
    sm = OfflineFallbackStateMachine()
    sm.on_offline_signal(True)
    sm.update(now=0.0)
    sm.on_offline_signal(False)
    sm.update(now=1.0)
    assert sm.state == State.RECOVERING

    sm.on_intent_received()
    assert sm.state == State.ONLINE

    out = sm.update(now=2.0)
    assert not out.stop_treads
    assert not out.hold_servos
    assert out.led_pattern == "normal"


def test_recovering_drops_back_to_offline_if_signal_reasserted():
    sm = OfflineFallbackStateMachine()
    sm.on_offline_signal(True)
    sm.update(now=0.0)
    sm.on_offline_signal(False)
    sm.update(now=1.0)
    assert sm.state == State.RECOVERING

    sm.on_offline_signal(True)
    sm.update(now=2.0)
    assert sm.state == State.OFFLINE


def test_recovering_does_not_auto_advance_without_intent():
    sm = OfflineFallbackStateMachine()
    sm.on_offline_signal(True)
    sm.update(now=0.0)
    sm.on_offline_signal(False)
    sm.update(now=1.0)
    assert sm.state == State.RECOVERING

    # many ticks pass, no intent received -- should stay RECOVERING
    for t in range(2, 50):
        sm.update(now=float(t))
    assert sm.state == State.RECOVERING


def test_update_never_raises_on_internal_error(monkeypatch):
    sm = OfflineFallbackStateMachine()

    def boom(now):
        raise ValueError("simulated failure")

    monkeypatch.setattr(sm, "_evaluate_transition", boom)
    out = sm.update(now=0.0)
    # holds prior state (ONLINE) and returns a valid output rather than raising
    assert sm.state == State.ONLINE
    assert out.led_pattern == "normal"
