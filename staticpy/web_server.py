import SimpleHTTPServer
import SocketServer
import socket
import os
import threading

class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    '''A basic request TestHandler

        Two unique rules:
            routes '/' -> index.html
            rounts '/path/to/page' -> /path/to/page.html'

        This disables logging

    '''
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        elif os.path.isfile('%s.html' % self.path.strip('\\/') ):
            self.path = '%s.html' % self.path
        
        return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(*args):
        return

class TestServer(SocketServer.TCPServer):
    '''A reusable test server

        Since this server may be stopped and restarted a lot
        we don't want to run into the "address already in use" error
        this resolves those problems
    '''
    allow_reuse_address = True


class Server(threading.Thread):
    def __init__(self, site_path, host = None, port = 8080):
        '''A single threaded SimpleHTTPServer

            This creates a daemon thread that sits and listens for web requests
            the thread stays alive untill the parent thread dies.

            By default we listen at localhost:8080
        '''
        if host is None:
            self.host = socket.gethostbyname(socket.gethostname())
        else:
            self.host = host
        self.port = port
        self.site_path = site_path
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        '''Start the server

            Starts the server this function blocks this thread until
            the parent thread dies clossing this thread.
        '''
        os.chdir(self.site_path)
        self.server = TestServer(('', self.port), TestHandler)
        print "Serving webpage at: %s:%d" % (self.host, self.port)
        self.server.serve_forever()
