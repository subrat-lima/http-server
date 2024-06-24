import re
import os
import gzip
import socket
import argparse

HOST = "localhost"

STATUS_CODES = {200: "OK", 404: "Not Found"}

SUPPORTED_ENCODING_FORMATS = ["gzip"]
FILE_TYPES = {
    "html": "text/html",
    "css": "text/css",
    "js": "text/javascript",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "aac": "audio/aac",
}


def get_options():
    directory = os.getcwd()
    port = 4221
    parser = argparse.ArgumentParser(description="options to configure http server")
    parser.add_argument("--directory", help="selects directory to scan")
    parser.add_argument("--port", help="selects the port")
    args = parser.parse_args()
    if args.directory is not None:
        directory = args.directory
    if args.port is not None:
        port = int(args.port)
    return {"directory": directory, "port": port}


def parse_request(data_packet):
    method = re.search(r"^(?P<method>(GET))", data_packet).group("method")
    path = re.search(r"^\w+\s(?P<path>[^\s]+)", data_packet).group("path")
    protocol = re.search(r"(?P<protocol>HTTP/\d\.\d)", data_packet).group("protocol")
    host = re.search(r"Host:\s(?P<host>\w+:\d+)", data_packet).group("host")

    accept_encoding = []
    if "Accept-Encoding" in data_packet:
        accept_encoding_set = set(
            re.search(
                r"Accept-Encoding:\s(?P<accept_encoding>([a-zA-Z0-9-]+(,\s)?)+)",
                data_packet,
            )
            .group("accept_encoding")
            .split(", ")
        )
        for encoding in accept_encoding_set:
            if encoding is SUPPORTED_ENCODING_FORMATS:
                accept_encoding.append(encoding)
        if len(accept_encoding) > 0:
            accept_encoding = ", ".join(accept_encoding)

    body = None
    request = {
        "headers": {
            "method": method,
            "path": path,
            "protocol": protocol,
            "host": host,
            "accept_encoding": accept_encoding,
        },
        "body": body,
    }
    return request


def generate_response(request, response):
    headers = f"{request['headers']['protocol']} {response['headers']['status_code']} {STATUS_CODES[response['headers']['status_code']]}\r\n"
    if "content_type" in response["headers"]:
        headers += f"Content-Type: {response['headers']['content_type']}\r\n"
        headers += f"Content-Length: {response['headers']['content_length']}\r\n"
    if "accept_encoding" in response["headers"]:
        headers += f"Content-Encoding: {response['headers']['accept_encoding']}\r\n"
    headers += "\r\n"
    response_packet = b"".join([headers.encode(), response["body"]])
    print("response: ")
    print(response_packet)
    return response_packet


def resolve_request(request, response):
    directory = get_options()["directory"]
    file_path = request["headers"]["path"]
    if file_path == "/":
        file_path = "index.html"
    else:
        file_path = file_path[1:]

    response["headers"] = {"status_code": 404}
    response["body"] = b""
    file_type = file_path.split(".")[-1]
    file_name = os.path.join(directory, file_path)
    if os.path.exists(file_name):
        with open(file_name) as f:
            response["body"] = f.read()
            if "gzip" in request["headers"]["accept_encoding"]:
                response["body"] = gzip.compress(bytes(body, "utf-8"))
                response["headers"]["accept_encoding"] = request["headers"][
                    "accept_encoding"
                ]
            response["headers"]["content_length"] = len(response["body"])
            response["headers"]["content_type"] = FILE_TYPES[file_type]
            response["headers"]["status_code"] = 200
            response["body"] = response["body"].encode()


def handle_connection(connection):
    data_packet = connection.recv(1024)
    print(data_packet)
    request = parse_request(data_packet.decode())

    response = {}
    resolve_request(request, response)
    print("resolved_request: ")
    print(response)

    response_packet_data = generate_response(request, response)
    print(f"response_packet_data:")
    print(response_packet_data)
    connection.sendall(response_packet_data)


def main():
    port = get_options()["port"]
    with socket.create_server((HOST, port), reuse_port=True) as server_socket:
        print(f"server running at http://{HOST}:{port}")
        while True:
            connection, addr = server_socket.accept()
            with connection:
                handle_connection(connection)


if __name__ == "__main__":
    main()
