import os

from werkzeug.wrappers import Request, Response
from werkzeug.middleware.shared_data import SharedDataMiddleware
from jinja2 import Environment, FileSystemLoader
from werkzeug.routing import Rule, Map
from werkzeug.utils import redirect
from werkzeug.exceptions import HTTPException, NotFound
from redis import StrictRedis


class BlogApp(object):
    """Implements a WSGI application for managing your posts."""

    def __init__(self, config):
        """Initializes the Jinja templating engine to render from the 'templates' folder, defines the mapping of URLs to view methods, and initializes the Redis interface."""
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)

        self.url_map = Map([
            Rule('/', endpoint='index'),
            Rule('/register', endpoint='register', methods=['POST', 'GET']),
            Rule('/login', endpoint='login', methods=['POST', 'GET']),
            Rule('/create', endpoint='add_post', methods=['GET', 'POST']),
            Rule('/posts', endpoint='posts', methods=['GET'])
        ])
        self.redis = StrictRedis(config['redis_host'], config['redis_port'], decode_responses=True)

    def render_template(self, template_name, **context):
        """Renders the specified template file using the Jinja templating engine."""
        template = self.jinja_env.get_template(template_name)
        return Response(template.render(context), mimetype='text/html')

    def index(self, request):
        return self.render_template('home.html')

    def posts(self, request):
        """Displays a list of the user's post"""
        posts = self.redis.lrange('posts', 0, -1)
        return self.render_template('posts.html', posts=posts)

    @
    def register(self, request):
        if request.method == 'POST':
            return self.render_template('register.html')
        username = request.form['username']
        password = request.form['password']
        user_id = self.redis.incrby('next_user_id', 1000)
        self.redis.hmset('user:' + user_id, dict(username=username, password=password))
        session['username'] = username
        return self.render_template('home.html')

    def login(self, request):
        return self.render_template('login.html')

    def add_post(self, request):
        """Adds a post to the posts page"""
        if request.method == 'POST':
            post_title = request.form['title']
            post_body = request.form['post_body']
            # full_post = [post_title, post_body]
            # full_post.unshift('queue')
            self.redis.rpush('posts', post_title)
            # self.redis.rpush(post_title, post_body)
            self.redis.rpush('posts', post_body)
            return redirect('/posts')
        return self.render_template('add_post.html')

    def error_404(self):
        response = self.render_template("404.html")
        response.status_code = 404
        return response

    def dispatch_request(self, request):
        """Dispatches the request."""
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, endpoint)(request, **values)
        # except NotFound:
        #     return self.error_4o4()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        """WSGI application that processes requests and returns responses."""
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """The WSGI server calls this method as the WSGI application."""
        return self.wsgi_app(environ, start_response)


def create_app():
    """Application factory function that returns an instance of an BlogApp."""
    app = BlogApp({'redis_host': 'localhost', 'redis_port': 6379})
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/static': os.path.join(os.path.dirname(__file__), 'static')
    })
    return app


if __name__ == '__main__':
    # Run the Werkzeug development server to serve the WSGI application (App)
    from werkzeug.serving import run_simple

    app = create_app()
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)
