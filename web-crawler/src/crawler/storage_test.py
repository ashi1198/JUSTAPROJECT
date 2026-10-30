import os
import tempfile

from main import PageRecord
from storage import records_to_dicts, save_results, load_results


def sample_records():
    return [
        PageRecord(
            url="https://example.com/",
            depth=0,
            status=200,
            error=None,
            attempts=1,
            title="Home - Café 日本語",
            link_counts={"INTERNAL": 3, "EXTERNAL": 1, "MEDIA": 0, "INVALID": 0},
        ),
        PageRecord(
            url="https://example.com/missing",
            depth=1,
            status=404,
            error=None,
            attempts=1,
        ),
        PageRecord(
            url="https://example.com/slow",
            depth=1,
            status=None,
            error="TimeoutError",
            attempts=3,
        ),
    ]


SUMMARY = {
    "pages_ok": 1,
    "pages_failed": 2,
    "failure_reasons": {"404": 1, "TimeoutError": 1},
    "skipped_robots": 0,
    "links_seen": {"INTERNAL": 3, "EXTERNAL": 1},
    "elapsed": 12.5,
}


def test_records_to_dicts():
    dicts = records_to_dicts(sample_records())
    assert len(dicts) == 3
    assert dicts[0]["url"] == "https://example.com/"
    assert dicts[0]["link_counts"]["INTERNAL"] == 3
    assert dicts[2]["status"] is None
    assert dicts[2]["error"] == "TimeoutError"
    assert isinstance(dicts[0], dict)  # plain dicts, not PageRecord objects


def test_save_and_load_round_trip():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "out.json")
        save_results(sample_records(), SUMMARY, path)
        summary, pages = load_results(path)
    assert summary == SUMMARY
    assert pages == records_to_dicts(sample_records())


def test_unicode_is_kept_readable():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "out.json")
        save_results(sample_records(), SUMMARY, path)
        with open(path, encoding="utf-8") as f:
            text = f.read()
    assert "Café 日本語" in text  # not written as \u escapes


def test_empty_results():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "empty.json")
        save_results([], {"pages_ok": 0}, path)
        summary, pages = load_results(path)
    assert summary == {"pages_ok": 0}
    assert pages == []


if __name__ == "__main__":
    test_records_to_dicts()
    test_save_and_load_round_trip()
    test_unicode_is_kept_readable()
    test_empty_results()
    print("All storage tests passed")
