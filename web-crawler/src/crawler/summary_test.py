from main import PageRecord
from summary import summarize


def make_records():
    counts_a = {"INTERNAL": 3, "EXTERNAL": 1, "MEDIA": 0, "INVALID": 0}
    counts_b = {"INTERNAL": 5, "EXTERNAL": 0, "MEDIA": 2, "INVALID": 0}
    return [
        PageRecord(
            url="a",
            depth=0,
            status=200,
            error=None,
            attempts=1,
            title="A",
            link_counts=counts_a,
        ),
        PageRecord(
            url="b",
            depth=1,
            status=200,
            error=None,
            attempts=2,
            title="B",
            link_counts=counts_b,
        ),
        PageRecord(url="c", depth=1, status=404, error=None, attempts=1),
        PageRecord(url="d", depth=1, status=None, error="TimeoutError", attempts=3),
        PageRecord(url="e", depth=1, status=200, error=None, attempts=1),  # not HTML
    ]


def test_summarize():
    s = summarize(make_records(), skipped=2, elapsed=12.5)
    assert s["pages_ok"] == 2
    assert s["pages_failed"] == 3
    assert s["failure_reasons"] == {"404": 1, "TimeoutError": 1, "not HTML": 1}
    assert s["skipped_robots"] == 2
    assert s["links_seen"] == {"INTERNAL": 8, "EXTERNAL": 1, "MEDIA": 2, "INVALID": 0}
    assert s["elapsed"] == 12.5


def test_summarize_empty():
    s = summarize([], skipped=0, elapsed=0)
    assert s["pages_ok"] == 0
    assert s["pages_failed"] == 0
    assert s["failure_reasons"] == {}
    assert s["links_seen"] == {}


if __name__ == "__main__":
    test_summarize()
    test_summarize_empty()
    print("All summary tests passed")
