def is_retryable(status, error_name):
    if error_name is not None:  # network-level failure: there is no status
        return True
    if status == 429:
        return True
    return status is not None and 500 <= status <= 599


def backoff_delay(attempt, base):
    return base * 2 ** (attempt - 1)
