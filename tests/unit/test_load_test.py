from scripts.load_test import summarize


def test_summarize_reports_percentiles_and_error_rate() -> None:
    report = summarize(
        latencies_ms=[10.0, 20.0, 30.0, 40.0, 50.0],
        successes=4,
        failures=1,
        elapsed_seconds=0.5,
        concurrency=5,
    )

    assert report["requests"] == 5
    assert report["rps"] == 10.0
    assert report["p50_ms"] == 30.0
    assert report["p95_ms"] == 50.0
    assert report["p99_ms"] == 50.0
    assert report["error_rate"] == 0.2


def test_summarize_handles_empty_measurement() -> None:
    report = summarize([], 0, 0, 1.0, 1)

    assert report["requests"] == 0
    assert report["rps"] == 0.0
    assert report["p50_ms"] is None
    assert report["error_rate"] == 0.0
