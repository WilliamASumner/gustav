import re 
from ajax import process_ajax
from nafc_html_remote import Interface

def home_handler(environ,response_fn,interface):
    status='200 OK'
    output = b'<h1> This is the home page!</h1>'
    response_fn(status,[('Content-Type','text/html')])
    return [output]

def nafc_handler(environ,response_fn,interface):
    if environ['REQUEST_METHOD'] == 'GET': # requests a resource
        return get_resource(environ['PATH_INFO'],response_fn,interface)

    elif environ['REQUEST_METHOD'] == 'POST':  # a message to gustav
        data_str = get_content(environ)
        response_str = process_ajax(interface,data_str)
        return [bytearray(response_str,'utf-8')]

def get_resource(path,response_fn,interface):
    print("Getting resource on path: " + "'" + str(path) + "'")
    if re.match("^/nafc$",path) or re.match("/index.html$",path):
        status='200 OK'
        response_fn(status,[('Content-Type','text/html')])
        return [interface.generate_html().encode()]

    elif re.match("^/nafc/css/styles.css$",path):
        status='200 OK'
        response_fn(status,[('Content-Type','text/css')])
        return [interface.generate_css().encode()]
    elif re.match("/nafc/js/main.js$",path):
        status='200 OK'
        response_fn(status,[('Content-Type','text/js')])
        return [interface.generate_js().encode()]

    else:
        response_fn('404 Not Found',[('Content-Type','text/html')])
        print("Failed to find resource: " + str(path))
        return [b'<html><body><h1>404 Not Found</h1></body></html>']

def get_content(environ):
    data_str = None
    if environ['CONTENT_LENGTH'] and environ['CONTENT_LENGTH'] > 0:
        data_str = wsgi.input.read(int(environ['CONTENT_LENGTH']))

    return data_str

routes = {
        re.compile('^[ /]?$'):home_handler,
        re.compile('^/nafc(/[a-z]*)*(.*\..*)*$'):nafc_handler, # /nafc/*
        }

class Application(object):
    def __init__(self,routes):
        self.routes = routes
        self.count = 0
        self.interface = Interface(alternatives=['A','B','C'])

    def not_found(self,environ,response_fn,interface):
        print("No matching handler for: " + str(environ.get('PATH_INFO')))
        response_fn('404 Not Found',[('Content-Type','text/html')])
        return [b'<html><body><h1>404 Not Found</h1></body></html>']

    def __call__(self,environ,response_fn):
        handler = self.not_found
        for key in routes:
            if key.match(environ.get('PATH_INFO')):
                handler = self.routes[key]

        return handler(environ,response_fn,self.interface)

application = Application(routes)
