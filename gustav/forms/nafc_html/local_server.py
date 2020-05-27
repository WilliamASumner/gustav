import os, sys
import re
import threading
import webbrowser
from ajax import process_ajax

import 

if sys.version_info[0] == 2:
    import SocketServer as sserver
    import SimpleHTTPServer as server_lib
else:
    import socketserver as sserver
    import http.server as server_lib

SockError = sserver.socket.error

# Adapted from https://gist.github.com/bradmontgomery/2219997
class CustomRequestHandler(server_lib.SimpleHTTPRequestHandler):
    interface = None
    logging = False

    def connect_interface(self,InterfaceInstance):
        self.interface = InterfaceInstance

    # https://stackoverflow.com/questions/25360798/save-logs-simplehttpserver
    def log_message(self, format, *args):
        """
        Method for writing out errors/log messages
        """
        if self.logging:
            log_file = open('logfile.txt', 'a', 1) # output not needed
            log_file.write(
                "%s - - [%s] %s\n" % (self.client_address[0],
                    self.log_date_time_string(),
                    format%args))

    def set_response_headers(self,kind):
        self.send_response(200)
        self.send_header("Content-type",kind)
        self.end_headers()

    def set_ajax_headers(self):
        self.send_response(200)
        self.send_header("Content-type","application/json")
        self.end_headers()

    def process_json(self,data_string):
        return process_ajax(self.interface,data_string)

    def do_GET(self):
        """
        Responds to all HTTP GET requests for things like html, css, js
        """

        if re.match("^/$",self.path) or re.match("/index.html",self.path):
            self.set_response_headers("text/html")
            self.wfile.write(self.interface.generate_html())

        elif re.match(".*css",self.path):
            self.set_response_headers("text/css")
            self.wfile.write(self.interface.generate_css())

        elif re.match(".*js",self.path):
            self.set_response_headers("application/javascript")
            self.wfile.write(self.interface.generate_js())

    def do_POST(self):
        """
        Responds to all HTTP POST requests that send data here
        """

        length = int(self.headers['Content-Length'])
        data_string = self.rfile.read(length).decode('UTF-8')
        response_str = self.process_json(data_string)
        self.set_ajax_headers();

        self.wfile.write(bytearray(response_str,'UTF-8'))

class CustomTCPServer(sserver.TCPServer,object):
    def __init__(self,server_address,RequestHandler,InterfaceInstance,logging=False):
        RequestHandler.interface = InterfaceInstance
        RequestHandler.logging = logging
        super(CustomTCPServer,self).__init__(server_address,RequestHandler)

class LocalServer:
    def __init__(self, app):
        self.interface = app.interface
        self.port = 8000
        self.server_thread = threading.Thread(target=self.start_server_thread) # start server in background

    def start_server_thread(self):
            print("Serving on port",self.port)
            try:
                self.server.serve_forever()

            except Exception as e:
                print("Unexpected error on server:" + str(e))
                self.server.server_close()
                sys.exit(1) # Don't continue on an error

    def start(self, openBrowser=True):
        while True:
            try:
                self.server = CustomTCPServer(("",self.port),CustomRequestHandler,self.interface)
                break
            except (OSError,SockError):
                self.port += 1 # port in use
            except Exception as e:
                raise Exception("Error starting up server: " + str(e))

        if openBrowser:
            self.browser = webbrowser.get() # get befault browser
            self.browser.open("http://localhost:" + str(self.port))
        self.server_thread.setDaemon(True)
        self.server_thread.start()







