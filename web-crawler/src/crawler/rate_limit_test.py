import asyncio
import time

from rate_limit import choose_gap, wait_time, wait_for_turn


def close(a, b):
    # floats like 0.6 aren't stored exactly, so compare with a tolerance
    return abs(a - b) < 1e-9


def test_choose_gap():
    assert choose_gap(None, 1) == 1  # site states no delay: use our default
    assert choose_gap(0, 1) == 1  # Crawl-delay 0: our default is a floor
    assert choose_gap(1, 1) == 1
    assert choose_gap(5, 1) == 5  # the site asks for more: honor it
    assert choose_gap(60, 1) == 60


def test_wait_time():
    assert wait_time(None, 100, 1) == 0  # first request to a site
    assert close(wait_time(100, 100.4, 1), 0.6)  # only the rest of the gap is left
    assert wait_time(100, 103, 1) == 0  # gap already passed
    assert wait_time(100, 100, 10) == 10  # just requested, long gap
    assert wait_time(100, 100, 1) == 1
    # a slot reserved in the future: wait for it, then the gap after it
    assert close(wait_time(100, 99, 1), 2)


def test_wait_for_turn():
    last = {}

    async def run():
        t0 = time.monotonic()
        await wait_for_turn(last, "site", 0.3)  # first request: no wait
        t1 = time.monotonic()
        await wait_for_turn(last, "site", 0.3)  # second one waits about 0.3s
        t2 = time.monotonic()
        return t1 - t0, t2 - t1

    first, second = asyncio.run(run())
    assert first < 0.1, f"first request waited {first:.2f}s"
    assert 0.25 < second < 0.6, f"second request waited {second:.2f}s"
    assert "site" in last


def test_wait_for_turn_reserves_slots():
    # three tasks ask for a turn at the same moment; each must get its own slot
    last = {}

    async def run():
        t0 = time.monotonic()
        await asyncio.gather(
            wait_for_turn(last, "site", 0.3),
            wait_for_turn(last, "site", 0.3),
            wait_for_turn(last, "site", 0.3),
        )
        return time.monotonic() - t0

    total = asyncio.run(run())
    # slots at about 0s, 0.3s, and 0.6s, so the whole thing takes about 0.6s
    assert 0.5 < total < 1.0, f"three turns took {total:.2f}s"


def test_wait_for_turn_sites_are_independent():
    # a different site has its own clock, so it doesn't wait behind the first
    last = {}

    async def run():
        await wait_for_turn(last, "site-a", 0.5)
        t0 = time.monotonic()
        await wait_for_turn(last, "site-b", 0.5)
        return time.monotonic() - t0

    waited = asyncio.run(run())
    assert waited < 0.1, f"site-b waited {waited:.2f}s"


if __name__ == "__main__":
    test_choose_gap()
    test_wait_time()
    test_wait_for_turn()
    test_wait_for_turn_reserves_slots()
    test_wait_for_turn_sites_are_independent()
    print("All rate limit tests passed")
