
import unittest
import apache_log_parser
import datetime
import doctest
import os.path

class ApacheLogParserTestCase(unittest.TestCase):
    maxDiff = None

    def test_simple(self):
        format_string = "%h <<%P>> %t %Dus \"%r\" %>s %b  \"%{Referer}i\" \"%{User-Agent}i\" %l %u"
        parser = apache_log_parser.make_parser(format_string)
        sample = '127.0.0.1 <<6113>> [16/Aug/2013:15:45:34 +0000] 1966093us "GET / HTTP/1.1" 200 3478  "https://example.com/" "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)" - -'
        log_data = parser(sample)
        self.assertNotEqual(log_data, None)
        self.assertEqual(log_data['status'], '200')
        self.assertEqual(log_data['pid'], '6113')
        self.assertEqual(log_data['request_first_line'], 'GET / HTTP/1.1')
        self.assertEqual(log_data['request_method'], 'GET')
        self.assertEqual(log_data['request_url'], '/')
        self.assertEqual(log_data['request_header_referer'], 'https://example.com/')

        self.assertEqual(log_data['request_header_user_agent'], 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)')

        self.assertEqual(log_data['request_header_user_agent__os__family'], 'Linux')

        self.assertEqual(apache_log_parser.get_fieldnames(format_string), ('remote_host', 'pid', 'time_received', 'time_us', 'request_first_line', 'status', 'response_bytes_clf', 'request_header_referer', 'request_header_user_agent', 'remote_logname', 'remote_user'))

    def test_pr8(self):
        parser = apache_log_parser.make_parser('%h %{remote}p %v %{local}p %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %P %D %{number}n %{SSL_PROTOCOL}x %{SSL_CIPHER}x %k %{UNIQUE_ID}e ')
        data = parser('127.0.0.1 50153 mysite.co.uk 443 [28/Nov/2014:10:03:40 +0000] "GET /mypage/this/that?stuff=all HTTP/1.1" 200 5129 "-" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36" 18572 363701 0 TLSv1.01 MY-CYPHER 0 VHhIfKwQGCMAAEiMUIAAAAF ')
        self.assertEqual(data, {
            'status': '200', 'extension_ssl_protocol': 'TLSv1.01', 'request_header_user_agent__browser__family': 'Chrome',
            'time_us': '363701', 'num_keepalives': '0', 'request_first_line': 'GET /mypage/this/that?stuff=all HTTP/1.1',
            'pid': '18572', 'response_bytes_clf': '5129', 'request_header_user_agent__os__family': u'Windows 7',
            'request_url': '/mypage/this/that?stuff=all', 'request_http_ver': '1.1',
            'request_header_referer': '-', 'server_name': 'mysite.co.uk', 'request_header_user_agent__is_mobile': False,
            'request_header_user_agent__browser__version_string': '37.0.2062',
            'request_header_user_agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36',
            'note_number': '0', 'request_header_user_agent__os__version_string': '',
            'server_port_local': '443', 'request_method': 'GET',
            'server_port_remote': '50153', 'env_unique_id': 'VHhIfKwQGCMAAEiMUIAAAAF',
            'time_received_datetimeobj': datetime.datetime(2014, 11, 28, 10, 3, 40),
            'time_received_isoformat': '2014-11-28T10:03:40', 'remote_host': '127.0.0.1',
            'time_received': '[28/Nov/2014:10:03:40 +0000]',
            'time_received_tz_datetimeobj': datetime.datetime(2014, 11, 28, 10, 3, 40, tzinfo=apache_log_parser.FixedOffset("0000")),
            'time_received_tz_isoformat': '2014-11-28T10:03:40+00:00', 'remote_host': '127.0.0.1',
            'time_received_utc_datetimeobj': datetime.datetime(2014, 11, 28, 10, 3, 40, tzinfo=apache_log_parser.FixedOffset("0000")),
            'time_received_utc_isoformat': '2014-11-28T10:03:40+00:00', 'remote_host': '127.0.0.1',
            'extension_ssl_cipher': 'MY-CYPHER',
        })

        parser = apache_log_parser.make_parser('%A %V %p %P %a \"%r\" \"%{main_call}n\" %{some_time}t %b %>s %D %{UNIQUE_ID}e ')
        data = parser('127.0.0.1 othersite 80 25572 192.168.1.100 "GET /Class/method/ HTTP/1.1" "-" 20141128155031 2266 200 10991 VHiZx6wQGCMAAEiBE8kAAAAA:VHiZx6wQGiMAAGPkBnMAAAAH:VHiZx6wQGiMAAGPkBnMAAAAH ')
        self.assertEqual(data, {
            'status': '200', 'note_main_call': '-', 'time_some_time': '20141128155031',
            'time_us': '10991', 'request_http_ver': '1.1', 'local_ip': '127.0.0.1',
            'pid': '25572', 'request_first_line': 'GET /Class/method/ HTTP/1.1', 'request_method': 'GET',
            'server_port': '80', 'response_bytes_clf': '2266', 'server_name2': 'othersite',
            'request_url': '/Class/method/',
            'env_unique_id': 'VHiZx6wQGCMAAEiBE8kAAAAA:VHiZx6wQGiMAAGPkBnMAAAAH:VHiZx6wQGiMAAGPkBnMAAAAH',
            'remote_ip': '192.168.1.100'})

    def test_issue9(self):
        parser = apache_log_parser.Parser("%h %v %V %l %u %t %r %>s %b %{Referer}i %{User-agent}i")
        log = "10.1.1.1 T1 blah.foo.com - - [08/Mar/2015:18:06:58 -0400] GET /content_images/3/American-University-in-Cairo-AUC.jpeg.jpg HTTP/1.1 404 344 http://www.google.ie AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
        data = parser.parse(log)
        self.assertEqual(data, {
            'status': '404',
            'request_header_referer': 'http://www.google.ie',
            'remote_user': '-',
            'server_name': 'T1',
            'request_http_ver': '1.1',
            'request_header_user_agent': '',
            'request_first_line': 'GET /content_images/3/American-University-in-Cairo-AUC.jpeg.jpg HTTP/1.1',
            'remote_logname': '-',
            'request_method': 'GET',
            'response_bytes_clf': '344',
            'server_name2': 'blah.foo.com',
            'request_url': '/content_images/3/American-University-in-Cairo-AUC.jpeg.jpg',
            'remote_host': '10.1.1.1',
            'time_received': '[08/Mar/2015:18:06:58 -0400]',
            'time_received_datetimeobj': datetime.datetime(2015, 3, 8, 18, 6, 58),
            'time_received_isoformat': '2015-03-08T18:06:58',
            'time_received_tz_datetimeobj': datetime.datetime(2015, 3, 8, 18, 6, 58, tzinfo=apache_log_parser.FixedOffset('-0400')),
            'time_received_tz_isoformat': '2015-03-08T18:06:58-04:00',
            'time_received_utc_datetimeobj': datetime.datetime(2015, 3, 8, 22, 6, 58, tzinfo=apache_log_parser.FixedOffset('0000')),
            'time_received_utc_isoformat': '2015-03-08T22:06:58+00:00',
        })

    def test_issue10_host(self):
        # hostname lookup should work
        format_string = "%h %l %u %t \"%r\" %>s %b"
        parser = apache_log_parser.make_parser(format_string)
        sample = '2001:0db8:85a3:0000:0000:8a2e:0370:7334 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
        log_data = parser(sample)
        self.assertNotEqual(log_data, None)
        self.assertEqual(log_data['remote_host'], '2001:0db8:85a3:0000:0000:8a2e:0370:7334')

    def test_issue10_ip(self):
        # remote ip address should work
        format_string = "%a %l %u %t \"%r\" %>s %b"
        parser = apache_log_parser.make_parser(format_string)
        sample = '2001:0db8:85a3:0000:0000:8a2e:0370:7334 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
        log_data = parser(sample)
        self.assertNotEqual(log_data, None)
        self.assertEqual(log_data['remote_ip'], '2001:0db8:85a3:0000:0000:8a2e:0370:7334')

    def test_issue11(self):
        format_string = "%h <<%P>> %t %Dus \"%r\" %>s %b  \"%{Referer}i\" \"%{User-Agent}i\" %l %u"
        parser = apache_log_parser.make_parser(format_string)
        sample = '127.0.0.1 <<6113>> [16/Aug/2013:15:45:34 +0000] 1966093us "DELETE / HTTP/1.1" 200 3478  "https://example.com/" "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)" - -'
        log_data = parser(sample)
        self.assertNotEqual(log_data, None)
        self.assertEqual(log_data['request_first_line'], 'DELETE / HTTP/1.1')
        self.assertEqual(log_data['request_method'], 'DELETE')

    def test_issue12_nonnum_status(self):
        # In case status is - as opposed to a number
        format_string = "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
        parser = apache_log_parser.make_parser(format_string)
        sample1 = '002:52ee:xxxx::x - - [11/Jun/2014:22:55:45 +0000] "GET /X230_2.51_g2uj10us.iso HTTP/1.1" - 3414853 "refer" "Mozilla/5.0 (X11; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0"'

        log_data1 = parser(sample1)
        self.assertNotEqual(log_data1, None)
        self.assertEqual(log_data1['status'], '-')

    def test_issue10_ipv6(self):
        parser = apache_log_parser.make_parser("%h %a %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"")
        sample1 = '10.178.98.112 2607:5300:60:2c74:: - - [24/Mar/2015:16:40:45 -0400] "GET /category/blog/page/3 HTTP/1.0" 200 41207 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30"'
        log_data1 = parser(sample1)

    def test_doctest_readme(self):
        doctest.testfile("../README.md")



if __name__ == '__main__':
    unittest.main()
