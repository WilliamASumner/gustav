from __future__ import with_statement
import re 
import sys
from ajax import process_ajax

html_dir = "./"
nafc_lib = "/var/www/wsgi/"
if nafc_lib not in sys.path:
    sys.path.insert(0,nafc_lib)

def home_handler(environ,response_fn,interface):
    status='200 OK'
    try:
        f = open(html_dir+"index.html","r")
        output = f.read().encode()

    except:
        status = "500 Internal Server Error"
        output = b"<h1>500 Internal Server Error</h1><h2>Error getting index.html</h2>"

    response_fn(status,[('Content-Type','text/html')])
    return [output]

def nafc_handler(environ,response_fn,interface):
    if environ['REQUEST_METHOD'] == 'GET': # requests a resource
        return get_resource(environ['PATH_INFO'],response_fn,interface)

    elif environ['REQUEST_METHOD'] == 'POST':  # a message to gustav
        data_str = get_content(environ)
        output, hadError = process_ajax(interface,data_str)
        output = output.encode()
        status = '200 OK'

        if hadError:
            status = '500 Internal Server Error'

        response_fn(status,[('Content-Type','application/json')])
        return [output]

def get_resource(path,response_fn,interface):
    if re.match("^[/(nafc) ]?$",path) or re.match("/index.html$",path):
        status='200 OK'
        response_fn(status,[('Content-Type','text/html')])
        output = interface.generate_html().encode()
        return [output]

    elif re.match("^/nafc/css/styles.css$",path):
        status='200 OK'
        response_fn(status,[('Content-Type','text/css')])
        output = interface.generate_css().encode()
        return [output]

    elif re.match("/nafc/js/.*\.js$",path):
        status='200 OK'
        response_fn(status,[('Content-Type','application/javascript')])
        js_file = re.match("/nafc/js/(.*)\.js",path).group(1)

        if js_file in ["button", "key", "main", "i_event"]:
            output = interface.generate_js(js_file).encode()

        else:
            print("Failed to find javascript file: '" + js_file)
            output = "".encode()

        return [output]

    else:
        response_fn('404 Not Found',[('Content-Type','text/html')])
        print("Failed to find resource: " + str(path))
        return [b'<html><body><h1>404 Not Found</h1></body></html>']

def get_content(environ):
    data_str = None
    if environ['CONTENT_LENGTH'] is not None and int(environ['CONTENT_LENGTH']) > 0:
            wsgi_input = environ['wsgi.input']
            data_str = wsgi_input.read(int(environ['CONTENT_LENGTH']))

    return data_str.decode('utf-8')

default_routes = {
        re.compile('^[ /]?$'):nafc_handler,
        re.compile('^/nafc(/[a-z]*)*(.*\..*)*$'):nafc_handler, # /nafc/*
        }

class Application(object):
    def __init__(self,routes=default_routes,interface=None):
        self.routes = routes
        self.count = 0
        self.interface = interface

    def not_found(self,environ,response_fn,interface):
        print("No matching handler for: " + str(environ.get('PATH_INFO')))
        response_fn('404 Not Found',[('Content-Type','text/html')])
        return [b'<html><body><h1>404 Not Found</h1></body></html>']

    def __call__(self,environ,response_fn):
        handler = self.not_found
        for key in self.routes:
            if key.match(environ.get('PATH_INFO')):
                handler = self.routes[key]

        return handler(environ,response_fn,self.interface)

application = Application()
