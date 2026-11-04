"""
Flash Socket Policy Server (TCP 843 & Inline)
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Permits Adobe Flash Player PPAPI socket connections from any domain/port.
"""

import socket
import threading
import sys
import os

POLICY_XML = (
    b'<?xml version="1.0"?>\n'
    b'<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">\n'
    b'<cross-domain-policy>\n'
    b'    <allow-access-from domain="*" to-ports="*" />\n'
    b'    <site-control permitted-cross-domain-policies="all" />\n'
    b'</cross-domain-policy>\x00'
)


class PolicyServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 843):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None

    def start(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sys.platform != 'win32':
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            elif hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(10)
            self.running = True
            print(f"[+] Flash Socket Policy Server listening on {self.host}:{self.port}")
        except PermissionError:
            print(f"[-] Permission denied binding to port {self.port} (requires Administrator privileges on Windows).")
            print(f"[*] Note: The DDTank Game Server also handles inline policy requests on game port 9200.")
            return False
        except Exception as e:
            print(f"[-] Could not bind policy server on port {self.port}: {e}")
            return False

        threading.Thread(target=self._accept_loop, daemon=True).start()
        return True

    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.sock.accept()
                threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client: socket.socket, addr):
        try:
            client.settimeout(3.0)
            data = client.recv(1024)
            if b'<policy-file-request/>' in data or b'policy' in data.lower():
                client.sendall(POLICY_XML)
                print(f"[+] Served Socket Policy to {addr[0]}:{addr[1]}")
            else:
                client.sendall(POLICY_XML)
        except Exception:
            pass
        finally:
            try:
                client.close()
            except Exception:
                pass

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 843
    server = PolicyServer(port=port)
    if server.start():
        print("[*] Press Ctrl+C to stop.")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
            print("[*] Policy Server stopped.")
