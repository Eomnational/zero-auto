import socket, threading, os, base64
from urllib.parse import urlparse

UP = urlparse(os.environ['UPSTREAM'])
UP_HOST, UP_PORT = UP.hostname, UP.port
UP_AUTH = None
if UP.username:
    UP_AUTH = base64.b64encode(f"{UP.username}:{UP.password or ''}".encode()).decode()
KK_HOST = os.environ.get('KK_HOST', 'gate.kookeey.info')
KK_PORT = int(os.environ.get('KK_PORT', '1000'))
KK_AUTH = os.environ.get('KK_AUTH_B64', '')
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', '18081'))

def log(*a):
    print(*a, flush=True)

def read_head(sock):
    buf = b""
    while b"\r\n\r\n" not in buf and len(buf) < 65536:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    head, _, rest = buf.partition(b"\r\n\r\n")
    return head, rest

def egress_connect(target_host, target_port):
    s = socket.create_connection((UP_HOST, UP_PORT), timeout=25)
    lines = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\nProxy-Connection: keep-alive\r\n"
    if UP_AUTH:
        lines += f"Proxy-Authorization: Basic {UP_AUTH}\r\n"
    s.sendall((lines + "\r\n").encode())
    head, _ = read_head(s)
    status = head.split(b"\r\n")[0].decode(errors="replace")
    if " 200" not in status:
        s.close()
        raise IOError("egress CONNECT failed: " + status)
    return s

def gate_tunnel():
    return egress_connect(KK_HOST, KK_PORT)

def gate_connect(target):
    s = gate_tunnel()
    lines = f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\nProxy-Connection: keep-alive\r\n"
    if KK_AUTH:
        lines += f"Proxy-Authorization: Basic {KK_AUTH}\r\n"
    s.sendall((lines + "\r\n").encode())
    head, rest = read_head(s)
    status = head.split(b"\r\n")[0].decode(errors="replace")
    log("GATE CONNECT", target, status)
    if " 200" not in status:
        s.close()
        raise IOError("gate CONNECT failed: " + status)
    return s, rest

def shuttle(a, b):
    try:
        while True:
            data = a.recv(65536)
            if not data:
                break
            b.sendall(data)
    except OSError:
        pass
    try:
        b.shutdown(socket.SHUT_WR)
    except OSError:
        pass

def handle(client):
    try:
        head, rest = read_head(client)
        if not head:
            client.close(); return
        line = head.split(b"\r\n")[0].decode(errors="replace")
        parts = line.split(" ")
        log("REQ", line[:140])
        if parts[0].upper() == "CONNECT":
            target = parts[1]
            up, grest = gate_connect(target)
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            if grest:
                client.sendall(grest)
            if rest:
                up.sendall(rest)
            t = threading.Thread(target=shuttle, args=(client, up), daemon=True)
            t.start()
            shuttle(up, client)
        else:
            # absolute-form http request -> forward through gate as HTTP proxy
            up = gate_tunnel()
            new_lines = [line]
            for h in head.decode(errors="replace").split("\r\n")[1:]:
                hl = h.lower()
                if hl.startswith("proxy-authorization:") or hl.startswith("proxy-connection:"):
                    continue
                new_lines.append(h)
            if KK_AUTH:
                new_lines.append(f"Proxy-Authorization: Basic {KK_AUTH}")
            new_lines.append("Proxy-Connection: keep-alive")
            up.sendall(("\r\n".join(new_lines) + "\r\n\r\n").encode() + rest)
            t = threading.Thread(target=shuttle, args=(client, up), daemon=True)
            t.start()
            shuttle(up, client)
    except Exception as e:
        log("HANDLE-ERR", repr(e)[:140])
        try: client.close()
        except OSError: pass

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", LISTEN_PORT))
srv.listen(50)
log(f"chain relay on {LISTEN_PORT} -> {KK_HOST}:{KK_PORT} via egress")
while True:
    c, _ = srv.accept()
    threading.Thread(target=handle, args=(c,), daemon=True).start()
