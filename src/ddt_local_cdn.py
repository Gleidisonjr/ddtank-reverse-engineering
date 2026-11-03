"""
DDTank Local CDN & Asset Web Server
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Hosts Flash assets, config.xml, crossdomain.xml, and API endpoints.
"""

import http.server
import socketserver
import os
import sys
import json
import socket

PORT = 8080
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WWW_DIR = os.path.join(BASE_DIR, 'www')

MIME_TYPES = {
    '.swf': 'application/x-shockwave-flash',
    '.xml': 'text/xml; charset=utf-8',
    '.ashx': 'text/xml; charset=utf-8',
    '.aspx': 'text/xml; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.css': 'text/css; charset=utf-8',
    '.ico': 'image/x-icon',
}


def get_tailscale_ip():
    """Attempts to find the Tailscale 100.x.y.z IP address on this machine."""
    try:
        import subprocess
        out = subprocess.check_output(['tailscale', 'ip', '-4'], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ip.startswith("100."):
                    return ip
        except Exception:
            pass
    return None


class DDTLocalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WWW_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS for Flash and Web runtimes
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in MIME_TYPES:
            return MIME_TYPES[ext]
        return super().guess_type(path)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        # Read and discard payload for ASP.NET / Flash requests
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            _ = self.rfile.read(content_length)
        return self.do_GET()

    def do_GET(self):
        # Handle IP API endpoint
        if self.path.startswith('/api/ip'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            resp = {
                "ip": self.client_address[0],
                "country": "BR",
                "city": "Localhost",
                "status": "success"
            }
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return

        # Redirect root to player.html
        if self.path in ('/', '/index.html'):
            self.path = '/player.html'

        # Route LoginSelectList
        if 'loginselectlist' in self.path.lower():
            self.path = '/request/LoginSelectList.ashx'

        # Route CreateLogin
        if 'createlogin' in self.path.lower():
            self.path = '/request/CreateLogin.ashx'

        # Fallback for /LoadServerList.ashx or ServerList.ashx
        if 'serverlist' in self.path.lower():
            self.path = '/request/ServerList.xml'

        # Strip query string for file existence check
        clean_path = self.path.split('?')[0].split('#')[0]
        local_file = os.path.normpath(os.path.join(WWW_DIR, clean_path.lstrip('/')))

        # If file does not exist, but is an XML, ASHX or ASPX request, serve dynamic success XML
        if not os.path.exists(local_file) and (clean_path.endswith('.xml') or clean_path.endswith('.ashx') or clean_path.endswith('.aspx')):
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.end_headers()
            fallback_xml = b'<?xml version="1.0" encoding="utf-8" ?>\n<Result value="true" message="Success">\n</Result>\n'
            self.wfile.write(fallback_xml)
            return

        return super().do_GET()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_cdn_server(port=PORT):
    ts_ip = get_tailscale_ip()
    local_ip = "127.0.0.1"

    print("==================================================================")
    print("        DDTank Local CDN & Asset Web Server Active                ")
    print("==================================================================")
    print(f"[+] Root Directory: {WWW_DIR}")
    print(f"[+] Local URL:      http://{local_ip}:{port}/player.html")
    if ts_ip:
        print(f"[+] Tailscale URL:  http://{ts_ip}:{port}/player.html (Share with friends)")
    else:
        print("[*] Tailscale not detected or not connected (Localhost mode)")
    print(f"[+] Assets hosted:  /flash/Loading.swf, /flash/2.swf, /config.xml")
    print("==================================================================")

    server = ThreadingHTTPServer(('0.0.0.0', port), DDTLocalHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down CDN server...")
        server.shutdown()


if __name__ == '__main__':
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_cdn_server(p)
