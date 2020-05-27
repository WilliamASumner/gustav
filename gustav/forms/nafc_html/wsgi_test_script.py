def home_handler(environ,response_fn):
    status='200 OK'
    output = b'<h1> This is the home page!</h1>'
    response_fn(status,[('Content-Type','text/html')])
    return [output]

def test_handler(environ,response_fn):
    status='200 OK'
    output = b'<h1> This is the test page!</h1>'
    response_fn(status,[('Content-Type','text/html')])
    return [output]

class Application(object):
    def __init__(self,routes):
        self.routes = routes

    def not_found(self,environ,response_fn):
        print("Failed to find path: " + str(environ.get('PATH_INFO')))
        response_fn('404 Not Found',[('Content-Type','text/plain')])
        return [b'404 Not Found']

    def __call__(self,environ,response_fn):
        handler = self.routes.get(environ.get('PATH_INFO')) or self.not_found
        return handler(environ,response_fn)

routes = {
        '':home_handler,
        ' ':home_handler,
        '/':home_handler,
        '/test': test_handler,
        }

application = Application(routes)

