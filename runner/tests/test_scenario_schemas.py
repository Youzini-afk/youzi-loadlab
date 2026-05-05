from youziloadlab_runner.scenarios.config_schemas import FIREWORKS_SCHEMA, POLLING_SCHEMA


def test_fireworks_schema_requires_setup_request_load_and_cleanup() -> None:
    assert FIREWORKS_SCHEMA["required"] == ["setup", "request", "loadProfile", "cleanup"]
    assert (
        FIREWORKS_SCHEMA["properties"]["setup"]["properties"]["testUserPrefix"]["default"]
        == "stress_test_fw_"
    )
    assert (
        FIREWORKS_SCHEMA["properties"]["setup"]["properties"]["testUserGroup"]["default"]
        == "fireworks_stress"
    )


def test_polling_schema_requires_polling_and_load_profile() -> None:
    assert POLLING_SCHEMA["required"] == ["polling", "loadProfile"]
    assert "channelListIntervalSeconds" in POLLING_SCHEMA["properties"]["polling"]["properties"]
