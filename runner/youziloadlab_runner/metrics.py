import math


def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    rank = math.ceil((percent / 100) * len(ordered))
    return ordered[max(rank - 1, 0)]


class ErrorClassifier:
    def classify(self, status_code: int, body: str) -> str:
        lowered = body.lower()
        if status_code == 0 or "timeout" in lowered:
            return "timeout"
        if status_code == 412:
            return "fireworks_412"
        if status_code == 429:
            return "rate_limited"
        if status_code in {401, 402, 403}:
            return "auth_or_quota"
        if 500 <= status_code <= 599:
            return "upstream_5xx"
        return "other_error"
