import os
import tempfile

from report import html_table, build_report_html, save_report

SUMMARY = {
    "pages_ok": 1,
    "pages_failed": 2,
    "failure_reasons": {"404": 1, "TimeoutError": 1},
    "skipped_robots": 3,
    "links_seen": {"INTERNAL": 5, "EXTERNAL": 1},
    "elapsed": 12.5,
}

PAGES = [
    {
        "url": "https://a.com/",
        "depth": 0,
        "status": 200,
        "error": None,
        "attempts": 1,
        "title": "Home <script>alert(1)</script>",
        "link_counts": {"INTERNAL": 5, "EXTERNAL": 1},
    },
    {
        "url": "https://a.com/missing",
        "depth": 1,
        "status": 404,
        "error": None,
        "attempts": 1,
        "title": None,
        "link_counts": {},
    },
    {
        "url": "https://a.com/slow",
        "depth": 1,
        "status": None,
        "error": "TimeoutError",
        "attempts": 3,
        "title": None,
        "link_counts": {},
    },
]


def test_html_table():
    table = html_table(["URL", "Status"], [["https://a.com/", 200], ["x", None]])
    assert "<table" in table and "</table>" in table
    assert "URL" in table and "https://a.com/" in table and "200" in table
    assert "None" not in table  # None is shown as an empty cell


def test_html_table_escapes_values():
    table = html_table(["Title"], [["<b>bold</b>"]])
    assert "<b>bold</b>" not in table
    assert "&lt;b&gt;" in table


def test_html_table_without_rows():
    table = html_table(["URL"], [])
    assert "<table" not in table  # a short "none" note instead


def test_report_is_a_complete_html_document():
    html = build_report_html(SUMMARY, PAGES)
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "</html>" in html


def test_report_shows_numbers_and_failures():
    html = build_report_html(SUMMARY, PAGES)
    assert "https://a.com/missing" in html  # the broken page is listed
    assert "https://a.com/slow" in html
    assert "404" in html
    assert "TimeoutError" in html
    assert "12.5" in html or "12.5s" in html  # elapsed time


def test_report_escapes_titles_from_the_web():
    html = build_report_html(SUMMARY, PAGES)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_report_with_no_pages_does_not_crash():
    empty = {
        "pages_ok": 0,
        "pages_failed": 0,
        "failure_reasons": {},
        "skipped_robots": 0,
        "links_seen": {},
        "elapsed": 0,
    }
    html = build_report_html(empty, [])
    assert "</html>" in html


def test_save_report():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "report.html")
        save_report("<html>Café</html>", path)
        with open(path, encoding="utf-8") as f:
            assert f.read() == "<html>Café</html>"


if __name__ == "__main__":
    test_html_table()
    test_html_table_escapes_values()
    test_html_table_without_rows()
    test_report_is_a_complete_html_document()
    test_report_shows_numbers_and_failures()
    test_report_escapes_titles_from_the_web()
    test_report_with_no_pages_does_not_crash()
    test_save_report()
    print("All report tests passed")
