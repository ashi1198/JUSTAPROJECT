import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag, urlsplit, urlunsplit
from enum import Enum
from pathlib import PurePosixPath
from collections import deque
from robots import is_allowed, robots_url
from rate_limit import choose_gap, wait_for_turn
import sys

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
    absolute_url = urljoin(baseurl, link)
    #    absolute_url,fragment=urldefrag(absolute_url)
    #    since fragment stays unused we will use this dirctly
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
        return (None, None, type(e).__name__)


def extract_links(html, base_url, domains):
    soup = BeautifulSoup(html, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    results = {link_type: set() for link_type in LinkType}
    for link in links:
        normalized_url = normalize_url(link, base_url)
        results[classify_url(normalized_url, domains)].add(normalized_url)
    title = " ".join(soup.title.get_text().split()) if soup.title else "No title"
    return title, results


async def crawl(seed, domains, max_pages, max_depth):
    last_requests = dict()
    robots_cache = dict()
    queue = deque()
    seen = set()
    pages_crawled = 0
    queue.append((seed, 0))
    seen.add(seed)
    timeout = aiohttp.ClientTimeout(total=10)
    headers = {"User-Agent": "MyCrawler/1.0 (ashi project)"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        while queue and pages_crawled < max_pages:
            url, depth = queue.popleft()
            if not await is_allowed(session, robots_cache, url, headers["User-Agent"]):
                print(f"skipped (robots.txt): {url}")
                continue
            key = robots_url(url)
            parser = robots_cache[key]
            site_gap = choose_gap(
                parser.crawl_delay(headers["User-Agent"]), DEFAULT_GAP
            )
            gap = site_gap
            for attempt in range(1, max_attempts + 1):
                await wait_for_turn(last_requests, key, gap)
                html, status, error_name = await fetch_html(session, url)
                if not is_retryable(status, error_name):
                    break
                if attempt < max_attempts:
                    print(
                        f"  retry {attempt}/{max_attempts} for {url}: {status or error_name}"
                    )
                    gap = max(site_gap, backoff_delay(attempt, 2))
            pages_crawled += 1
            if html is None:
                print(
                    f"[{pages_crawled}] (depth {depth}) {url} failed after attempt:{attempt+1}"
                )
                continue
            print(f"[{pages_crawled}] (depth {depth}) {url}")
            title, links = extract_links(html, url, domains)
            # links is a dictionary of enum linktype as key and urls in it as values
            print("Title:", title)
            for link_type, urls in links.items():
                print(link_type.name, len(urls))
            if depth < max_depth:
                for internal in sorted(links[LinkType.INTERNAL]):
                    if internal not in seen:
                        seen.add(internal)
                        queue.append((internal, depth + 1))


if __name__ == "__main__":
    asyncio.run(crawl(URL, domains, max_pages, max_depth))
    # using if case when test is imported bottom line code will automatically be executed so to prevent it we used this
