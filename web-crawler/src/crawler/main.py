import asyncio
import aiohttp
from bs4 import BeautifulSoup


URL = "https://example.com"


async def fetch_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

            print("URL:", url)
            print("Status:", response.status)
            print("Content-Type:", response.headers.get("Content-Type"))
            print("Size:", len(html), "characters")

            soup = BeautifulSoup(html, "html.parser")
            print("Title:", soup.title.string if soup.title else "No title")


asyncio.run(fetch_page(URL))