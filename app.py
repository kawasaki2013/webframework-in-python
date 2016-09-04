import cgi
import re
from collections import namedtuple


Route = namedtuple('Route', ['method', 'path', 'callback'])


def http404(request, start_response):
    start_response('404 Not Found', [('Content-type', 'text/plain; charset=utf-8')])
    return [b'404 Not Found']


class Router:
    def __init__(self):
        self.routes = []

    def add(self, method, path, callback):
        route = Route(method=method, path=path, callback=callback)
        self.routes.append(route)

    def match(self, environ):
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO'] or '/'

        for r in filter(lambda x: x.method == method.upper(), self.routes):
            matched = re.compile(r.path).match(path)
            if matched:
                kwargs = matched.groupdict()
                return r.callback, kwargs
        return http404, {}


class Request:
    def __init__(self, environ):
        self.environ = environ
        self._body = None

    @property
    def forms(self):
        form = cgi.FieldStorage(
            fp=self.environ['wsgi.input'],
            environ=self.environ,
            keep_blank_values=True,
        )
        params = {k: form[k].value for k in form}
        return params

    @property
    def args(self):
        params = cgi.FieldStorage(
            environ=self.environ,
            keep_blank_values=True,
        )
        p = {k: params[k].value for k in params}
        return p

    @property
    def body(self) -> str:
        if self._body is None:
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            self._body = self.environ['wsgi.input'].read(content_length).decode('utf-8')
        return self._body


class App:
    def __init__(self):
        self.router = Router()

    def route(self, path=None, method='GET', callback=None):
        def decorator(callback_func):
            self.router.add(method, path, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def __call__(self, env, start_response):
        callback, kwargs = self.router.match(env)
        request = Request(env)
        return callback(request, start_response, **kwargs)
