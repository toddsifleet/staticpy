import socket
import threading
import hashlib
import base64
from struct import pack

#this is used to automatically refresh the page when we are developing
#it really speeds up the iteration cycles.  It is inject to a template.
client_js_code = '''
    <script type="text/javascript"> 
        window.onload = function() {
            var s = new WebSocket("ws://%s:%s/");
            s.onopen = function(e) { document.title = 'MONITORING'; };
            s.onclose = function(e) { document.title = 'NO MONITORING';  };
            s.onmessage = function(e) {document.location.reload(true); };
        };
    </script>
'''
def frame_message(message):
    '''Frame a message for transmission

        For a message to be sent across the socket it must be for formatted
        in the form <opcode><length><message>.

        This function takes care of that.

        params: message string
        return: framed message string
    '''
    length = len(message)
    if length > 0xffff:
        length = "\x7f%s" % pack(">Q", length)
    elif length > 0x7d:
        length = "\x7e%s" % pack(">H", length)
    else:
        length = chr(len(message))

    return "%s%s%s" % (chr(0x81), length, message)
    

def parse_key(request):
    '''Parse the websocket key out of a connection request

        When opening a new websocket connection the client will send
        a message containing a Sec-WebSocket-Key, here we parse out 
        and return the value

        params: connection request string
        returns: Sec-WebSocket-Key string
    '''
    key = None
    for line in request.split('\r\n'):
        if line.startswith('Sec-WebSocket-Key:'):
            key = line.split(':')[1].strip()

    if not key:
        raise Exception("Could not parse request!")

    return key



def get_response_key(key):
    '''Generate unique Sec-WebSocket-Accept key

        To open a WebSocket connection we must respond with the correct
        Sec-WebSocket-Accept key.  This value is generated by concatenating 
        the request key to the salt hashing it and then encoding it to base64.

        input: Sec-WebSocket-Key string
        output: Sec-WebSocket-Accept string
    '''
    salt = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    response_key =  hashlib.sha1("%s%s" % (key, salt)).digest()
    return response_key.encode("base64").strip()

def generate_response(key):
    '''Generate connection accept response

        Generates the required response to open a WebSocket connection
        with the client.

        params: Sec-WebSocket-Key
        return: response message
    '''
    response_key = get_response_key(key)
    response = [
        'HTTP/1.1 101 Web Socket Protocol Handshake',
        'Connection:Upgrade',
        'Sec-WebSocket-Accept: %s' % response_key,
        'Upgrade:WebSocket'
        ]

    return '\r\n'.join(response) + '\r\n\r\n'

class WebSocket(object):
    ''' WebSocket server worker

        This class operates as a one way server "worker" on creation
        we read the connection request of the supplied socket and issue
        the correct response to start the connection.

        Once the object has been created it can be used to send messages
        to the client, however it cannot receive anything.

        Note: This does not handle the older style of websocket that uses key-1 and
        key-2.  I have only tested this on: iOS 6 (iphone/ipad), Chrome 24, Safari 6 and
        Firefox 18; so your mileage may vary.
        
        params: 
            sock: a connected socket 
    '''
    def __init__(self, sock):
        self.sock = sock
        self.connect()

    def connect(self):
        '''Connect to a WebSocket client

            This function does everything necessary to negotiate a 
            connection with a new WebSocket client.

            params: None
        '''
        request = self.sock.recv(4096)
        self.key = parse_key(request)
        response = generate_response(self.key)
        self.sock.send(response)

    def send(self, message):
        '''Send a message

            Send a message to the connected client.

            params: message
            return:
                1 on success
                0 on failure
        '''
        try:
            self.sock.send(frame_message(message))
            return True
        except:
            print 'error writing'
            return False

    def close(self):
        self.sock.close()

    def __delete__(self):
        self.close()

class WebSocketServer(threading.Thread):
    '''A simple threaded WebSocketServer

        A very simple websocket server, once initialized we bind the socket
        and sit and wait for a connection.  When a new client tries to connect
        we create a WebSocket object and accept the connection.  The newly created
        WebSocket is placed on the queue expecting the parent process to handle it.
    '''
    def __init__(self, queue, host = None, port = 8888):
        '''WebSocketServer initializer

            params:
                queue: the Queue.Queue() to place the connections on
                host: the host to connect if not set:
                    socket.gethostbyname(socket.gethostname())
                port: the port to try to connect on.  If this fails
                    we will try to bind to 10 higher ports until we are successful.
            returns:
                nothing
        '''
        self.queue = queue

        if host is None:
            host = socket.gethostbyname(socket.gethostname())

        threading.Thread.__init__(self)
        self.daemon = True
        self.host = host
        self.port = port
        self.sock = self.bind()
        #this is the client code
        self.client_js_code = client_js_code % (self.host, '1234')

    def run(self):
        '''Run server

            Start Listen on the specified socket.  When a new connection
            is made we accept it and place it on the queue, and start waiting again

            The thread can be stopped by turning off self.running.

            params: nothing
            return: nothing
        '''
        self.running = True
        self.sock.listen(1)
        while self.running:
            t,_ = self.sock.accept();
            self.queue.put(WebSocket(t))

    def bind(self):
        '''Bind to a socket

            Tries to bind to the specified host on the specified port.  If we fails
            to bind the socket we try the next 10 ports in order.  If all 10 ports fails
            we raise an exception.

            params: nothings
            returns: 
                success: a socket connection
                failure: raises exception
        '''
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        for i in range(10):
            try:
                sock.bind((self.host, self.port))
                print 'Listening at %s:%s' % (self.host, self.port)
                return sock

            except Exception as e:
                print 'Error Binding to port %s:\n%s' % (self.port, e)
                self.port += 1
                print 'Trying to bind to port %s' % self.port

        raise Exception('Unable to bind %s' % self.host)