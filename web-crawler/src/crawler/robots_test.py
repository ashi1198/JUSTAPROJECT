from robots import parse_robots, robots_url
from robots import parser_for_response, BLOCK_ALL

AGENT = "MyCrawler"


def rules(*lines):
    # collects any number of arguments into one robots.txt text
    return "\n".join(lines)


def test_basic_rules():
    rp = parse_robots(
        rules(
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /search",
            "",
            "User-agent: BadBot",
            "Disallow: /",
        )
    )
    assert rp.can_fetch(AGENT, "https://example.com/about")
    assert not rp.can_fetch(AGENT, "https://example.com/admin/users")
    # BadBot has its own block, which is used instead of the * block for that crawler
    assert not rp.can_fetch("BadBot", "https://example.com/about")


def test_agent_matching_is_case_insensitive():
    rp = parse_robots(rules("User-agent: BadBot", "Disallow: /"))
    assert not rp.can_fetch("badbot", "https://example.com/")
    assert not rp.can_fetch("BADBOT", "https://example.com/")
    # a crawler with a different name has no matching block, so nothing is blocked
    assert rp.can_fetch(AGENT, "https://example.com/")


def test_empty_file_allows_all():
    # no rules means no restrictions (this is also how a 404 robots.txt is handled)
    rp = parse_robots("")
    assert rp.can_fetch(AGENT, "https://example.com/anything")


def test_empty_disallow_blocks_nothing():
    # "Disallow:" with nothing after the colon is the opposite of "Disallow: /"
    rp = parse_robots(rules("User-agent: *", "Disallow:"))
    assert rp.can_fetch(AGENT, "https://example.com/anything")


def test_disallow_root_blocks_everything():
    # this is also the "block the whole site" fallback for server errors
    rp = parse_robots(rules("User-agent: *", "Disallow: /"))
    assert not rp.can_fetch(AGENT, "https://example.com/")
    assert not rp.can_fetch(AGENT, "https://example.com")  # no path counts as "/"
    assert not rp.can_fetch(AGENT, "https://example.com/a/b/c.html")


def test_prefix_with_trailing_slash():
    # rules are literal prefix matches on the path
    rp = parse_robots(rules("User-agent: *", "Disallow: /admin/"))
    assert not rp.can_fetch(AGENT, "https://example.com/admin/")
    assert not rp.can_fetch(AGENT, "https://example.com/admin/users")
    # "/admin" is shorter than the rule "/admin/", so it doesn't start with it
    assert rp.can_fetch(AGENT, "https://example.com/admin")
    assert rp.can_fetch(AGENT, "https://example.com/administrator")


def test_prefix_without_trailing_slash():
    # without the slash, the rule is broader: anything starting with "/admin"
    rp = parse_robots(rules("User-agent: *", "Disallow: /admin"))
    assert not rp.can_fetch(AGENT, "https://example.com/admin")
    assert not rp.can_fetch(AGENT, "https://example.com/admin/users")
    assert not rp.can_fetch(AGENT, "https://example.com/administrator")
    assert rp.can_fetch(AGENT, "https://example.com/about")


def test_query_string_is_part_of_the_match():
    rp = parse_robots(rules("User-agent: *", "Disallow: /search"))
    # the path starts with /search, so the query string doesn't save it
    assert not rp.can_fetch(AGENT, "https://example.com/search?q=books")
    # the rule matches the START of the path, not anywhere in the URL
    assert rp.can_fetch(AGENT, "https://example.com/find?q=search")


def test_full_user_agent_string():
    # the header your crawler really sends; only the part before "/" is matched
    full = "MyCrawler/1.0 (student project)"
    rp = parse_robots(rules("User-agent: MyCrawler", "Disallow: /private/"))
    assert not rp.can_fetch(full, "https://example.com/private/x")
    assert rp.can_fetch(full, "https://example.com/public")
    # a block for one crawler doesn't affect other crawlers
    assert rp.can_fetch("OtherBot", "https://example.com/private/x")


def test_parser_ignores_host():
    # can_fetch only looks at the path, so one parser must be used per site
    rp = parse_robots(rules("User-agent: *", "Disallow: /admin/"))
    assert not rp.can_fetch(AGENT, "https://some-other-site.com/admin/x")


def test_robots_url():
    cases = [
        (
            "https://books.toscrape.com/catalogue/page-2.html",
            "https://books.toscrape.com/robots.txt",
        ),
        (
            "https://books.toscrape.com/a.html?x=1#top",
            "https://books.toscrape.com/robots.txt",
        ),
        ("http://localhost:8000/a", "http://localhost:8000/robots.txt"),
        ("https://books.toscrape.com", "https://books.toscrape.com/robots.txt"),
    ]
    for url, expected in cases:
        result = robots_url(url)
        assert result == expected, f"{url!r}: expected {expected!r}, got {result!r}"


def test_parser_for_response():
    rules_text = "User-agent: *\nDisallow: /admin/"
    blocked_url = "https://example.com/admin/x"
    open_url = "https://example.com/about"

    # (status, body text, url to check, should it be allowed?)
    cases = [
        (200, rules_text, blocked_url, False),  # a real file is followed
        (200, rules_text, open_url, True),
        (201, rules_text, blocked_url, False),  # any 2xx counts as success
        (204, "", open_url, True),  # empty file means no restrictions
        (301, "", open_url, True),  # redirect: treated as no rules
        (403, "", open_url, True),  # 4xx means no file: allow everything
        (404, "", open_url, True),
        (410, "", open_url, True),
        (429, "", open_url, False),  # told to slow down: be cautious
        (500, "", open_url, False),  # server errors: rules unknown, block
        (503, "", open_url, False),
        (999, "", open_url, False),  # unrecognized status: block
    ]
    for status, text, url, expected in cases:
        parser = parser_for_response(status, text)
        result = parser.can_fetch("MyCrawler", url)
        assert (
            result == expected
        ), f"status {status} on {url!r}: expected {expected}, got {result}"


def test_block_all_constant():
    # the fallback text used for network errors must block everything
    parser = parse_robots(BLOCK_ALL)
    assert not parser.can_fetch("MyCrawler", "https://example.com/")
    assert not parser.can_fetch("MyCrawler", "https://example.com/anything/at/all")


if __name__ == "__main__":
    test_basic_rules()
    test_agent_matching_is_case_insensitive()
    test_empty_file_allows_all()
    test_empty_disallow_blocks_nothing()
    test_disallow_root_blocks_everything()
    test_prefix_with_trailing_slash()
    test_prefix_without_trailing_slash()
    test_query_string_is_part_of_the_match()
    test_full_user_agent_string()
    test_parser_ignores_host()
    test_robots_url()
    test_parser_for_response()
    test_block_all_constant()
    print("All robots tests passed")
