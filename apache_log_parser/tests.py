
import unittest
import apache_log_parser

class ApacheLogParserTestCase(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
