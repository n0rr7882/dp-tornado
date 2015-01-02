# -*- coding: utf-8 -*-
#
#   dp for Tornado
#      YoungYong Park (youngyongpark@gmail.com)
#      2014.10.23
#


from engine.helper import Helper as dpHelper

try:
    import urllib.parse as _parse
except:
    import urllib as _parse

try:
    import urlparse
except:
    pass


class UrlParse(object):
    def __init__(self, request=None, scheme='', netloc='', path='', params=None, query='', framgment=''):
        if 'X-Proxy-Prefix' in request.headers:
            if path.startswith(request.headers['X-Proxy-Prefix']):
                path = path[(len(request.headers['X-Proxy-Prefix']) - 1):]

        self.request = request
        self.scheme = scheme
        self.netloc = netloc
        self.path = path
        self.params = params if params else {}
        self.query = query
        self.fragment = framgment

    def __str__(self):
        return ('scheme=%s, netloc=%s, path=%s, params=%s, query=%s, fragment=%s'
                % (self.scheme, self.netloc, self.path, self.params, self.query, self.fragment))


class UrlHelper(dpHelper):
    def quote(self, s):
        if self.helper.system.py_version <= 2:
            return _parse.quote_plus(s)
        else:
            return _parse.quote_plus(s)

    def build(self, url, params):
        if self.helper.system.py_version <= 2:
            return '%s?%s' % (url, _parse.urlencode(params))
        else:
            return '%s?%s' % (url, _parse.urlencode(params))

    def parse(self, request):
        if self.helper.system.py_version <= 2:
            p = urlparse.urlparse(request.uri)
            query = dict(urlparse.parse_qsl(p.query, keep_blank_values=True))
        else:
            p = _parse.urlparse(request.uri)
            query = dict(_parse.parse_qsl(p.query, keep_blank_values=True))

        return UrlParse(request, p.scheme, p.netloc, p.path, p.params, query, p.fragment)