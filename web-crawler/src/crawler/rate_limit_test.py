from rate_limit import choose_gap, wait_time


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


if __name__ == "__main__":
    test_choose_gap()
    test_wait_time()
    print("All rate limit tests passed")
