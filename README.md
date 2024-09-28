# BareBoneCrawler is a minimal Web Crawler with asyncio Coroutines.
A simple web crawler, initially using an async event loop and callbacks with the select API, followed by an implementation using Python coroutines, and finally using asyncio coroutines. The implementation primarily follows the approach described in
[500 Lines or Less A Web Crawler With asyncio Coroutines](https://aosabook.org/en/500L/a-web-crawler-with-asyncio-coroutines.html) but the site quite old so a lot of changes had to be made. for example https is not handled in the book.

### Facts and challenges
- A non-blocking socket throws an exception from connect, even when it is working normally. This exception replicates the irritating behavior of the underlying C function, which sets errno to EINPROGRESS to tell you it has begun.
- BSD Unix's solution to this problem was select, a C function that waits for an event to occur on a non-blocking socket or a small array of them. Nowadays the demand for Internet applications with huge numbers of connections has led to replacements like poll, then kqueue on BSD and epoll on Linux.
- Python 3.4's DefaultSelector uses the best select-like function available on your system.
- After you register a callback on some event with select api, there also a need of event loop that run calls the callback function when a registered I/O event has occured.
- An async framework builds on the two features we have shown—non-blocking sockets and the event loop—to run concurrent operations on a single thread
- What asynchronous I/O is right for, is applications with many slow or sleepy connections with infrequent events
- Connection: close head in the request is important, some websites keep the connection open thus it never returns the b'' we expect.
- Using the ssl library, you cannot simply establish a non-blocking HTTPS connection in Python. Otherwise, you will always encounter a 400 Bad Request error, where an HTTP request is made on an HTTPS port. Resolving this issue requires some additional steps.First, you need to establish a connection and ensure that the connection is fully established (i.e., the file descriptor is writable). Then, you should wrap the socket in SSL context with do_handshake_on_connect=False. This is necessary due to the non-blocking nature of the socket, which can lead to timing issues with the handshake, resulting in the 400 Bad Request error.
Since the handshake is not automatic in this case, you need to perform it manually. This comes with its own set of challenges, including handling SSLWantReadError. You must catch this exception and attempt to handshake again when the file descriptor is available for reading.one of the important reference [Notes on non-blocking sockets](https://docs.python.org/3/library/ssl.html#notes-on-non-blocking-sockets), dont even remenber how many links and comments i went through.
- Now again, some websites were helpful and return a 400 response then there were some which didn't even botherd to send any response regarding http requst over https port issue, such expamle is the 'xkcd.com' and for a while did not even understand what was the problem. the recv only reviced response of b'' and that it nothing else.
- The first packet exchanged in any version of any SSL/TLS handshake is the client hello packet which signifies the client's wish to establish a secure context. So, the discirptor has to be writable? and When an SSL/TLS handshake is complete on a non-blocking socket, the file descriptor will become writable again?. This means that the socket is ready to send request? so select should register a event_write with on_handshaked callback?


### REFERENCES and READS
- [Notes on non-blocking sockets](https://docs.python.org/3/library/ssl.html#notes-on-non-blocking-sockets)
- [A walk-through of an SSL handshake](https://commandlinefanatic.com/cgi-bin/showarticle.cgi?article=art059)
- [Nonblocking I/O](https://copyconstruct.medium.com/nonblocking-i-o-99948ad7c957)