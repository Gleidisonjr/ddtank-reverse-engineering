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

# 100% compliant minimal AS3 SWF (31 bytes, AS3 bit set, ShowFrame, End)
MINIMAL_AS3_SWF = bytes.fromhex('4657530e1f000000780007d000001770000018010044110800000040000000')

# 1x1 transparent dummy PNG (67 bytes)
EMPTY_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


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
        # Normalize double slashes and strip query parameters for routing
        query = ''
        if '?' in self.path:
            raw_path, query = self.path.split('?', 1)
            query = '?' + query
        else:
            raw_path = self.path

        while '//' in raw_path:
            raw_path = raw_path.replace('//', '/')

        self.path = raw_path + query

        # Handle IP API endpoint
        if raw_path.startswith('/api/ip'):
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
        if raw_path in ('/', '/index.html'):
            self.path = '/player.html' + query
            raw_path = '/player.html'

        # Route LoginSelectList
        if 'loginselectlist' in raw_path.lower():
            self.path = '/request/LoginSelectList.ashx' + query
            raw_path = '/request/LoginSelectList.ashx'

        # Route CreateLogin
        if 'createlogin' in raw_path.lower():
            self.path = '/request/CreateLogin.ashx' + query
            raw_path = '/request/CreateLogin.ashx'

        # Fallback for /LoadServerList.ashx or ServerList.ashx
        if 'serverlist' in raw_path.lower():
            self.path = '/request/ServerList.xml' + query
            raw_path = '/request/ServerList.xml'

        # Route PickGliss UI package (xml.png)
        if raw_path.endswith('xml.png') or 'xml.png' in raw_path:
            xml_png_path = os.path.join(WWW_DIR, 'flash', 'ui', 'xml', 'xml.png')
            if not os.path.exists(xml_png_path):
                xml_png_path = os.path.join(WWW_DIR, 'ui', 'xml', 'xml.png')
            if os.path.exists(xml_png_path):
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                with open(xml_png_path, 'rb') as f:
                    content = f.read()
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Route 3.png (Trainer SWF package)
        if raw_path.endswith('3.png') or '3.png' in raw_path:
            p3 = os.path.join(WWW_DIR, 'flash', '3.png')
            if not os.path.exists(p3):
                p3 = os.path.join(WWW_DIR, '3.png')
            content = None
            if os.path.exists(p3):
                with open(p3, 'rb') as f:
                    content = f.read()
            else:
                content = MINIMAL_AS3_SWF
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        clean_path = raw_path
        local_file = os.path.normpath(os.path.join(WWW_DIR, clean_path.lstrip('/')))

        # Dual path resolution: try with and without /flash/ prefix
        if not os.path.exists(local_file):
            if clean_path.startswith('/flash/'):
                alt_file = os.path.normpath(os.path.join(WWW_DIR, clean_path[7:]))
                if os.path.exists(alt_file):
                    local_file = alt_file
            else:
                alt_file = os.path.normpath(os.path.join(WWW_DIR, 'flash', clean_path.lstrip('/')))
                if os.path.exists(alt_file):
                    local_file = alt_file

        # If file exists on disk, serve it directly
        if os.path.exists(local_file) and not os.path.isdir(local_file):
            ctype = self.guess_type(local_file)
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            with open(local_file, 'rb') as f:
                content = f.read()
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # Dynamic Fallback 1: Any requested SWF that does not exist -> return valid minimal AS3 SWF
        if clean_path.endswith('.swf'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-shockwave-flash')
            self.send_header('Content-Length', str(len(MINIMAL_AS3_SWF)))
            self.end_headers()
            self.wfile.write(MINIMAL_AS3_SWF)
            return

        # Dynamic Fallback 2: XML, ASHX or ASPX -> return valid success XML
        if clean_path.endswith('.xml') or clean_path.endswith('.ashx') or clean_path.endswith('.aspx'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            fallback_xml = b'<?xml version="1.0" encoding="utf-8" ?>\n<Result value="true" message="Success">\n</Result>\n'
            self.send_header('Content-Length', str(len(fallback_xml)))
            self.end_headers()
            self.wfile.write(fallback_xml)
            return

        # Dynamic Fallback 3: Images (PNG, JPG, etc.) -> return 1x1 transparent PNG
        if clean_path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(EMPTY_PNG)))
            self.end_headers()
            self.wfile.write(EMPTY_PNG)
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
