import re
import os
import socket
import argparse

HOST = "localhost"
PORT = 4221

STATUS_CODES = {200: "OK", 404: "Not Found"}


def get_directory():
    directory = os.getcwd()
    parser = argparse.ArgumentParser(description="selects directory to scan")
    parser.add_argument("--directory", help="selects directory to scan")
    args = parser.parse_args()
    print(f"directory: {args.directory}")
    if args.directory is not None:
        directory = args.directory
        print(f"directory set to {directory}")
    return directory


def parse_request(data_packet):
    method = re.search(r"^(?P<method>(GET))", data_packet).group("method")
    path = re.search(r"^\w+\s(?P<path>[^\s]+)", data_packet).group("path")
    protocol = re.search(r"(?P<protocol>HTTP/\d\.\d)", data_packet).group("protocol")
    host = re.search(r"Host:\s(?P<host>\w+:\d+)", data_packet).group("host")

    body = None
    request = {
        "headers": {"method": method, "path": path, "protocol": protocol, "host": host},
        "body": body,
    }
    return request


def generate_response(request, status_code, body):
    header = f"{request['headers']['protocol']} {status_code} {STATUS_CODES[status_code]}\r\n\r\n"
    header = header.encode()
    body = body.encode()
    response = header + body
    return response


def handle_connection(connection):
    data_packet = connection.recv(1024)
    print(data_packet)
    request = parse_request(data_packet.decode())

    body = ""
    if request["headers"]["path"] == "/":
        status_code = 200
    else:
        directory = get_directory()
        print(f"directory: {directory}")
        file_name = os.path.join(directory, request["headers"]["path"][1:])
        print(file_name)
        if os.path.exists(file_name):
            print(f"file_found")
            status_code = 200
            with open(file_name) as f:
                body = f.read()
        else:
            status_code = 404

    response = generate_response(request, status_code, body)
    connection.sendall(response)


def main():
    with socket.create_server((HOST, PORT), reuse_port=True) as server_socket:
        print(f"server running at http://{HOST}:{PORT}")
        while True:
            connection, addr = server_socket.accept()
            with connection:
                handle_connection(connection)


if __name__ == "__main__":
    main()
