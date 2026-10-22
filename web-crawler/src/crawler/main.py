import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag ,urlsplit, urlunsplit
from enum import Enum
from pathlib import PurePosixPath
class LinkType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    MEDIA = "media"
    INVALID = "invalid"

MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf"}
URL = "https://books.toscrape.com/"
domains = {urlsplit(URL).hostname}

def classify_url(link,domains):
    splitted_url=urlsplit(link)
    if splitted_url.scheme not in {"http","https"} or not splitted_url.hostname :
        return LinkType.INVALID
    extension = PurePosixPath(splitted_url.path).suffix.lower()
    if extension in MEDIA_EXTENSIONS :
        return LinkType.MEDIA
    if splitted_url.hostname in domains:
        return LinkType.INTERNAL
   
    return LinkType.EXTERNAL
    

def normalize_url(link,baseurl):
       absolute_url=urljoin(baseurl,link)
       absolute_url,fragment=urldefrag(absolute_url)
       return absolute_url
       #splitted_url=urlsplit(absolute_url)
async def fetch_page(url,domains):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            print("URL:", url)
            print("Status:", response.status)
            print("Content-Type:", response.headers.get("Content-Type"))
            print("Size:", len(html), "characters")
            soup = BeautifulSoup(html, "html.parser")
            print("Title:", soup.title.string.strip() if soup.title else "No title")
            links= [a['href'] for a in soup.find_all('a',href=True)]
            results={link_type: set() for link_type in LinkType}
            for link in links :
                normalized_url=normalize_url(link,url)
                results[classify_url(normalized_url,domains)].add(normalized_url)
            for link_type, urls in results.items():
                print(link_type.name, len(urls))
              
# ------this is for test ------

# for t in ["mailto:a@b.com", "https://google.com",
#           "https://books.toscrape.com/media/x.jpg",
#           "https://books.toscrape.com/catalogue/page-2.html"]:
#     print(t, "->", classify_url(t, domains))

if __name__ == "__main__":
    asyncio.run(fetch_page(URL, domains)) 
    # using if cause when test is imported bottom line code will automatically be executed so to prevent it we used this


    # tests will be present in test.py
# assert classify_url("mailto:a@b.com", domains) == LinkType.INVALID  #test if value is true python runs normally if error then will print something
# assert classify_url("https://google.com", domains) == LinkType.INTERNAL# check this output will print something wrong