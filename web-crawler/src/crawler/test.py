from main import classify_url, normalize_url, extract_links, LinkType

domains = {"books.toscrape.com"}


def test_classify_url():
    cases = [
        ("mailto:a@b.com", LinkType.INVALID),
        ("javascript:void(0)", LinkType.INVALID),
        ("ftp://books.toscrape.com/f.txt", LinkType.INVALID),
        ("", LinkType.INVALID),
        ("//books.toscrape.com/a.html", LinkType.INVALID),
        ("https://google.com", LinkType.EXTERNAL),
        ("https://www.books.toscrape.com/", LinkType.EXTERNAL),
        ("https://google.com/a.png", LinkType.MEDIA),
        ("https://books.toscrape.com/media/x.jpg", LinkType.MEDIA),
        ("https://books.toscrape.com/X.JPG", LinkType.MEDIA),
        ("https://books.toscrape.com/a.html?img=x.jpg", LinkType.INTERNAL),
        ("https://BOOKS.toscrape.com:443/catalogue/page-2.html", LinkType.INTERNAL),
        ("https://books.toscrape.com", LinkType.INTERNAL),
        ("https://books.toscrape.com/catalogue/", LinkType.INTERNAL),
        ("https://books.toscrape.com/catalogue/page-2.html", LinkType.INTERNAL),
    ]
    for url, expected in cases:
        result = classify_url(url, domains)
        assert result == expected, f"{url!r}: expected {expected}, got {result}"


def test_normalize_url():
    cases = [
        # (link, base, expected)
        ("page-2.html", "https://books.toscrape.com/catalogue/",
         "https://books.toscrape.com/catalogue/page-2.html"),
        ("../index.html", "https://books.toscrape.com/catalogue/page-2.html",
         "https://books.toscrape.com/index.html"),
        ("/index.html", "https://books.toscrape.com/catalogue/page-2.html",
         "https://books.toscrape.com/index.html"),
        ("https://google.com/x", "https://books.toscrape.com/",
         "https://google.com/x"),
        ("a.html#reviews", "https://books.toscrape.com/",
         "https://books.toscrape.com/a.html"),
        ("a.html?x=1", "https://books.toscrape.com/",
         "https://books.toscrape.com/a.html?x=1"),
        ("//books.toscrape.com/a.html", "https://books.toscrape.com/",
         "https://books.toscrape.com/a.html"),
    ]
    for link, base, expected in cases:
        result = normalize_url(link, base)
        assert result == expected, f"{link!r} on {base!r}: expected {expected}, got {result}"


def test_extract_links():
    html = """<html><head><title>  Test
      Page </title></head><body>
    <a href="a.html">1</a>
    <a href="a.html#top">2</a>
    <a href="https://google.com">3</a>
    <a href="mailto:a@b.com">4</a>
    <a href="/media/x.jpg">5</a>
    <a name="no-href">6</a>
    </body></html>"""
    base = "https://books.toscrape.com/catalogue/"

    title, results = extract_links(html, base, domains)

    assert title == "Test Page", f"title was {title!r}"
    assert results[LinkType.INTERNAL] == {"https://books.toscrape.com/catalogue/a.html"}
    assert results[LinkType.EXTERNAL] == {"https://google.com"}
    assert results[LinkType.INVALID] == {"mailto:a@b.com"}
    assert results[LinkType.MEDIA] == {"https://books.toscrape.com/media/x.jpg"}


def test_extract_links_no_title():
    title, results = extract_links('<a href="a.html">x</a>', "https://books.toscrape.com/", domains)
    assert title == "No title"


if __name__ == "__main__":
    test_classify_url()
    test_normalize_url()
    test_extract_links()
    test_extract_links_no_title()
    print("All tests passed")