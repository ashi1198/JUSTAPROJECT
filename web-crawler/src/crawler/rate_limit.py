import time, asyncio


def choose_gap(crawl_delay, default_gap):
    # the site's Crawl-delay if it asks for more than our default, else our default
    # (None means the site states no delay; 0 is treated the same, because
    # our own default is a floor)
    if crawl_delay is None:
        return default_gap
    return max(default_gap, crawl_delay)


def wait_time(last_req, now, min_gap):
    # seconds to wait before the next request to a site
    if last_req is None:
        return 0  # no previous request: go straight away
    elapsed = now - last_req
    return max(0, min_gap - elapsed)


async def wait_for_turn(last_requests, key, gap):
    now = time.monotonic()
    wait = wait_time(last_requests.get(key), now, gap)
    last_requests[key] = now + wait  # reserve the slot BEFORE sleeping
    await asyncio.sleep(wait)
