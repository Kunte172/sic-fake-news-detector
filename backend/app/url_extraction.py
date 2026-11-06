"""Bounded public HTTP(S) fetching with IP pinning and no proxy/cookie forwarding."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import threading
import time
from urllib.parse import urlsplit, urlunsplit, urljoin

MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
TOTAL_SECONDS = 12
IO_SECONDS = 3
_RESOLVER = ThreadPoolExecutor(max_workers=4, thread_name_prefix='article-dns')
_DNS_SLOTS = threading.BoundedSemaphore(4)

class UrlError(Exception):
    def __init__(self, detail, status_code=422):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def remaining(deadline):
    value = deadline - time.monotonic()
    if value <= 0:
        raise UrlError('Article request timed out', 504)
    return min(IO_SECONDS, value)


def public_ip(value):
    address = ipaddress.ip_address(value)
    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast


def validate_url(url):
    if not isinstance(url, str) or not url or len(url) > 2048:
        raise UrlError('URL must contain 1–2048 characters')
    if re.search(r'[\x00-\x20\x7f\\]', url):
        raise UrlError('URL contains whitespace, controls or backslashes')
    try:
        parts = urlsplit(url)
        if parts.scheme.lower() not in ('http', 'https') or not parts.hostname:
            raise ValueError()
        if parts.username is not None or parts.password is not None:
            raise ValueError()
        host = parts.hostname.encode('idna').decode('ascii').lower().rstrip('.')
        if '%' in host or host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
            raise ValueError()
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        if port != (443 if parts.scheme == 'https' else 80):
            raise ValueError()
        try:
            if not public_ip(host):
                raise UrlError('Private or special IP addresses are blocked')
        except ValueError:
            pass
    except (ValueError, UnicodeError):
        raise UrlError('Use a public HTTP(S) URL on its standard port, without credentials') from None
    return parts, host, port


def resolve_public(host, port, deadline):
    # Bound active DNS workers, including requests that outlive their timeout.
    if not _DNS_SLOTS.acquire(blocking=False):
        raise UrlError('DNS resolver busy; try again', 503)
    try:
        future = _RESOLVER.submit(socket.getaddrinfo, host, port, 0, socket.SOCK_STREAM)
    except Exception:
        _DNS_SLOTS.release()
        raise
    future.add_done_callback(lambda _: _DNS_SLOTS.release())
    try:
        answers = future.result(timeout=remaining(deadline))
    except FutureTimeout:
        raise UrlError('DNS lookup timed out', 504) from None
    except OSError:
        raise UrlError('Cannot resolve article host', 502) from None
    ips = list(dict.fromkeys(answer[4][0] for answer in answers))
    if not ips or any(not public_ip(ip) for ip in ips):
        raise UrlError('Host resolves to a private or special address')
    return ips[0]


def connect_pinned(host, port, ip, scheme, timeout):
    cls = http.client.HTTPSConnection if scheme == 'https' else http.client.HTTPConnection
    connection = cls(host, port, timeout=timeout)
    # http.client still uses the original host for Host, TLS SNI and certificate
    # verification; only the TCP destination is replaced with a validated IP.
    connection._create_connection = lambda address, timeout=timeout, source_address=None: socket.create_connection(
        (ip, port), timeout, source_address)
    return connection


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.paragraphs = []
        self.primary = []
        self.current = None
        self.is_primary = False

    def handle_starttag(self, tag, attrs):
        if tag in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
            if tag == 'br' and self.current is not None:
                self.current.append(' ')
            return
        if tag == 'p':
            self.finish_paragraph()
            if not any(t in self.stack for t in ('script','style','noscript','nav','header','footer','aside','form')):
                self.current = []
                self.is_primary = any(t in self.stack for t in ('article','main'))
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == 'p':
            self.finish_paragraph()
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, data):
        if self.current is not None and not any(t in self.stack for t in ('script','style','noscript')):
            self.current.append(data)

    def finish_paragraph(self):
        if self.current is not None:
            value = re.sub(r'\s+', ' ', ''.join(self.current)).strip()
            if value:
                self.paragraphs.append(value)
                if self.is_primary:
                    self.primary.append(value)
        self.current = None


def extract_html(data, charset='utf-8'):
    try:
        decoded = data.decode(charset, errors='replace')
    except LookupError:
        decoded = data.decode('utf-8', errors='replace')
    parser = ArticleParser()
    parser.feed(decoded)
    parser.finish_paragraph()
    text = '\n\n'.join(parser.primary or parser.paragraphs)
    if not 80 <= len(text) <= 50_000:
        raise UrlError('Cannot extract an article of 80–50000 characters; paste its text instead')
    return text


def fetch_article(url):
    deadline = time.monotonic() + TOTAL_SECONDS
    for hop in range(MAX_REDIRECTS + 1):
        parts, host, port = validate_url(url)
        ip = resolve_public(host, port, deadline)
        connection = connect_pinned(host, port, ip, parts.scheme, remaining(deadline))
        timer = None
        try:
            path = urlunsplit(('', '', parts.path or '/', parts.query, ''))
            connection.request('GET', path, headers={'User-Agent':'SIC-Fake-News-Lens/1.0', 'Accept':'text/html, application/xhtml+xml', 'Accept-Encoding':'identity'})
            if connection.sock:
                active_socket = connection.sock
                active_socket.settimeout(remaining(deadline))
                def abort_socket():
                    try:
                        active_socket.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    active_socket.close()
                timer = threading.Timer(max(.001, deadline - time.monotonic()), abort_socket)
                timer.daemon = True
                timer.start()
            response = connection.getresponse()
            if response.status in (301,302,303,307,308):
                location = response.getheader('Location')
                if not location or hop == MAX_REDIRECTS:
                    raise UrlError('Missing redirect location or too many redirects')
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise UrlError('Article server returned an unsuccessful response', 502)
            media = response.headers.get_content_type()
            if media not in ('text/html', 'application/xhtml+xml'):
                raise UrlError('Article URL must return HTML')
            if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
                raise UrlError('Compressed article responses are not supported')
            length = response.getheader('Content-Length')
            if length:
                try:
                    if int(length) < 0 or int(length) > MAX_BYTES:
                        raise UrlError('Article exceeds the 2 MiB download limit', 413)
                except ValueError:
                    raise UrlError('Invalid article Content-Length') from None
            chunks, count = [], 0
            while True:
                if connection.sock:
                    connection.sock.settimeout(remaining(deadline))
                remaining(deadline)
                chunk = response.read1(min(65536, MAX_BYTES + 1 - count))
                if not chunk:
                    break
                count += len(chunk)
                if count > MAX_BYTES:
                    raise UrlError('Article exceeds the 2 MiB download limit', 413)
                chunks.append(chunk)
            remaining(deadline)
            return extract_html(b''.join(chunks), response.headers.get_content_charset() or 'utf-8')
        except (TimeoutError, socket.timeout):
            raise UrlError('Article request timed out', 504) from None
        except (OSError, http.client.HTTPException, UnicodeError):
            remaining(deadline)
            raise UrlError('Cannot securely download article', 502) from None
        finally:
            if timer:
                timer.cancel()
            connection.close()
    raise UrlError('Too many redirects')
