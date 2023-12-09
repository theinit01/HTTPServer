"""
GET /index.html HTTP/1.1
Host: example.com
Connection: keep-alive
User-Agent: Mozilla/5.0
"""


import os
import socket
import mimetypes

class TCPServer:
    def __init__(self, host = '127.0.0.1',port =8888):
        self.host = host
        self.port = port

    def start(self):
        #create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)

        print("Listening at: ",s.getsockname())

        while True:
            conn, addr = s.accept()
            print("Connected by", addr)
            data = conn.recv(1024)

            response = self.handle_request(data)

            conn.sendall(response)
            conn.close()
    
    def handle_request(self,data):
        """Handles incoming data and returns a response.
        override this in httpsubclass"""

        return data

class HTTPServer(TCPServer):

    headers = {
        'Server': 'Crude Server',
        'Content-Type': 'text/html',
    }

    status_codes ={
        200: 'OK',
        404: 'Not Found',
        403: 'Access Forbidden',
        501: 'Not implemented',
    }


    def handle_request(self, data):
        #create an instance of HTTPRequest
        request = HTTPRequest(data)

        #look at the req method and call appropriate handler. eg. Get, POST etc.
        try:
            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = self.HTTP_501_handler
        
        response = handler(request)

        return response
    
    def serve_forbidden_page(self):
        response_line = self.response_line(status_code=403)
        response_headers = self.response_headers()
        blank_line = b"\r\n"
        response_body = b"<h1>403 Forbidden:</h1><hr><p>Access to this resource is restricted.</p>"

        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def HTTP_501_handler(self, request):    #handler for all the rest of the methods
        response_line = self.response_line(status_code=501)

        response_headers = self.response_headers()

        blank_line = b"\r\n"

        response_body = b"<h1>501 Not Implemented</h1>"

        return b"".join([response_line, response_headers, blank_line, response_body])
    
    def handle_GET(self, request):      #handler for GET
        filename = request.uri.strip('/')

        if filename == 'main.py':
            return self.serve_forbidden_page()
        
        if filename == '':
            filename = 'index.html'
        
        else:
            filename = request.uri.strip('/')
        if os.path.exists(filename):
            response_line = self.response_line(status_code=200)
            #find mime type of file requested ( can be different for images etc.CONTENT TYPE needs to be changed to render properly)
            # if nothing is found, send text/html
            content_type = mimetypes.guess_type(filename)[0] or 'text/html'

            extra_headers = {'Content-Type': content_type}
            response_headers = self.response_headers(extra_headers)

            with open(filename,'rb') as f:
                response_body = f.read()
        else:
            response_line = self.response_line(status_code=404)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1><p> Requested resource couldn't be found<p><hr>"

        blank_line = b"\r\n"

        return b"".join([response_line,response_headers,blank_line,response_body])

    def response_line(self, status_code):
        # returns response line
        reason = self.status_codes[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)

        return line.encode()

    def response_headers(self, extra_headers= None):
        # returns headers. The extra_headers can be a dict for sending extra headers if needed
        headers_copy = self.headers.copy()
        if extra_headers:
            headers_copy.update(extra_headers)
        
        headers = ""

        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])
        
        return headers.encode()

# need for parsing the request to see what page is requested in the request.
# for eg. GET /index.html HTTP/1.1
class HTTPRequest:
    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = "1.1" # default to HTTP/1.1 if request doesn't provide a version

        # call self.parse() to parse the request
        self.parse(data)
    
    def parse(self,data):
        lines = data.split(b"\r\n")

        request_line = lines[0]

        words = request_line.split(b" ")
        self.method = words[0].decode()

        if len(words) > 1: #sometimes index.html is not sent by browser for default homepage
            self.uri = words[1].decode()
        if len(words) > 2:
            self.http_version = words[2]


if __name__ == '__main__':
    server = HTTPServer()
    server.start()
