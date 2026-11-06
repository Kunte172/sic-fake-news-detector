import io
import socket
import time
import unittest
from email.message import Message
from unittest.mock import patch, Mock
from backend.app import url_extraction as u

BODY = b'<html><nav><p>Skip navigation</p></nav><article><p>' + b'Independent reporting on a public event. ' * 4 + b'</p><script>ignore me</script></article></html>'

class Response:
    def __init__(self, body=BODY, status=200, headers=None):
        self.status = status
        self.headers = Message()
        for k,v in (headers or {'Content-Type':'text/html; charset=utf-8'}).items():
            self.headers[k] = v
        self.stream = io.BytesIO(body)
    def getheader(self, key, default=None):
        return self.headers.get(key, default)
    def read1(self, size):
        return self.stream.read(size)

class UrlTests(unittest.TestCase):
    def test_reject_nonpublic_credential_and_non_http_urls(self):
        for url in ['file:///etc/passwd','ftp://example.com/a','http://localhost/a','http://127.0.0.1','http://10.1.1.1','http://169.254.169.254','http://[::1]','http://[::ffff:127.0.0.1]','https://user:pass@example.com','https://example.com:444','https://example.com/\r\nx:1','https://example.com\\@127.0.0.1']:
            with self.subTest(url=url), self.assertRaises(u.UrlError):
                u.validate_url(url)

    def test_mixed_public_private_dns_is_blocked(self):
        records=[(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443)) for ip in ['8.8.8.8','127.0.0.1']]
        with patch.object(u.socket,'getaddrinfo',return_value=records), self.assertRaises(u.UrlError):
            u.resolve_public('news.example',443,time.monotonic()+2)

    def test_pin_destination_keep_tls_hostname(self):
        c=u.connect_pinned('news.example',443,'8.8.8.8','https',2)
        self.assertEqual(c.host,'news.example')
        self.assertTrue(c._context.check_hostname)
        with patch.object(u.socket,'create_connection') as connect:
            c._create_connection(('news.example',443),2,None)
            connect.assert_called_once_with(('8.8.8.8',443),2,None)

    def run_fetch(self, responses):
        connections=[]
        for response in responses:
            c=Mock();c.sock=None;c.getresponse.return_value=response;connections.append(c)
        with patch.object(u,'resolve_public',return_value='8.8.8.8'), patch.object(u,'connect_pinned',side_effect=connections):
            result=u.fetch_article('https://news.example/article')
        for c in connections:
            c.close.assert_called_once()
        return result

    def test_extract_primary_content_and_close(self):
        text=self.run_fetch([Response()])
        self.assertIn('Independent reporting',text)
        self.assertNotIn('navigation',text)
        self.assertNotIn('ignore me',text)

    def test_redirect_to_private_is_never_connected(self):
        c=Mock();c.sock=None;c.getresponse.return_value=Response(status=302,headers={'Location':'http://127.0.0.1/admin'})
        with patch.object(u,'resolve_public',return_value='8.8.8.8'), patch.object(u,'connect_pinned',return_value=c) as connect:
            with self.assertRaises(u.UrlError):
                u.fetch_article('https://news.example/article')
            self.assertEqual(connect.call_count,1)
            c.close.assert_called_once()

    def test_relative_redirect_and_limit(self):
        text=self.run_fetch([Response(status=302,headers={'Location':'/next'}),Response()])
        self.assertIn('Independent',text)
        with self.assertRaises(u.UrlError):
            self.run_fetch([Response(status=302,headers={'Location':'/loop'}) for _ in range(4)])

    def test_reject_content_type_encoding_and_http_errors(self):
        for response in [Response(headers={'Content-Type':'application/pdf'}),Response(headers={'Content-Type':'text/html','Content-Encoding':'gzip'}),Response(status=403),Response(body=b'<p>short</p>')]:
            with self.subTest(response=response), self.assertRaises(u.UrlError):
                self.run_fetch([response])

    def test_size_limit_header_and_stream(self):
        for r in [Response(headers={'Content-Type':'text/html','Content-Length':str(u.MAX_BYTES+1)}),Response(body=b'x'*(u.MAX_BYTES+1))]:
            with self.assertRaises(u.UrlError) as exc:
                self.run_fetch([r])
            self.assertEqual(exc.exception.status_code,413)

    def test_socket_timeout_is_504(self):
        c=Mock();c.sock=None;c.request.side_effect=socket.timeout()
        with patch.object(u,'resolve_public',return_value='8.8.8.8'),patch.object(u,'connect_pinned',return_value=c),self.assertRaises(u.UrlError) as exc:
            u.fetch_article('https://news.example')
        self.assertEqual(exc.exception.status_code,504)
        c.close.assert_called_once()

    def test_deadline_exhaustion(self):
        with self.assertRaises(u.UrlError) as exc:
            u.remaining(time.monotonic()-1)
        self.assertEqual(exc.exception.status_code,504)
