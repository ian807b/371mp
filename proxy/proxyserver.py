import socket
import http.client

serverPort = 8888
proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxySocket.bind(('', serverPort))
proxySocket.listen(1)

print("Proxy Server is ready to receive")

cache = {}


def forward_request(path, last_modified=None):
    connection = http.client.HTTPConnection("localhost", 12000)
    headers = {}
    if last_modified:
        headers['If-Modified-Since'] = last_modified
    connection.request("GET", path, headers=headers)
    response = connection.getresponse()
    return response.status, response.reason, response.getheaders(), response.read()


while True:
    connectionSocket, addr = proxySocket.accept()
    request = connectionSocket.recv(1024).decode()

    if not request:
        connectionSocket.close()
        continue

    first_line = request.split('\n')[0]
    path = first_line.split(' ')[1]

    cached_item = cache.get(path)
    last_modified = cached_item[1] if cached_item else None

    status, reason, headers, content = forward_request(path, last_modified)

    if status == 304:
        content = cached_item[0]
        status, reason = 200, "OK"
    elif status == 200:
        last_modified = next((header[1] for header in headers if header[0].lower() == 'last-modified'), None)
        cache[path] = (content, last_modified)

        if path == '/test.html':
            with open('test.html', 'wb') as file:
                file.write(content)

    response = "HTTP/1.1 " + str(status) + " " + reason + "\r\n"
    for header in headers:
        response += header[0] + ": " + header[1] + "\r\n"
    response += "\r\n"
    response += content.decode() if content else ""
    connectionSocket.send(response.encode())
    connectionSocket.close()
