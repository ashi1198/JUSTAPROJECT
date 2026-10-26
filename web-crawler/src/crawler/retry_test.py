from main import is_retryable, backoff_delay


def test_is_retryable():
    # network-level failures have no status, only an error name
    assert is_retryable(None, "TimeoutError")
    assert is_retryable(None, "ClientConnectorError")
    # server trouble and "slow down" are worth another try
    assert is_retryable(500, None)
    assert is_retryable(503, None)
    assert is_retryable(429, None)
    # asking again gets the same answer
    assert not is_retryable(404, None)
    assert not is_retryable(403, None)
    assert not is_retryable(410, None)
    # the request worked (the page just wasn't HTML)
    assert not is_retryable(200, None)


def test_backoff_delay():
    assert backoff_delay(1, 2) == 2
    assert backoff_delay(2, 2) == 4
    assert backoff_delay(3, 2) == 8


if __name__ == "__main__":
    test_is_retryable()
    test_backoff_delay()
    print("All retry tests passed")
