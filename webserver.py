from datetime import datetime, timezone
from socket import *
from email.utils import parsedate_to_datetime
import os
import time

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
print("The server is ready to receive")


def create_http_response(status_code, content='', file_path=''):
    response = "HTTP/1.1 " + status_code + "\r\n"

    if os.path.exists(file_path):
        last_modified_time = os.path.getmtime(file_path)
        last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(last_modified_time))
        response += "Last-Modified: " + last_modified + "\r\n"

    if content:
        response += "Content-Length: " + str(len(content)) + "\r\n"
        response += "Content-Type: text/html\r\n"

    response += "\r\n"
    response += content
    return response


# Bad requests = Methods other than GET
def parse_request_header(request):
    headers = request.split("\r\n")
    if len(headers) > 0 and len(headers[0].split()) == 3:
        request_line = headers[0].split()
        method, filename = request_line[0], request_line[1]
        if method == "GET":
            filename = filename.strip("/")
            return filename
    return "bad_request"


def parse_modified_since(request):
    for line in request.split("\r\n"):
        if line.startswith("If-Modified-Since:"):
            return parsedate_to_datetime(line[len("If-Modified-Since:"):].strip())
    return None


def parse_content_length(request):
    for line in request.split("\r\n"):
        if line.lower().startswith("content-length"):
            return True
    return False


def parse_request_method(request):
    headers = request.split("\r\n")
    if len(headers) > 0 and len(headers[0].split()) == 3:
        request_line = headers[0].split()
        method = request_line[0]
        return method
    return "bad_request"


while True:
    connectionSocket, addr = serverSocket.accept()
    request = connectionSocket.recv(1024).decode()

    # Checks Content-Length first
    method = parse_request_method(request)
    if method != "GET" and not parse_content_length(request):
        response = create_http_response("411 Length Required", "Content-Length Required")
        connectionSocket.send(response.encode())
        connectionSocket.close()
        continue

    modified_since = parse_modified_since(request)
    filename = parse_request_header(request)

    if filename == 'test.html':
        file_path = 'test.html'
        file_last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path), timezone.utc)

        if modified_since and modified_since >= file_last_modified_time:
            response = create_http_response("304 Not Modified", file_path='test.html')
        else:
            try:
                with open('test.html', 'r') as file:
                    content = file.read()
                    response = create_http_response("200 OK", content, file_path='test.html')
            except FileNotFoundError:
                response = create_http_response("404 Not Found", "File Not Found", file_path='test.html')
    elif filename == "bad_request":
        response = create_http_response("400 Bad Request", "Invalid Request")
    else:
        response = create_http_response("403 Forbidden", "Access Denied")

    connectionSocket.send(response.encode())

    connectionSocket.close()
