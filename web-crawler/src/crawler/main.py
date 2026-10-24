import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag ,urlsplit, urlunsplit
from enum import Enum
from pathlib import PurePosixPath
from collections import deque
import sys
class LinkType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    MEDIA = "media"
    INVALID = "invalid"
text ="" 
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf"}
URL = sys.argv[1] if len(sys.argv)>1 else  "https://books.toscrape.com/"
domains = {urlsplit(URL).hostname}
max_pages=10
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
    #    absolute_url,fragment=urldefrag(absolute_url)
    #    since fragment stays unused we will use this dirctly
       return urldefrag(absolute_url).url
                   
async def fetch_html(session,url):
    try:
        async with session.get(url) as res:
            if res.status != 200 :
                return None 
            content_type = res.headers.get("Content-Type","")
            if "text/html" not in content_type:
                return None
            html=await res.text()
            return html
    except (aiohttp.ClientError,asyncio.TimeoutError) as e:
        print(f"error: {type(e).__name__}: {e}".strip())
        return None
    


def extract_links(html,base_url,domains):
    soup = BeautifulSoup(html, "html.parser")
    links= [a['href'] for a in soup.find_all('a',href=True)]
    results={link_type: set() for link_type in LinkType}
    for link in links :
        normalized_url=normalize_url(link,base_url)
        results[classify_url(normalized_url,domains)].add(normalized_url)
    title=" ".join(soup.title.get_text().split()) if soup.title else "No title"
    return title,results    


async def crawl(seed,domains,max_pages):
    queue=deque()
    seen=set()
    pages_crawled=0
    queue.append(seed)
    seen.add(seed)
    timeout=aiohttp.ClientTimeout(total=10)
    headers = {"User-Agent": "MyCrawler/1.0 (ashi project)"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        while queue and pages_crawled < max_pages :
            url=queue.popleft()
            html=await fetch_html(session,url)
            await asyncio.sleep(1)
            pages_crawled+=1
            if html is None:
                print(f"[{pages_crawled}] {url} failed")
                continue
            print(f"[{pages_crawled}] {url}")
            title,links=extract_links(html,url,domains)
            print("Title:", title.strip() )
            for link_type, urls in links.items():
                    print(link_type.name, len(urls))
            for internal in sorted(links[LinkType.INTERNAL]):
                if internal not in seen:
                  seen.add(internal)
                  queue.append(internal)
            
   

if __name__ == "__main__":
    asyncio.run(crawl(URL,domains,max_pages)) 
    # using if case when test is imported bottom line code will automatically be executed so to prevent it we used this

