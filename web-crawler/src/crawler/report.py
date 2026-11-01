"""Build a single-file HTML report from a crawl summary and its page records.

Only the standard library is used. This file must NOT import main.py.

`summary` is the dictionary returned by summarize():
    {"pages_ok", "pages_failed", "failure_reasons": {reason: count},
     "skipped_robots", "links_seen": {TYPE: count}, "elapsed"}

`pages` is a list of dictionaries, one per crawled URL:
    {"url", "depth", "status", "error", "attempts", "title", "link_counts"}
"""

from collections import Counter
from datetime import datetime
from html import escape

STYLE = """
body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 1100px; color: #222; }
h1 { margin-bottom: 0.2rem; }
h2 { margin-top: 2rem; border-bottom: 2px solid #eee; padding-bottom: 0.3rem; }
.muted { color: #777; font-size: 0.9rem; }
.cards { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; }
.card { border: 1px solid #ddd; border-radius: 8px; padding: 0.8rem 1.2rem; min-width: 130px; }
.card .number { font-size: 1.8rem; font-weight: bold; }
.card.bad .number { color: #b00020; }
table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; font-size: 0.9rem; }
th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; word-break: break-all; }
th { background: #f5f5f5; }
tr:nth-child(even) td { background: #fafafa; }
"""


def html_table(headers, rows):
    """Return an HTML <table> string (or a short note when there are no rows)."""
    if not rows:
        return "<p class='muted'>none</p>"
    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = []
        for value in row:
            text = "" if value is None else escape(str(value))
            cells.append(f"<td>{text}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><tr>{head}</tr>{''.join(body_rows)}</table>"


def failure_label(page):
    # what to show for a failed page: the HTTP status, or the network error name
    status, error = page.get("status"), page.get("error")
    if status == 200:
        return "200 (not HTML)"
    if status is not None:
        return status
    return error or "unknown"


def card(label, value, bad=False):
    css = "card bad" if bad else "card"
    return (
        f"<div class='{css}'><div class='number'>{escape(str(value))}</div>"
        f"<div class='muted'>{escape(label)}</div></div>"
    )


def build_report_html(summary, pages, title="Crawl report"):
    """Return a complete HTML document as a string (it starts with <!DOCTYPE html>)."""
    pages_ok = summary.get("pages_ok", 0)
    pages_failed = summary.get("pages_failed", 0)
    skipped = summary.get("skipped_robots", 0)
    elapsed = summary.get("elapsed", 0)

    cards = "".join(
        [
            card("pages fetched", pages_ok),
            card("pages failed", pages_failed, bad=pages_failed > 0),
            card("skipped by robots.txt", skipped),
            card("time taken", f"{elapsed:.1f}s"),
        ]
    )

    # a page counts as a failure when it has no title
    failures = [
        [p["url"], failure_label(p), p.get("attempts")]
        for p in pages
        if p.get("title") is None
    ]
    reasons = list(summary.get("failure_reasons", {}).items())
    all_pages = [
        [
            p["url"],
            p.get("depth"),
            failure_label(p) if p.get("title") is None else p.get("status"),
            p.get("title"),
            (p.get("link_counts") or {}).get("INTERNAL", 0),
        ]
        for p in pages
    ]
    status_counts = Counter(
        str(failure_label(p) if p.get("title") is None else p.get("status"))
        for p in pages
    )
    links_seen = list(summary.get("links_seen", {}).items())
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<h1>{escape(title)}</h1>
<p class="muted">Generated {generated}</p>
<div class="cards">{cards}</div>

<h2>Failed pages</h2>
{html_table(["URL", "Status / error", "Attempts"], failures)}

<h2>Failure reasons</h2>
{html_table(["Reason", "Count"], reasons)}

<h2>Results by status</h2>
{html_table(["Status", "Pages"], sorted(status_counts.items()))}

<h2>All pages</h2>
{html_table(["URL", "Depth", "Status", "Title", "Internal links"], all_pages)}

<h2>Links seen by type</h2>
<p class="muted">A link is counted once for every page it appears on.</p>
{html_table(["Type", "Count"], links_seen)}
</body>
</html>
"""


def save_report(html_text, path):
    """Write the report to `path` using UTF-8."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_text)
