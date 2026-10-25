from robots import parse_robots
def test_parse_robots():

    text = "\n".join([
    "User-agent: *",
    "Disallow: /admin/",
    "Disallow: /search",
    "",
    "User-agent: BadBot",
    "Disallow: /",
    ])
    rp = parse_robots(text)
    assert rp.can_fetch("MyCrawler", "https://example.com/about") == True
    assert rp.can_fetch("MyCrawler", "https://example.com/admin/users") == False
    assert rp.can_fetch("Badbot", "https://example.com/") == False
    assert rp.can_fetch("Mycrawl", "https://example.com/admin") == True
    assert not rp.can_fetch("mycrawl","https://example.com/search?q=books")
    rp_empty = parse_robots("")
    assert rp_empty.can_fetch("MyCrawler", "https://example.com/anything") ==True
    text2="\n".join([
        "User-agent: *",
        "Disallow:",
    ])
    rp_noblock=parse_robots(text2)
    assert rp_noblock.can_fetch("hi","https://example.com/nothing")
    text3="\n".join([
            "User-agent: *",
            "Disallow:/",
        ])
    assert not parse_robots(text3).can_fetch("myblock","https://example.com/nothing")
if __name__ == "__main__":
    test_parse_robots()
    print("All robots tests passed")