import asyncio
import aiohttp
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit, urlunsplit
from retry import is_retryable, backoff_delay

BLOCK_ALL = "User-agent: *\nDisallow: /"


def robots_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))


def parse_robots(text):
    parser = RobotFileParser()
    parser.parse(text.splitlines())
    return parser


def parser_for_response(status, text):
    if 200 <= status <= 299:
        return parse_robots(text)
    if 300 <= status <= 399:
        return parse_robots("")
    if status == 429:
        return parse_robots(BLOCK_ALL)
    if 400 <= status <= 499:
        return parse_robots("")
    return parse_robots(BLOCK_ALL)


def robots_unavailable_reason(status):
    # None when we got usable rules (or a clean "no file"); otherwise a short reason
    if 200 <= status <= 399:
        return None
    if 400 <= status <= 499 and status != 429:
        return None
    return f"status {status}"


async def get_robots(session, cache, url, max_attempts=3):
    # returns (parser, unavailable_reason); the robots.txt is fetched once per site
    key = robots_url(url)
    if key in cache:
        return cache[key]

    status = None
    error_name = None
    text = ""
    for attempt in range(1, max_attempts + 1):
        status, error_name, text = None, None, ""
        try:
            async with session.get(key) as res:
                status = res.status
                if 200 <= status < 300:
                    text = await res.text(errors="ignore")
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            error_name = type(e).__name__
        if not is_retryable(status, error_name):
            break
        if attempt < max_attempts:
            print(
                f"  robots retry {attempt}/{max_attempts} for {key}: {status or error_name}"
            )
            await asyncio.sleep(backoff_delay(attempt, 2))

    if error_name is not None:
        print(
            f"  robots fetch failed for {key}: {error_name} after {attempt} attempt(s)"
        )
        parser = parse_robots(BLOCK_ALL)
        unavailable = error_name
    else:
        parser = parser_for_response(status, text)
        unavailable = robots_unavailable_reason(status)
    cache[key] = (parser, unavailable)
    return cache[key]


async def is_allowed(session, cache, url, user_agent):
    parser, _ = await get_robots(session, cache, url)
    return parser.can_fetch(user_agent, url)
