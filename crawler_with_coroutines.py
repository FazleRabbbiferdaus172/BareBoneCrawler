import socket
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ
import ssl
import re
from bs4 import BeautifulSoup

selector = DefaultSelector()

host_address = 'xkcd.com'
host_port = 443
urls_todo = {'/'}
seen_urls = {'/'}
stopped = False

class Link():

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

class Task:
    def __init__(self, coro):
        self.coro = coro
        f = Future()
        f.set_result(None)
        self.step(f)

    def step(self, future):
        try:
            next_future = self.coro.send(future.result)
        except socket.gaierror as e:
            raise e
        except Exception as e:
            # altough this exception should only pass the coroutine related exception
            # this is creating problems when ssl related exception are not being able to raise their exceptions.
            # try fixing this later.
            print(e)
            return
        
        next_future.add_done_callback(self.step)

class Future:
    
    def __init__(self):
        self.result = None
        self._callbacks = []

    def add_done_callback(self, fn):
        self._callbacks.append(fn)

    def set_result(self, result):
        self.result = result
        for fn in self._callbacks:
            fn(self)

class Fetcher:

    def __init__(self, url, host_address, host_port):
        self.response = b''
        self.url = url
        self.sock = None
        self.host_address = host_address
        self.host_port = host_port

    def fetch(self):
        self.ssl_context = ssl.create_default_context()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        try:
            self.sock.connect((self.host_address, self.host_port))
        except BlockingIOError:
            pass
        f = Future()
        def on_connected():
            f.set_result(None)
        selector.register(self.sock.fileno(), EVENT_WRITE, on_connected)
        yield f
        selector.unregister(self.sock.fileno())
        print('Connected')

        # handle ssl handshake here
        f = Future()

        def on_handshaked():
            f.set_result('Hand Shaked.')

        def try_handshake():
            try:
                
                self.sock.do_handshake()
                on_handshaked()
                # if self.sock.getpeercert():
                #     on_handshaked()
            except ssl.SSLWantReadError:
                try:
                    selector.modify(self.sock.fileno(), EVENT_READ, try_handshake)
                except:
                    selector.register(self.sock.fileno(), EVENT_READ, try_handshake)
            except ssl.SSLWantWriteError:
                try:
                    selector.modify(self.sock.fileno(), EVENT_WRITE, try_handshake)
                except:
                    selector.register(self.sock.fileno(), EVENT_WRITE, try_handshake)
            except Exception as e:
                raise e
        self.sock = self.ssl_context.wrap_socket(self.sock, server_hostname=self.host_address,do_handshake_on_connect=False)
        try_handshake()
        status = yield f
        print(status)
        selector.unregister(self.sock.fileno())

        request = self.build_request(self.url, self.host_address)
        self.sock.send(request)

        while True:
            f = Future()

            def on_readable():
                f.set_result(self.sock.recv(4096))

            selector.register(self.sock.fileno(), EVENT_READ, on_readable)

            chunk = yield f

            selector.unregister(self.sock.fileno())

            if chunk != b'':
                self.response += chunk
            else:
                print(self.response.decode('utf-8'))
                break

            

    def connected(self, key, mask):
        try:
            self.sock = self.ssl_context.wrap_socket(self.sock, server_hostname=self.host_address,do_handshake_on_connect=False)
            self.sock.do_handshake()
            selector.unregister(key.fd)  # check self.sock.fileno() == key.fd
            request = self.build_request(self.url, self.host_address)
            self.sock.send(request)
            selector.register(key.fd, EVENT_READ, self.read_response)
        except ssl.SSLWantReadError:
            selector.modify(key.fd, EVENT_READ, self.do_handshake)
        except ssl.SSLWantWriteError:
            selector.modify(key.fd, EVENT_WRITE, self.do_handshake)

    def do_handshake(self, key, mask):
        try:
            self.sock.do_handshake()
            selector.unregister(key.fd)  # check self.sock.fileno() == key.fd
            request = self.build_request(self.url, self.host_address)
            self.sock.send(request)
            selector.register(key.fd, EVENT_READ, self.read_response)
        except ssl.SSLWantReadError:
            selector.modify(key.fd, EVENT_READ, self.do_handshake)
        except ssl.SSLWantWriteError:
            selector.modify(key.fd, EVENT_WRITE, self.do_handshake)

    @staticmethod
    def build_request(url, host_address):
        request_line = f"GET {url} HTTP/1.1\r\n"
        headers = [
            f"Host: {host_address}",
            "Connection: close",
        ]
        request_headers = "\r\n".join(headers)
        request = f"{request_line}{request_headers}\r\n\r\n"
        encoded_request = request.encode('utf-8')
        return encoded_request
    
    def read_response(self, key, mask):
        global stopped
        try:
            chunk = self.sock.recv(4096)
            # print(chunk.decode('utf-8'))
            if chunk != b'':
                self.response += chunk
            else:
                print("successful response")
                selector.unregister(key.fd)
                links = self.parse_links()
                for link in links.difference(seen_urls):
                    urls_todo.add(link)
                    new_featcher = Fetcher(link, host_address, host_port)
                    new_featcher.fetch()
                
                seen_urls.update(links)
                urls_todo.remove(self.url)
                if not urls_todo:
                    stopped = True
        except ssl.SSLWantReadError:
            selector.modify(key.fd, EVENT_READ, self.do_handshake)
        except ssl.SSLWantWriteError:
            selector.modify(key.fd, EVENT_WRITE, self.do_handshake)

    def parse_links(self):
        links = set()
        response_soup = BeautifulSoup(self.response.decode('utf-8'), 'html.parser')
        all_anchor_tag = response_soup.find_all('a')
        for anchor in all_anchor_tag:
            link = Link(anchor.get('href'))
            if link.is_path_only():
                links.add(anchor.get('href'))
        return links

fetcher = Fetcher('/', host_address, host_port)
coro_gen = fetcher.fetch()
Task(coro_gen)

def event_loop():
    while not stopped:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback()

event_loop()