import os, sys
import threading
import webbrowser

from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

from application import application

class LocalServer:
    def __init__(self, interface):
        self.interface = interface
        self.port = 8003
        self.server = None
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
                self.server = make_server('',self.port,application)
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

if __name__ == "__main__":
    server = LocalServer(None).start()
    while True:
        pass
