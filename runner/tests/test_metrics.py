from youziloadlab_runner.metrics import ErrorClassifier, percentile


def test_percentile_uses_nearest_rank() -> None:
    assert percentile([10, 20, 30, 40, 50], 95) == 50
    assert percentile([10, 20, 30, 40, 50], 50) == 30


def test_error_classifier_handles_nashiyard_and_provider_errors() -> None:
    classifier = ErrorClassifier()
    assert classifier.classify(429, "rate limit") == "rate_limited"
    assert classifier.classify(412, "invalid key") == "fireworks_412"
    assert classifier.classify(500, "upstream failed") == "upstream_5xx"
    assert classifier.classify(0, "timeout") == "timeout"
