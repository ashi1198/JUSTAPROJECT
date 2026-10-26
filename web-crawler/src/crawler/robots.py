from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit, urlunsplit
import asyncio, aiohttp

BLOCK_ALL = "User-agent: *\nDisallow: /"


def robots_url(url):
    urlobj = urlsplit(url)
    return urlunsplit((urlobj.scheme, urlobj.netloc, "/robots.txt", "", ""))


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


async def get_robots(session, cache, url):
    key = robots_url(url)
    if key in cache:
        return cache[key]
    try:
        async with session.get(key) as res:
            status = res.status
            text = await res.text()
        parser = parser_for_response(status, text)
        cache[key] = parser
        return parser
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"  robots fetch failed for {key}: {type(e).__name__}: {e}")
        parser = parse_robots(BLOCK_ALL)
    cache[key] = parser
    return parser


async def is_allowed(session, cache, url, user_agent):
    parser = await get_robots(session, cache, url)
    return parser.can_fetch(user_agent, url)
