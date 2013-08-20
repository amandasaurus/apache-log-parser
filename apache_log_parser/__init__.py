import re

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

FORMAT_STRINGS = [
    ['%%', '%', lambda match: ''],
    [make_regex('%a'), '\d{,3}(.\d{\3}){3}', lambda match: 'remote_ip'], #	Remote IP-address
    [make_regex('%A'), '\d{,3}(.\d{\3}){3}', lambda match: 'local_ip'], #	Local IP-address
    [make_regex('%B'), '\d+', lambda match: 'response_bytes'], #	Size of response in bytes, excluding HTTP headers.
    [make_regex('%b'), '\d+', lambda match: 'response_bytes_clf'], #	Size of response in bytes, excluding HTTP headers. In CLF format, i.e. a '-' rather than a 0 when no bytes are sent.
    [make_regex('%\{[^\]]+?\}C'), '.*?', extract_inner_value("cookie_", "C") ], #	The contents of cookie Foobar in the request sent to the server. Only version 0 cookies are fully supported.
    [make_regex('%D'), '\d+', lambda match: 'time_us'], #	The time taken to serve the request, in microseconds.
    [make_regex('%\{[^\}]+?\}e'), '.*?', 'env'], #	The contents of the environment variable FOOBAR
    [make_regex('%f'), '.*?', lambda match: 'filename'], #	Filename
    [make_regex('%h'), '.*?', lambda match: 'remote_host'], #	Remote host
    [make_regex('%H'), '.*?', lambda match: 'protocol'], #	The request protocol
    [make_regex('%\{[^\]]+?\}i'), '.*?', extract_inner_value("request_header_", "i") ], #	The contents of Foobar: header line(s) in the request sent to the server. Changes made by other modules (e.g. mod_headers) affect this. If you're interested in what the request header was prior to when most modules would have modified it, use mod_setenvif to copy the header into an internal environment variable and log that value with the %\{VARNAME}e described above.
    [make_regex('%k'), '.*?', lambda match: 'num_keepalives'], #	Number of keepalive requests handled on this connection. Interesting if KeepAlive is being used, so that, for example, a '1' means the first keepalive request after the initial one, '2' the second, etc...; otherwise this is always 0 (indicating the initial request). Available in versions 2.2.11 and later.
    [make_regex('%l'), '.*?', lambda match: 'remote_logname'], #	Remote logname (from identd, if supplied). This will return a dash unless mod_ident is present and IdentityCheck is set On.
    [make_regex('%m'), '.*?', lambda match: 'method'], #	The request method
    [make_regex('%\{[^\]]+?\}n'), '.*?', extract_inner_value("note_", "n") ], #	The contents of note Foobar from another module.
    [make_regex('%\{[^\]]+?\}o'), '.*?',extract_inner_value("response_header_", "o") ], #	The contents of Foobar: header line(s) in the reply.
    [make_regex('%p'), '.*?', lambda match: 'server_port'], #	The canonical port of the server serving the request
    [make_regex('%\{[^\]]+?\}p'), '.*?', extract_inner_value("server_port_", "p") ], #	The canonical port of the server serving the request or the server's actual port or the client's actual port. Valid formats are canonical, local, or remote.
    [make_regex('%P'), '.*?', lambda match: 'pid'], #	The process ID of the child that serviced the request.
    [make_regex('%\{[^\]]+?\}P'), '.*?', extract_inner_value("pid_", "P") ], #	The process ID or thread id of the child that serviced the request. Valid formats are pid, tid, and hextid. hextid requires APR 1.2.0 or higher.
    [make_regex('%q'), '.*?', lambda match: 'query_string' ], #	The query string (prepended with a ? if a query string exists, otherwise an empty string)
    [make_regex('%r'), '.*?', lambda match: 'request_first_line'], #	First line of request
    [make_regex('%R'), '.*?', lambda match: 'handler'], #	The handler generating the response (if any).
    [make_regex('%s'), '.*?', lambda match: 'status'], #	Status. For requests that got internally redirected, this is the status of the *original* request --- %>s for the last.
    [make_regex('%t'), '.*?', lambda match: 'time_recieved'], #	Time the request was received (standard english format)
    [make_regex('%\{[^\]]+?\}t'), '.*?', extract_inner_value("time_", "t") ], #	The time, in the form given by format, which should be in strftime(3) format. (potentially localized)
    [make_regex('%T'), '.*?', lambda match: 'time_s'], #	The time taken to serve the request, in seconds.
    [make_regex('%u'), '.*?', lambda match: 'remote_user'], #	Remote user (from auth; may be bogus if return status (%s) is 401)
    [make_regex('%U'), '.*?', lambda match: 'url_path' ], #	The URL path requested, not including any query string.
    [make_regex('%v'), '.*?', lambda match: 'server_name'], #	The canonical ServerName of the server serving the request.
    [make_regex('%V'), '.*?', lambda match: 'server_name2'], #	The server name according to the UseCanonicalName setting.
    [make_regex('%X'), '.*?', lambda match: 'conn_status'], #	Connection status when response is completed:
        # X =	connection aborted before the response completed.
        # + =	connection may be kept alive after the response is sent.
        # - =	connection will be closed after the response is sent.
        # (This directive was %c in late versions of Apache 1.3, but this conflicted with the historical ssl %{var}c syntax.)
    [make_regex('%I'), '.*?', lambda match: 'bytes_rx'], #	Bytes received, including request and headers, cannot be zero. You need to enable mod_logio to use this.
    [make_regex('%O'), '.*?', lambda match: 'bytes_tx'], #	Bytes sent, including headers, cannot be zero. You need to enable mod_logio to use this.
]

def make_parser(format_string):
    pattern = "("+"|".join(x[0] for x in FORMAT_STRINGS)+")"
    parts = re.split(pattern, format_string)

    
    log_line_regex = ""
    while True:
        if len(parts) == 0:
            break
        if len(parts) == 1:
            raw, regex = parts.pop(0), None
        elif len(parts) >= 2:
            raw, regex = parts.pop(0), parts.pop(0)
        if len(raw) > 0:
            log_line_regex += re.escape(raw)
        if regex is not None:
            for format_spec in FORMAT_STRINGS:
                pattern_regex, log_part_regex, name_func = format_spec
                match = re.match("^"+pattern_regex+"$", regex)
                if match:
                    #import pudb ; pudb.set_trace()
                    name = name_func(match.group())
                    if len(match.groups()) > 0:
                        inner_name = match.groups()
                    log_line_regex += "(?P<"+name+">"+log_part_regex+")"
                    break

    log_line_regex = re.compile(log_line_regex)

    def matcher(log_line):
        match = log_line_regex.match(log_line)
        return match.groupdict()
        
    return matcher
    

