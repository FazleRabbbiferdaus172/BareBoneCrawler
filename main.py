import socket
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ

selector = DefaultSelector()

host_address = 'example.com'
host_port = 80
url = '/'
request_line = f"GET {url} HTTP/1.1\r\n"
headers = [
        f"Host: {host_address}",
        "Connection: close",
        "User-Agent: Python/3.10"
    ]
request_headers = "\r\n".join(headers)
request = f"{request_line}{request_headers}\r\n\r\n"
encoded = request.encode('ascii')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False)
try:
    sock.connect((host_address, host_port))
except BlockingIOError:
    pass

# sock = socket.socket()
# sock.connect((host_address, host_port))

def start_receive():
    response = b''
    chunk = sock.recv(1024)
    if not chunk:
        selector.unregister(sock.fileno())
    response += chunk
    print(response.decode('utf-8'))


def send_request():
    sock.send(encoded)
    selector.register(sock.fileno(), EVENT_READ, start_receive)

def connected():
    selector.unregister(sock.fileno())
    send_request()
    print("Connected")

selector.register(sock.fileno(), EVENT_WRITE, connected)
print("hi")

def loop():
    while True:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback()
loop()