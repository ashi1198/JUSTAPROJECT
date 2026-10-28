from collections import Counter


def page_ok(record):
    return record.status == 200 and record.title is not None


def failure_reason(record):
    if record.status == 200:
        return "not HTML"
    if record.status is not None:
        return str(record.status)
    return record.error or "unknown"


def summarize(records, skipped, elapsed):
    pages_ok = 0
    failure_reasons = Counter()
    links_seen = Counter()
    for record in records:
        if page_ok(record):
            pages_ok += 1
            links_seen.update(record.link_counts)
        else:
            failure_reasons[failure_reason(record)] += 1
    return {
        "pages_ok": pages_ok,
        "pages_failed": len(records) - pages_ok,
        "failure_reasons": dict(failure_reasons),
        "skipped_robots": skipped,
        "links_seen": dict(links_seen),
        "elapsed": elapsed,
    }
