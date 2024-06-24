import re
import os
import socket
import argparse

HOST = "localhost"
PORT = 4221
directory = os.getcwd()

STATUS_CODES = {200: "OK", 404: "Not Found"}


def set_directory():
    parser = argparse.ArgumentParser(description="selects directory to scan")
    parser.add_argument("--directory", help="selects directory to scan")
    args = parser.parse_args()
    if args.directory is not None:
        directory = args.directory


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
    response = f"{header}{body}"
    return response.encode()


def handle_connection(connection):
    data_packet = connection.recv(1024)
    print(data_packet)
    request = parse_request(data_packet.decode())

    body = ""
    if request["headers"]["path"] == "/":
        status_code = 200
    else:
        file_name = os.path.join(directory, request["headers"]["path"][1:])
        print(file_name)
        if os.path.exists(file_name):
            print(f"file_found")
            status_code = 200
        else:
            status_code = 404

    response = generate_response(request, status_code, body)
    connection.sendall(response)


def main():
    set_directory()
    with socket.create_server((HOST, PORT), reuse_port=True) as server_socket:
        print(f"server running at http://{HOST}:{PORT}")
        while True:
            connection, addr = server_socket.accept()
            with connection:
                handle_connection(connection)


if __name__ == "__main__":
    main()
