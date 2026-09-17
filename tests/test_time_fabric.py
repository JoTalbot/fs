from fs_overlay.time_fabric import LogicalClock, PlatformTimeAdapter


def test_platform_time_adapter_uses_utc_wall_clock():
    adapter = PlatformTimeAdapter()
    wall = adapter.wall_time()
    assert wall.tzinfo is not None
    assert wall.utcoffset().total_seconds() == 0
    assert adapter.wall_time_ns() > 0


def test_monotonic_time_is_non_negative_and_moves_forward():
    adapter = PlatformTimeAdapter()
    first = adapter.monotonic_ns()
    second = adapter.monotonic_ns()
    assert first >= 0
    assert second >= first


def test_logical_clock_never_moves_backwards():
    values = iter((10, 7, 12))
    clock = LogicalClock(_source=lambda: next(values))
    assert clock.now() == 10
    assert clock.now() == 10
    assert clock.now() == 12


def test_logical_clock_can_observe_remote_value():
    clock = LogicalClock(_value=5, _source=lambda: 4)
    assert clock.observe(20) == 20
    assert clock.now() == 20


def test_logical_clock_rejects_invalid_source_value():
    clock = LogicalClock(_source=lambda: True)
    try:
        clock.now()
    except ValueError as exc:
        assert "non-negative integer" in str(exc)
    else:
        raise AssertionError("invalid logical clock source was accepted")


def test_logical_clock_rejects_invalid_observed_value():
    clock = LogicalClock()
    try:
        clock.observe(-1)
    except ValueError as exc:
        assert "non-negative integer" in str(exc)
    else:
        raise AssertionError("invalid logical clock value was accepted")


def test_logical_clock_rejects_boolean_observation():
    clock = LogicalClock()
    try:
        clock.observe(True)
    except ValueError as exc:
        assert "non-negative integer" in str(exc)
    else:
        raise AssertionError("boolean logical clock value was accepted")
