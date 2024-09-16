import socket
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ
import ssl
import time

selector = DefaultSelector()

host_address = 'xkcd.com'
host_port = 443
urls_todo = set(['/'])
seen_urls = set(['/'])


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
        selector.register(self.sock.fileno(), EVENT_WRITE, self.connected)

    def connected(self, key, mask):
        try:
            self.sock = self.ssl_context.wrap_socket(self.sock, server_hostname=self.host_address,do_handshake_on_connect=False)
            self.sock.do_handshake()
            print(f"Conected to {self.host_address}:{self.host_port}")
            print(f"{self.sock.getpeername()}")
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
        chunk = self.sock.recv(4096)
        # print(chunk.decode('utf-8'))
        if chunk != b'':
            self.response += chunk
        else:
            print(self.response.decode('utf-8'))
            selector.unregister(key.fd)
            links = self.parse_links()
                # for link in links.difference(seen_urls):
                #     urls_todo.add(link)
                #     new_featcher = Fetcher(link, host_address, host_port)
                #     new_featcher.fetch()

    def parse_links(self):
        return ['/domains/example']

fetcher = Fetcher('/', host_address, host_port)
fetcher.fetch()

while True:
    events = selector.select()
    for event_key, event_mask in events:
        callback = event_key.data
        callback(event_key, event_mask)
