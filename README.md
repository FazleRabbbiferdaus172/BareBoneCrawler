# BareBoneCrawler is a minimal Web Crawler with asyncio Coroutines.

### Facts
- A non-blocking socket throws an exception from connect, even when it is working normally. This exception replicates the irritating behavior of the underlying C function, which sets errno to EINPROGRESS to tell you it has begun.
- BSD Unix's solution to this problem was select, a C function that waits for an event to occur on a non-blocking socket or a small array of them. Nowadays the demand for Internet applications with huge numbers of connections has led to replacements like poll, then kqueue on BSD and epoll on Linux.
- Python 3.4's DefaultSelector uses the best select-like function available on your system.
- After you register a callback on some event with select api, there also a need of event loop that run calls the callback function when a registered I/O event has occured.
- An async framework builds on the two features we have shown—non-blocking sockets and the event loop—to run concurrent operations on a single thread
- What asynchronous I/O is right for, is applications with many slow or sleepy connections with infrequent events