import re
from datetime import datetime, tzinfo, timedelta

import user_agents

class ApacheLogParserException(Exception): pass

class LineDoesntMatchException(ApacheLogParserException):
    def __init__(self, log_line=None, regex=None, *args, **kwargs):
        self.log_line = log_line
        self.regex = regex

    def __repr__(self):
        return u"LineDoesntMatchException(log_line={0!r}, regex={1!r})".format(self.log_line, self.regex)

    __str__ = __repr__

def extract_inner_value(output_prefix, input_suffix):
    """
    Given an input format like %{Referer}o return a function that will extract that 'Referer' from a match
    """
    regex = re.compile("^%\{([^\}]+?)\}"+input_suffix+"$")
    def matcher(matched_string):
        match = regex.match(matched_string)
        inner_value = match.groups()[0]
        inner_value = inner_value.strip().lower().replace("-", "_")
        return output_prefix+inner_value
    return matcher

def make_regex(format_template):
    """
    Turn a format_template from %s into something like %[<>]?s
    """
    # FIXME support the return code format
    percent, rest = format_template[0], format_template[1:]
    return percent+"[<>]?"+rest

def extra_request_from_first_line(matched_strings):
    first_line = matched_strings['request_first_line']
    match = re.match("^(?P<method>GET|HEAD|POST|OPTIONS|PUT|CONNECT|PATCH|PROPFIND|DELETE)\s?(?P<url>.{,10000}?)(\s+HTTP/(?P<http_ver>1.[01]))?$", first_line)
    if match is None:
        # Possibly garbage, ignore it
        results = { 'request_first_line': first_line, 'request_method': '', 'request_url': '', 'request_http_ver': ''}
    else:
        results = { 'request_first_line': first_line, 'request_method': match.groupdict()['method'], 'request_url': match.groupdict()['url'], 'request_http_ver': match.groupdict()['http_ver']}
    return results

def parse_user_agent(matched_strings):
    ua = matched_strings['request_header_user_agent']
    parsed_ua = user_agents.parse(ua)
    matched_strings.update({
        'request_header_user_agent__browser__family': parsed_ua.browser.family,
        'request_header_user_agent__browser__version_string': parsed_ua.browser.version_string,
        'request_header_user_agent__os__family': parsed_ua.os.family,
        'request_header_user_agent__os__version_string': parsed_ua.os.version_string,
        'request_header_user_agent__is_mobile': parsed_ua.is_mobile,
    })

    return matched_strings

class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, string):
        #import pudb ; pudb.set_trace()
        if string[0] == '-':
            direction = -1
            string = string[1:]
        elif string[0] == '+':
            direction = +1
            string = string[1:]
        else:
            direction = +1
            string = string

        hr_offset = int(string[0:2], 10)
        min_offset = int(string[2:3], 10)
        min_offset = hr_offset * 60 + min_offset
        min_offset = direction * min_offset

        self.__offset = timedelta(minutes = min_offset)

        self.__name = string

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta(0)

    def __repr__(self):
        return repr(self.__name)


def apachetime(s):
    """
    Given a string representation of a datetime in apache format (e.g.
    "01/Sep/2012:06:05:11 +0000"), return the python datetime for that string, with timezone
    """
    month_map = {'Jan': 1, 'Feb': 2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7,
        'Aug':8,  'Sep': 9, 'Oct':10, 'Nov': 11, 'Dec': 12}
    s = s[1:-1]

    tz_string = s[21:26]
    tz = FixedOffset(tz_string)

    obj = datetime(year=int(s[7:11]), month=month_map[s[3:6]], day=int(s[0:2]),
                hour=int(s[12:14]), minute=int(s[15:17]), second=int(s[18:20]),
                tzinfo=tz )

    return obj

def format_time(matched_strings):

    time_received = matched_strings['time_received']

    # Parse it to a timezone string
    obj = apachetime(time_received)
    
    # For backwards compatibility, time_received_datetimeobj is a naive
    # datetime, so we have to create a timezone less version
    naive_obj = obj.replace(tzinfo=None)

    utc = FixedOffset('0000')
    utc_obj = obj.astimezone(utc)

    return {
        'time_received':time_received,
        'time_received_datetimeobj': naive_obj, 'time_received_isoformat': naive_obj.isoformat(),
        'time_received_tz_datetimeobj': obj, 'time_received_tz_isoformat': obj.isoformat(),
        'time_received_utc_datetimeobj': utc_obj, 'time_received_utc_isoformat': utc_obj.isoformat(),
    }

IPv4_ADDR_REGEX = '(?:\d{1,3}\.){3}\d{1,3}'
IPv6_ADDR_REGEX = "([0-9A-Fa-f]{0,4}:){2,7}([0-9A-Fa-f]{0,4})"
IP_ADDR_REGEX = "("+IPv4_ADDR_REGEX+"|"+IPv6_ADDR_REGEX+")"

FORMAT_STRINGS = [
    ['%%', '%', lambda match: '', lambda matched_strings: matched_strings],
    [make_regex('%a'), IP_ADDR_REGEX, lambda match: 'remote_ip', lambda matched_strings: matched_strings], #	Remote IP-address
    [make_regex('%A'), IP_ADDR_REGEX, lambda match: 'local_ip', lambda matched_strings: matched_strings], #	Local IP-address
    [make_regex('%B'), '(\d+|-)', lambda match: 'response_bytes', lambda matched_strings: matched_strings], #	Size of response in bytes, excluding HTTP headers.
    [make_regex('%b'), '(\d+|-)', lambda match: 'response_bytes_clf', lambda matched_strings: matched_strings], #	Size of response in bytes, excluding HTTP headers. In CLF format, i.e. a '-' rather than a 0 when no bytes are sent.
    [make_regex('%\{[^\}]+?\}C'), '.*?', extract_inner_value("cookie_", "C") , lambda matched_strings: matched_strings], #	The contents of cookie Foobar in the request sent to the server. Only version 0 cookies are fully supported.
    [make_regex('%D'), '-?\d+', lambda match: 'time_us', lambda matched_strings: matched_strings], #	The time taken to serve the request, in microseconds.
    [make_regex('%\{[^\}]+?\}e'), '.*?', extract_inner_value("env_", "e"), lambda matched_strings: matched_strings], #	The contents of the environment variable FOOBAR
    [make_regex('%f'), '.*?', lambda match: 'filename', lambda matched_strings: matched_strings], #	Filename
    [make_regex('%h'), '.*?', lambda match: 'remote_host', lambda matched_strings: matched_strings], #	Remote host
    [make_regex('%H'), '.*?', lambda match: 'protocol', lambda matched_strings: matched_strings], #	The request protocol

    # Special case of below, for matching just user agent
    [make_regex('%\{User-Agent\}i'), '.*?', lambda match: "request_header_user_agent" , parse_user_agent],
    [make_regex('%\{[^\}]+?\}i'), '.*?', extract_inner_value("request_header_", "i") , lambda matched_strings: matched_strings], #	The contents of Foobar: header line(s) in the request sent to the server. Changes made by other modules (e.g. mod_headers) affect this. If you're interested in what the request header was prior to when most modules would have modified it, use mod_setenvif to copy the header into an internal environment variable and log that value with the %\{VARNAME}e described above.

    [make_regex('%k'), '.*?', lambda match: 'num_keepalives', lambda matched_strings: matched_strings], #	Number of keepalive requests handled on this connection. Interesting if KeepAlive is being used, so that, for example, a '1' means the first keepalive request after the initial one, '2' the second, etc...; otherwise this is always 0 (indicating the initial request). Available in versions 2.2.11 and later.
    [make_regex('%l'), '.*?', lambda match: 'remote_logname', lambda matched_strings: matched_strings], #	Remote logname (from identd, if supplied). This will return a dash unless mod_ident is present and IdentityCheck is set On.
    [make_regex('%m'), '.*?', lambda match: 'method', lambda matched_strings: matched_strings], #	The request method
    [make_regex('%\{[^\}]+?\}n'), '.*?', extract_inner_value("note_", "n") , lambda matched_strings: matched_strings], #	The contents of note Foobar from another module.
    [make_regex('%\{[^\}]+?\}o'), '.*?',extract_inner_value("response_header_", "o") , lambda matched_strings: matched_strings], #	The contents of Foobar: header line(s) in the reply.
    [make_regex('%p'), '.*?', lambda match: 'server_port', lambda matched_strings: matched_strings], #	The canonical port of the server serving the request
    [make_regex('%\{[^\}]+?\}p'), '.*?', extract_inner_value("server_port_", "p") , lambda matched_strings: matched_strings], #	The canonical port of the server serving the request or the server's actual port or the client's actual port. Valid formats are canonical, local, or remote.
    [make_regex('%P'), '.*?', lambda match: 'pid', lambda matched_strings: matched_strings], #	The process ID of the child that serviced the request.
    [make_regex('%\{[^\}]+?\}P'), '.*?', extract_inner_value("pid_", "P") , lambda matched_strings: matched_strings], #	The process ID or thread id of the child that serviced the request. Valid formats are pid, tid, and hextid. hextid requires APR 1.2.0 or higher.
    [make_regex('%q'), '.*?', lambda match: 'query_string' , lambda matched_strings: matched_strings], #	The query string (prepended with a ? if a query string exists, otherwise an empty string)
    [make_regex('%r'), '.*?', lambda match: 'request_first_line', extra_request_from_first_line], #	First line of request
    [make_regex('%R'), '.*?', lambda match: 'handler', lambda matched_strings: matched_strings], #	The handler generating the response (if any).
    [make_regex('%s'), '([0-9]+?|-)', lambda match: 'status', lambda matched_strings: matched_strings], #	Status. For requests that got internally redirected, this is the status of the *original* request --- %>s for the last.
    [make_regex('%t'), '\[.*?\]', lambda match: 'time_received', format_time], #	Time the request was received (standard english format)
    [make_regex('%\{[^\}]+?\}t'), '.*?', extract_inner_value("time_", "t") , lambda matched_strings: matched_strings], #	The time, in the form given by format, which should be in strftime(3) format. (potentially localized)
    [make_regex('%\{[^\}]+?\}x'), '.*?', extract_inner_value("extension_", "x") , lambda matched_strings: matched_strings], # Extension value, e.g. mod_ssl protocol and cipher
    [make_regex('%T'), '.*?', lambda match: 'time_s', lambda matched_strings: matched_strings], #	The time taken to serve the request, in seconds.
    [make_regex('%u'), '.*?', lambda match: 'remote_user', lambda matched_strings: matched_strings], #	Remote user (from auth; may be bogus if return status (%s) is 401)
    [make_regex('%U'), '.*?', lambda match: 'url_path' , lambda matched_strings: matched_strings], #	The URL path requested, not including any query string.
    [make_regex('%v'), '.*?', lambda match: 'server_name', lambda matched_strings: matched_strings], #	The canonical ServerName of the server serving the request.
    [make_regex('%V'), '.*?', lambda match: 'server_name2', lambda matched_strings: matched_strings], #	The server name according to the UseCanonicalName setting.
    [make_regex('%X'), '.*?', lambda match: 'conn_status', lambda matched_strings: matched_strings], #	Connection status when response is completed:
        # X =	connection aborted before the response completed.
        # + =	connection may be kept alive after the response is sent.
        # - =	connection will be closed after the response is sent.
        # (This directive was %c in late versions of Apache 1.3, but this conflicted with the historical ssl %{var}c syntax.)
    [make_regex('%I'), '.*?', lambda match: 'bytes_rx', lambda matched_strings: matched_strings], #	Bytes received, including request and headers, cannot be zero. You need to enable mod_logio to use this.
    [make_regex('%O'), '.*?', lambda match: 'bytes_tx', lambda matched_strings: matched_strings], #	Bytes sent, including headers, cannot be zero. You need to enable mod_logio to use this.
]

class Parser:
    def __init__(self, format_string):
        self.names = []

        self.pattern = "("+"|".join(x[0] for x in FORMAT_STRINGS)+")"
        self.parts = re.split(self.pattern, format_string)

        self.functions_to_parse = {}

        self.log_line_regex = ""
        while True:
            if len(self.parts) == 0:
                break
            if len(self.parts) == 1:
                raw, regex = self.parts.pop(0), None
            elif len(self.parts) >= 2:
                raw, regex = self.parts.pop(0), self.parts.pop(0)
            if len(raw) > 0:
                self.log_line_regex += re.escape(raw)
            if regex is not None:
                for format_spec in FORMAT_STRINGS:
                    pattern_regex, log_part_regex, name_func, values_func = format_spec
                    match = re.match("^"+pattern_regex+"$", regex)
                    if match:
                        name = name_func(match.group())
                        self.names.append(name)
                        self.functions_to_parse[name] = values_func
                        self.log_line_regex += "(?P<"+name+">"+log_part_regex+")"
                        break

        self._log_line_regex_raw = self.log_line_regex
        self.log_line_regex = re.compile(self.log_line_regex)
        self.names = tuple(self.names)

    def parse(self, log_line):
        match = self.log_line_regex.match(log_line)
        if match is None:
            raise LineDoesntMatchException(log_line=log_line, regex=self.log_line_regex.pattern)
        else:
            results = {}
            for name in self.functions_to_parse:
                values = {name: match.groupdict()[name]}
                values = self.functions_to_parse[name](values)
                results.update(values)
            return results


def make_parser(format_string):
    return Parser(format_string).parse

def get_fieldnames(format_string):
    return Parser(format_string).names
