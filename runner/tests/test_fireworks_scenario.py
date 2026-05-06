from youziloadlab_runner.scenarios.nashiyard_fireworks_channel import (
    build_test_usernames,
    default_fireworks_phases,
    fireworks_phases_json,
    load_fireworks_phases_from_env,
)


def test_build_test_usernames_are_zero_padded_and_isolated() -> None:
    assert build_test_usernames("stress_test_fw_", 3) == [
        "stress_test_fw_001",
        "stress_test_fw_002",
        "stress_test_fw_003",
    ]


def test_default_fireworks_phases_match_design_document() -> None:
    phases = default_fireworks_phases()
    assert [phase.name for phase in phases] == [
        "smoke",
        "baseline",
        "ramp",
        "peak",
        "fault_injection",
        "recovery",
    ]
    assert phases[0].duration_seconds == 60
    assert phases[0].users == 5
    assert phases[3].users == 100


def test_fireworks_phases_json_round_trips() -> None:
    phases = default_fireworks_phases()
    loaded = load_fireworks_phases_from_env(fireworks_phases_json(phases))

    assert loaded == phases
