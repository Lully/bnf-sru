import aiohttp
import asyncio

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.content.read()

async def fetch_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(asyncio.create_task(fetch_url(session, url)))
        results = await asyncio.gather(*tasks)
        return results

if __name__ == '__main__':
    urls = ['https://www.bnf.fr', 'https://catalogue.bnf.fr', 'https://data.bnf.fr']
    results = asyncio.run(fetch_urls(urls))
    print(results)