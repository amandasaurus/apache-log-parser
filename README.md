Parses log lines from an apache log file in (almost) any format possible

[![Build Status](https://travis-ci.org/rory/apache-log-parser.png?branch=master)](https://travis-ci.org/rory/apache-log-parser)

Installation
============

    pip install apache-log-parser

Usage
=====

    import apache_log_parser
    line_parser = apache_log_parser.make_parser("%v %h %l %u %t \"%r\" %>s %b")

This creates & returns a function, ``line_parser``, which accepts a line from an apache log file in that format, and will return the parsed values in a dictionary.

Example
=======

    >>> import apache_log_parser
    >>> line_parser = apache_log_parser.make_parser("%h <<%P>> %t %Dus \"%r\" %>s %b  \"%{Referer}i\" \"%{User-Agent}i\" %l %u")
    >>> log_line_data = line_parser('127.0.0.1 <<6113>> [16/Aug/2013:15:45:34 +0000] 1966093us "GET / HTTP/1.1" 200 3478  "https://example.com/" "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)" - -')
    >>> from pprint import pprint
    >>> pprint(log_line_data)
    {'pid': '6113',
     'remote_host': '127.0.0.1',
     'remote_logname': '-',
     'remote_user': '',
     'request_first_line': 'GET / HTTP/1.1',
     'request_header_referer': 'https://example.com/',
     'request_header_user_agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18)',
     'request_header_user_agent__browser__family': 'Other',
     'request_header_user_agent__browser__version_string': '',
     'request_header_user_agent__is_mobile': False,
     'request_header_user_agent__os__family': 'Linux',
     'request_header_user_agent__os__version_string': '',
     'request_http_ver': '1.1',
     'request_method': 'GET',
     'request_url': '/',
     'response_bytes_clf': '3478',
     'status': '200',
     'time_received': '[16/Aug/2013:15:45:34 +0000]',
     'time_received_datetimeobj': datetime.datetime(2013, 8, 16, 15, 45, 34),
     'time_received_isoformat': '2013-08-16T15:45:34',
     'time_received_tz_datetimeobj': datetime.datetime(2013, 8, 16, 15, 45, 34, tzinfo='0000'),
     'time_received_tz_isoformat': '2013-08-16T15:45:34+00:00',
     'time_received_utc_datetimeobj': datetime.datetime(2013, 8, 16, 15, 45, 34, tzinfo='0000'),
     'time_received_utc_isoformat': '2013-08-16T15:45:34+00:00',
     'time_us': '1966093'}

There is a at least one key/value in the returned dictionary for each apache log placeholder. Some have more than one (e.g. all the `time_received*`).

The version numbers follow [Semantic Versioning](http://semver.org/).


Supported values
========
```python
    '%a'  #	Remote IP-address
    '%A'  #	Local IP-address
    '%B'  #	Size of response in bytes, excluding HTTP headers.
    '%b'  #	Size of response in bytes, excluding HTTP headers. In CLF format, i.e. a '-' rather than a 0 when no bytes are sent.
    '%D'  #	The time taken to serve the request, in microseconds.
    '%f'  #	Filename
    '%h'  #	Remote host
    '%H'  #	The request protocol
    '%k'  #	Number of keepalive requests handled on this connection. Interesting if KeepAlive is being used, so that, for example, a '1' means the first keepalive request after the initial one, '2' the second, etc...; otherwise this is always 0 (indicating the initial request). Available in versions 2.2.11 and later.
    '%l'  #	Remote logname (from identd, if supplied). This will return a dash unless mod_ident is present and IdentityCheck is set On.
    '%m'  #	The request method
    '%p'  #	The canonical port of the server serving the request
    '%P'  #	The process ID of the child that serviced the request.
    '%q'  #	The query string (prepended with a ? if a query string exists, otherwise an empty string)
    '%r'  #	First line of request
    '%R'  #	The handler generating the response (if any).
    '%s'  #	Status. For requests that got internally redirected, this is the status of the *original* request --- %>s for the last.
    '%t'  #	Time the request was received (standard english format)
    '%T'  #	The time taken to serve the request, in seconds.
    '%u'  #	Remote user (from auth; may be bogus if return status (%s) is 401)
    '%U'  #	The URL path requested, not including any query string.
    '%v'  #	The canonical ServerName of the server serving the request.
    '%V'  #	The server name according to the UseCanonicalName setting.
    '%X'  #	Connection status when response is completed:
              # X =	connection aborted before the response completed.
              # + =	connection may be kept alive after the response is sent.
              # - =	connection will be closed after the response is sent.
              # (This directive was %c in late versions of Apache 1.3, but this conflicted with the historical ssl %{var}c syntax.)
    '%I'  #	Bytes received, including request and headers, cannot be zero. You need to enable mod_logio to use this.
    '%O'  #	Bytes sent, including headers, cannot be zero. You need to enable mod_logio to use this.
    
    '%\{User-Agent\}i'  # Special case of below, for matching just user agent
    '%\{[^\}]+?\}i'  #	The contents of Foobar: header line(s) in the request sent to the server. Changes made by other modules (e.g. mod_headers) affect this. If you're interested in what the request header was prior to when most modules would have modified it, use mod_setenvif to copy the header into an internal environment variable and log that value with the %\{VARNAME}e described above.
    
    '%\{[^\}]+?\}C'  #	The contents of cookie Foobar in the request sent to the server. Only version 0 cookies are fully supported.
    '%\{[^\}]+?\}e'  #	The contents of the environment variable FOOBAR
    '%\{[^\}]+?\}n'  #	The contents of note Foobar from another module.
    '%\{[^\}]+?\}o'  #	The contents of Foobar: header line(s) in the reply.
    '%\{[^\}]+?\}p'  #	The canonical port of the server serving the request or the server's actual port or the client's actual port. Valid formats are canonical, local, or remote.
    '%\{[^\}]+?\}P'  #	The process ID or thread id of the child that serviced the request. Valid formats are pid, tid, and hextid. hextid requires APR 1.2.0 or higher.
    '%\{[^\}]+?\}t'  #	The time, in the form given by format, which should be in strftime(3) format. (potentially localized)
    '%\{[^\}]+?\}x'  # Extension value, e.g. mod_ssl protocol and cipher
```

Copyright
=========

This package is © 2013-2015 Rory McCann, released under the terms of the GNU GPL v3 (or at your option a later version). If you'd like a different licence, please email <rory@technomancy.org>


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/rory/apache-log-parser/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

