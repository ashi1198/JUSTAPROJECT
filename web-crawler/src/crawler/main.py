import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlsplit
from enum import Enum
from pathlib import PurePosixPath
from collections import deque, Counter
from robots import get_robots, robots_url
from rate_limit import choose_gap, wait_for_turn
import sys
import time
from dataclasses import dataclass, field
from summary import summarize


@dataclass
class PageRecord:
    url: str
    depth: int
    status: int | None
    error: str | None
    attempts: int
    title: str | None = None
    link_counts: dict = field(default_factory=dict)


DEFAULT_GAP = 1


class LinkType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    MEDIA = "media"
    INVALID = "invalid"


MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf"}
URL = sys.argv[1] if len(sys.argv) > 1 else "https://books.toscrape.com/"
domains = {urlsplit(URL).hostname}
max_pages = 10
max_depth = 1
max_attempts = 3


def classify_url(link, domains):
    splitted_url = urlsplit(link)
    if splitted_url.scheme not in {"http", "https"} or not splitted_url.hostname:
        return LinkType.INVALID
    extension = PurePosixPath(splitted_url.path).suffix.lower()
    if extension in MEDIA_EXTENSIONS:
        return LinkType.MEDIA
    if splitted_url.hostname in domains:
        return LinkType.INTERNAL
    return LinkType.EXTERNAL


def normalize_url(link, baseurl):
    # resolve a relative link against the page it was found on, then drop the #fragment
    absolute_url = urljoin(baseurl, link)
    return urldefrag(absolute_url).url


def is_retryable(status, error_name):
    if error_name is not None:  # network-level failure: there is no status
        return True
    if status == 429:
        return True
    return status is not None and 500 <= status <= 599


def backoff_delay(attempt, base):
    return base * 2 ** (attempt - 1)


async def fetch_html(session, url):
    try:
        async with session.get(url) as res:
            if res.status != 200:
                return None, res.status, None
            content_type = res.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None, 200, None
            html = await res.text(errors="ignore")
            return html, 200, None
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError) as e:
        return None, None, type(e).__name__


def extract_links(html, base_url, domains):
    soup = BeautifulSoup(html, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    links_by_type = {link_type: set() for link_type in LinkType}
    for link in links:
        normalized_url = normalize_url(link, base_url)
        links_by_type[classify_url(normalized_url, domains)].add(normalized_url)
    title = " ".join(soup.title.get_text().split()) if soup.title else "No title"
    return title, links_by_type


async def crawl(seed, domains, max_pages, max_depth):
    last_requests = dict()
    robots_cache = dict()
    queue = deque()
    seen = set()
    records = []
    skipped = Counter()
    pages_crawled = 0
    queue.append((seed, 0))
    seen.add(seed)
    timeout = aiohttp.ClientTimeout(total=10)
    headers = {"User-Agent": "MyCrawler/1.0 (ashi project)"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        while queue and pages_crawled < max_pages:
            url, depth = queue.popleft()
            key = robots_url(url)

            # robots.txt: one parser per site (cached), plus why it may be unavailable
            parser, unavailable = await get_robots(session, robots_cache, url)
            if not parser.can_fetch(headers["User-Agent"], url):
                if unavailable:
                    skipped["robots.txt unavailable"] += 1
                    print(f"skipped (robots.txt unavailable: {unavailable}): {url}")
                else:
                    skipped["robots.txt rule"] += 1
                    print(f"skipped (robots.txt rule): {url}")
                continue

            # the site's Crawl-delay, with our own default as the minimum
            site_gap = choose_gap(
                parser.crawl_delay(headers["User-Agent"]), DEFAULT_GAP
            )
            gap = site_gap

            # up to max_attempts tries; every try waits for this site's turn
            for attempt in range(1, max_attempts + 1):
                await wait_for_turn(last_requests, key, gap)
                html, status, error_name = await fetch_html(session, url)
                if not is_retryable(status, error_name):
                    break
                if attempt < max_attempts:
                    print(
                        f"  retry {attempt}/{max_attempts} for {url}: "
                        f"{status or error_name}"
                    )
                    gap = max(site_gap, backoff_delay(attempt, 2))

            # retries don't count as pages: one URL is one page
            pages_crawled += 1

            if html is None:
                print(
                    f"[{pages_crawled}] (depth {depth}) {url} "
                    f"failed after {attempt} attempt(s): {status or error_name}"
                )
                records.append(
                    PageRecord(
                        url=url,
                        depth=depth,
                        status=status,
                        error=error_name,
                        attempts=attempt,
                    )
                )
                continue

            print(f"[{pages_crawled}] (depth {depth}) {url}")
            title, links_by_type = extract_links(html, url, domains)
            print("Title:", title)
            for link_type, urls in links_by_type.items():
                print(link_type.name, len(urls))

            if depth < max_depth:
                for internal in sorted(links_by_type[LinkType.INTERNAL]):
                    if internal not in seen:
                        seen.add(internal)
                        queue.append((internal, depth + 1))

            records.append(
                PageRecord(
                    url=url,
                    depth=depth,
                    status=status,
                    error=None,
                    attempts=attempt,
                    title=title,
                    link_counts={
                        link_type.name: len(urls)
                        for link_type, urls in links_by_type.items()
                    },
                )
            )
    return records, skipped


if __name__ == "__main__":
    # the guard stops the crawl from starting when another file imports this one
    start = time.monotonic()
    records, skipped = asyncio.run(crawl(URL, domains, max_pages, max_depth))
    elapsed = time.monotonic() - start
    summary = summarize(records, sum(skipped.values()), elapsed)

    print("\n--- crawl summary ---")
    print(f"pages ok:        {summary['pages_ok']}")
    print(f"pages failed:    {summary['pages_failed']}")
    for reason, count in summary["failure_reasons"].items():
        print(f"  {reason}: {count}")
    print(f"skipped (robots): {summary['skipped_robots']}")
    for kind, count in skipped.items():
        print(f"  skipped, {kind}: {count}")
    print(f"links seen:      {summary['links_seen']}")
    print(f"time:            {summary['elapsed']:.1f}s")
    if not records:
        print("nothing was crawled: check the seed URL or robots.txt")
