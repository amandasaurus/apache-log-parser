Parses log lines from an apache log file in (almost) any format possible

[![Build Status](https://travis-ci.org/rory/apache-log-parser.png?branch=master)](https://travis-ci.org/rory/apache-log-parser)

Usage:

    import apache_log_parser
    line_parser = apache_log_parser.make_parser("%v %h %l %u %t \"%r\" %>s %b")

This creates & returns a function, ``line_parser``, which accepts a line from an apache log file in that format, and will return the parsed values in a dictionary.

Example:

    >>> import apache_log_parser
    >>> line_parser = apache_log_parser.make_parser("%h <<%P>> %t %Dus \"%r\" %>s %b  \"%{Referer}i\" \"%{User-Agent}i\" %l %u")
    >>> log_line_data = line_parser('127.0.0.1 <<6113>> [16/Aug/2013:15:45:34 +0000] 1966093us "GET / HTTP/1.1" 200 3478  "https://example.com/" "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)" - -')
    >>> pprint(log_line_data)
    {'pid': '6113',
     'remote_host': '127.0.0.1',
     'remote_logname': '-',
     'remote_user': '',
     'request_first_line': 'GET / HTTP/1.1',
     'request_header_referer': 'https://example.com/',
     'request_header_user_agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)',
     'response_bytes_clf': '3478',
     'status': '200',
     'time_received': '[16/Aug/2013:15:45:34 +0000]',
     'time_us': '1966093'}
    
The version numbers follow [Semantic Versioning](http://semver.org/).

This package is © 2013 Rory McCann, released under the terms of the GNU GPL v3 (or at your option a later version)


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/rory/apache-log-parser/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

