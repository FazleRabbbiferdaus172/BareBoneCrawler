import re
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from asyncio import Queue


host_address = 'https://xkcd.com'
max_redirect=10
max_task=10

class Link:

    protocol_pattern = re.compile(r'(https+)')
    host_name_pattern = re.compile(r'(https?)?:?//([\w.-]+)/?')

    def __init__(self, url):
        self.url = url if url else '/'

    def get_host_name(self):
        host_name = False
        match = re.match(self.host_name_pattern, self.url)
        if match:
            host_name = match.group(2)
        return host_name

    def get_protocol(self):
        protocol = False
        match = re.match(self.protocol_pattern, self.url)
        if match:
            protocol = match.group()
        return protocol

    def get_path(self):
        path = ''
        return path

    def is_url(self):
        result = False
        has_protocol = re.match(self.protocol_pattern, self.url)
        has_host_name = re.match(self.host_name_pattern, self.url)
        result = True if has_host_name or has_protocol else False
        return result

    def is_path_only(self):
        host_name = self.get_host_name()
        return not (self.is_url() or self.is_fragment_only() or host_name)

    def is_fragment_only(self):
        return self.url[0] == '#'

    def __str__(self):
        return f"{self.url}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.url})"

class Crawler:
    def __init__(self, root_url, max_redirect=10):
        self.max_tasks = max_task
        self.max_redirect = max_redirect
        self.q = Queue()
        self.seen_urls = set()
        self.session = aiohttp.ClientSession(loop=loop)
        self.q.put_nowait((root_url, self.max_redirect))

    # @asyncio.coroutine
    async def crawl(self):
        works = [asyncio.Task(self.work()) for _ in range(self.max_tasks)]

        await self.q.join()
        for w in works:
            w.cancel()

    # @asyncio.coroutine
    async def work(self):
        while True:
            url, max_redirect = await self.q.get()

            await self.fetch(url, max_redirect)
            self.q.task_done()

    # @asyncio.coroutine
    async def fetch(self, url, max_redirect):
        response = await self.session.get(url, allow_redirects=False)
        response_body = await response.read()
        print(f"read response of url {url}")
        print("____________________________")
        try:
            if 'location' in response.headers:
                if max_redirect > 0:
                    next_url = response.headers['location']
                    if next_url in self.seen_urls:
                        return
                    self.seen_urls(next_url)
                    self.q.put_nowait((next_url, max_redirect - 1))
            else:
                links = self.parse_links(response_body)
                self.collect_links(links=links)
        except Exception as e:
            print(e)
        finally:
            await response.release()
    
    def parse_links(self, response_body):
        links = set()
        response_soup = BeautifulSoup(
            response_body.decode('utf-8'), 'html.parser')
        all_anchor_tag = response_soup.find_all('a')
        for anchor in all_anchor_tag:
            link = Link(anchor.get('href'))
            if link.is_path_only():
                links.add(anchor.get('href'))
        return links
    
    def collect_links(self, links):
        for link in links.difference(self.seen_urls):
            self.q.put_nowait((host_address+link, self.max_redirect - 1))
 
loop = asyncio.get_event_loop()

crawler = Crawler('https://xkcd.com', max_redirect)

loop.run_until_complete(crawler.crawl())
