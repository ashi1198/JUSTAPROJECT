# Polite Web Crawler

An asynchronous web crawler written in Python from scratch. It starts from a seed URL, discovers pages by following links, and collects a structured record for every page it visits. It follows each site's `robots.txt`, limits its own request rate per site, retries temporary failures, and produces a JSON dataset and an HTML report of what it found.

**Category:** Data Engineering and Analytics (web data collection, structuring, storage, and reporting).

![Example report](docs/report.png)

## Quick start

```
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/crawler/main.py --max-pages 10 --output results.json --report report.html
```

Then open `report.html` in a browser. A sample run is saved in `examples/`.

## The problem

The web holds a lot of useful information, but it is scattered across millions of pages, changes constantly, and breaks quietly: links die, pages fail, and sites go down without anyone noticing. Collecting that data reliably is hard, and careless scrapers make things worse. They ignore site rules, overload small servers, and crash on the first error.

This project collects web data responsibly. Because every page, including every failure, gets a structured record, the output doubles as a site-health dataset: which pages are broken, why, and how deep they sit. Small organisations, such as schools, nonprofits, and local groups, can use it to find broken pages without paying for a commercial audit tool.

## Features

- Breadth-first crawling from any seed URL, using a queue and a `seen` set so no URL is queued twice
- URL normalization (relative links resolved against the page they were found on, `#fragments` removed) and link classification: internal, external, media, invalid
- Limits on the number of pages and on crawl depth
- `robots.txt` support: fetched once per site (with retries), cached, and checked before every request
- Fail-safe policy: if a site's rules cannot be fetched, the site is not crawled, and this is reported separately from "blocked by a rule"
- Per-site rate limiting (1 second by default, honoring a larger `Crawl-delay`)
- Request timeout, content-type check (only HTML is parsed), and retries with exponential backoff for temporary failures (timeouts, connection errors, 5xx, 429)
- A `PageRecord` for every URL, successes and failures alike, and an end-of-crawl summary
- JSON export of the summary and all page records
- A self-contained HTML report (summary, failed pages, results by status, all pages, links seen)
- Command-line options for seed, limits, delay, allowed domains, and output files, validated before the crawl starts
- Unit tests for the URL, robots, rate-limit, retry, summary, command-line, storage, and report logic

## Architecture

The crawler is a pipeline around one work queue. The seed enters the queue as a `(url, depth)` pair. For every URL taken from the queue:

1. **robots.txt**: the site's rules are fetched once and cached. A disallowed URL, or a site whose rules cannot be fetched, is skipped and counted with its reason.
2. **Rate limit**: wait until the site's minimum gap since the last request has passed.
3. **Fetch**: a request with a timeout and a content-type check. Temporary failures are retried up to 3 times with backoff.
4. **Parse**: for HTML pages, extract the title and every `<a href>` link.
5. **Normalize, classify, deduplicate**: internal links that are not already in `seen` are queued with depth + 1, unless the depth limit is reached.
6. **Record**: a `PageRecord` is stored for the URL, whether it succeeded or failed.

The loop ends when the queue is empty or the page limit is reached. The crawler then builds a summary from the records, and optionally writes a JSON file and an HTML report.

Layers: command line, then the crawl engine (queue, limits, deduplication), then the politeness layer (robots.txt, rate limiting, retries), then fetching and parsing, then records, summary, storage, and report.

## Tech stack

- Python 3.10 or newer (developed on 3.11), `asyncio`
- `aiohttp` for HTTP requests
- `beautifulsoup4` for HTML parsing
- Standard library: `urllib` (URL handling and robots rules), `dataclasses`, `argparse`, `json`, `html`, `collections`

## Usage

```
python src/crawler/main.py                                  # crawls https://books.toscrape.com/
python src/crawler/main.py https://quotes.toscrape.com/     # another seed
python src/crawler/main.py --max-pages 20 --max-depth 2 --delay 1.5
python src/crawler/main.py --output results.json --report report.html
```

(On Windows, `src\crawler\main.py` works too.)

| Option           | Default                       | Meaning                                                                                        |
| ---------------- | ----------------------------- | ---------------------------------------------------------------------------------------------- |
| `seed`           | `https://books.toscrape.com/` | URL to start from (must start with `http://` or `https://`)                                    |
| `--max-pages`    | 10                            | Stop after this many pages                                                                     |
| `--max-depth`    | 1                             | How many links away from the seed to follow (the seed is depth 0)                              |
| `--delay`        | 1.0                           | Minimum seconds between requests to one site. A site's own `Crawl-delay` wins if it is larger. |
| `--allow-domain` | none                          | Extra domain to treat as internal. Can be repeated. The seed's host is always internal.        |
| `--output`       | none                          | Write the summary and all page records to this JSON file. Its folder must already exist.       |
| `--report`       | none                          | Write an HTML report to this file. Its folder must already exist.                              |

Run `python src/crawler/main.py --help` for the full list.

### Example output

```
[1] (depth 0) https://books.toscrape.com/
Title: All products | Books to Scrape - Sandbox
INTERNAL 73
EXTERNAL 0
MEDIA 0
INVALID 0
[2] (depth 1) https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
Title: A Light in the Attic | Books to Scrape - Sandbox
INTERNAL 3
...
```

A page that keeps failing is retried, then reported with its reason:

```
  retry 1/3 for https://httpbin.org/status/503: 503
  retry 2/3 for https://httpbin.org/status/503: 503
[1] (depth 0) https://httpbin.org/status/503 failed after 3 attempt(s): 503

--- crawl summary ---
pages ok:        0
pages failed:    1
  503: 1
skipped (robots): 0
links seen:      {}
time:            9.5s
```

A site whose rules cannot be fetched is skipped and reported as such, not as a rule-based block:

```
skipped (robots.txt unavailable: ClientConnectorDNSError): https://httpbin.ord/status/503
```

### JSON output

`--output results.json` writes one file:

```
{
  "summary": { "pages_ok": ..., "pages_failed": ..., "failure_reasons": {...},
               "skipped_robots": ..., "links_seen": {...}, "elapsed": ... },
  "pages": [
    { "url": "...", "depth": 0, "status": 200, "error": null,
      "attempts": 1, "title": "...", "link_counts": { "INTERNAL": 73, ... } },
    ...
  ]
}
```

### HTML report

`--report report.html` writes a single self-contained page (no external files) with key numbers, a table of failed pages (the "broken links" view), failure reasons, results by status, every page with its depth and status, and links seen by type. Every value that came from the web is escaped before it is written into the page.

## Project layout

```
src/crawler/
  main.py          crawl loop, command line, URL normalize/classify, fetch, link extraction, PageRecord
  robots.py        robots.txt fetching (with retries), caching, and rule checks
  rate_limit.py    per-site waiting
  retry.py         which failures are retried, and the backoff delay
  summary.py       end-of-crawl summary
  storage.py       JSON export of the results
  report.py        HTML report
  *_test.py        unit tests for each module
examples/          a sample results file and report
docs/              screenshots
requirements.txt
README.md
```

`retry.py` is separate so that `robots.py` and `main.py` can both use it without importing each other. `storage.py` and `report.py` do not import `main.py` for the same reason.

## Design decisions

- **Normalization, classification, and deduplication are separate functions.** Each does one job and can be tested with plain strings.
- **`hostname`, not `netloc`, when comparing domains.** `netloc` includes the port, user info, and original capitalization, so one site could look like several.
- **The file extension is only a guess.** `classify_url` guesses media from the path. The real answer is the response's `Content-Type`, which is checked before the body is read.
- **robots.txt statuses follow the standard's convention.** 2xx: follow the file. 3xx and other 4xx: no rules, allow everything. 429, 5xx, and network errors: the rules are unknown, so the site is not crawled.
- **"Rule" and "unavailable" are different outcomes.** A blocked URL and an unreachable site call for different actions, so they are counted and printed separately.
- **The rate limiter reserves a slot before sleeping.** The next allowed time is recorded first and the sleep happens after, so concurrent workers could not claim the same moment. This keeps the design ready for concurrency.
- **`time.monotonic()`, not `time.time()`.** The monotonic clock never jumps backwards when the system clock is adjusted.
- **A site's `Crawl-delay` is honored, and our own default is a floor.** `Crawl-delay: 0` still gives 1 second.
- **Retries do not count as pages.** `max_pages` counts URLs. The attempt cap prevents endless retrying.
- **Pure functions where possible** (`wait_time`, `choose_gap`, `is_retryable`, `backoff_delay`, `summarize`), which keeps the tests simple and fast.
- **Output is built from records.** The summary, the JSON file, and the report all come from the same list of `PageRecord`s, so they cannot disagree.
- **Arguments are validated first.** A missing output folder is reported before the crawl starts, so a typo cannot throw the results away.

## Tests

Each test file runs on its own from the project root:

```
python src/crawler/test.py
python src/crawler/robots_test.py
python src/crawler/rate_limit_test.py
python src/crawler/retry_test.py
python src/crawler/summary_test.py
python src/crawler/cli_test.py
python src/crawler/storage_test.py
python src/crawler/report_test.py
```

Each prints an "All ... tests passed" line. (`cli_test.py` also prints argparse's error messages while it checks that bad inputs are rejected. That is expected.)

## Known limitations

- The `robots.txt` request is retried but is not rate-limited, and a site whose rules stay unreachable after the retries is skipped for the rest of the crawl.
- Python's `robots.txt` parser does not understand wildcard rules (`*`, `$` inside a path).
- A `200` response that is not HTML is reported as a failure.
- Only the exact hostname counts as internal, so `www.example.com` and `example.com` are different sites unless one is added with `--allow-domain`.
- Different URLs for the same page (`/` and `/index.html`) are treated as different pages.
- Pages that build their content with JavaScript are not rendered, so their content is not seen.
- Requests are sequential, so `async` gives no speedup yet.
- External links are classified and counted, but not followed or stored.
- "Links seen" counts a link once for every page it appears on, not once overall.

## Roadmap

- Concurrent workers with `asyncio.Queue` (`--workers`)
- SQLite storage for the page records
- A shared work queue and `seen` set in Redis, so several crawler processes can cooperate
- A policy for external links (record them, or follow them up to a limit)
- Optional browser rendering (Playwright) for JavaScript-heavy pages
- Comparing two crawls to show what broke since the last one
- Continuous testing with GitHub Actions

## Responsible use

Only crawl sites you have permission to crawl. The crawler identifies itself with its own `User-Agent`, follows `robots.txt`, and limits its request rate. Check a site's terms of use before crawling it. Practice sites such as `books.toscrape.com` and `quotes.toscrape.com` exist for this purpose.
