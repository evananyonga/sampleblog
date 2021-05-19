from werkzeug.wrappers import Request, Response


class App(object):
    """Implements a WSGI application for managing your posts."""

    def __init__(self):
        pass

    def dispatch_request(self, request):
        """Dispatches the request."""
        return Response('Hello World!')

    def wsgi_app(self, environ, start_response):
        """WSGI application that processes requests and returns responses."""
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """The WSGI server calls this method as the WSGI application."""
        return self.wsgi_app(environ, start_response)


def create_app():
    """Application factory function that returns an instance of an App."""
    app = App()
    return app


if __name__ == '__main__':
    # Run the Werkzeug development server to serve the WSGI application (App)
    from werkzeug.serving import run_simple

    app = create_app()
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)
