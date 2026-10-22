from main import classify_url, LinkType

domains = {"books.toscrape.com"}

tests = [
    ("mailto:a@b.com", LinkType.INVALID),
    ("https://google.com", LinkType.EXTERNAL),
    ("https://books.toscrape.com/media/x.jpg", LinkType.MEDIA),
    ("https://books.toscrape.com/catalogue/page-2.html", LinkType.INTERNAL),
]

for url, expected in tests:
    result = classify_url(url, domains)
    assert result == expected, f"{url}: expected {expected}, got {result}"

print("All tests passed")