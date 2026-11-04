"""
DDTank Local CDN & Asset Web Server
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Hosts Flash assets, config.xml, crossdomain.xml, and API endpoints.
Provides case-insensitive path resolution, CompressTextLoader zlib+XOR encoding,
and transparent upstream caching.
"""

import http.server
import socketserver
import os
import sys
import json
import socket
import re
import shutil
import urllib.parse
import urllib.request
import urllib.error
import zlib

PORT = 8080
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WWW_DIR = os.path.join(BASE_DIR, 'www')

UPSTREAM_CDN = 'https://resource.ddclassico.com'
UPSTREAM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 DDClassico/2.0.5',
    'Referer': 'https://game.ddclassico.com/'
}

# DDT_Loading.swf supplies the CompressTextLoader used at runtime, including
# by the core loaded into its ApplicationDomain. The older decoder embedded
# in 2.png is shadowed by it. Only the first 1024 compressed bytes are XORed.
DDT_XOR_KEY = bytes([127, 95, 200, 255, 15, 34, 78, 90])
DDT_XOR_LIMIT = 1024

# StartupResourceLoader uses TextLoader for these tables. Sending compressed
# bytes to those analyzers produces Flash XML parser Error #1090.
PLAIN_XML_TABLES = frozenset({
    'serverlist.xml', 'pettemplateinfo.xml', 'petskillinfo.xml',
    'petconfiginfo.xml', 'petlevelinfo.xml', 'totemhonortemplate.xml',
})

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
    '.flv': 'video/x-flv',
    '.mp3': 'audio/mpeg',
    '.txt': 'text/plain; charset=utf-8',
    '.bin': 'application/octet-stream',
    '.zip': 'application/zip',
}


def encode_compress_text(data: bytes) -> bytes:
    """Encode a table for the CompressTextLoader supplied by DDT_Loading.swf."""
    compressed = bytearray(zlib.compress(data))
    for i in range(min(len(compressed), DDT_XOR_LIMIT)):
        compressed[i] ^= DDT_XOR_KEY[i % len(DDT_XOR_KEY)]
    return bytes(compressed)


def is_compressed_text_file(clean_path: str) -> bool:
    """
    Determines if the requested endpoint expects CompressTextLoader (zlib+XOR) encoding.
    Most /request/*.xml tables use CompressTextLoader; the channel list and
    several pet/totem tables use TextLoader instead (including localized paths).
    """
    clean_lower = clean_path.lower()
    if clean_lower.startswith('/request/') and clean_lower.endswith('.xml'):
        if clean_lower.rsplit('/', 1)[-1] in PLAIN_XML_TABLES:
            return False
        return True
    return False


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


def find_case_insensitive(base_dir: str, rel_path: str) -> str | None:
    """
    Case-insensitive filesystem lookup.
    Given rel_path (e.g. 'flash/ddt_loading.swf' or 'flash/ui/portugal/xml/xml.png'),
    finds the matching file on disk even on case-sensitive filesystems.
    """
    current = os.path.abspath(base_dir)
    clean = rel_path.replace('\\', '/').strip('/')
    if not clean:
        return current
    parts = [p for p in clean.split('/') if p and p != '.']
    for part in parts:
        if part == '..':
            return None
        if not os.path.isdir(current):
            return None
        entries = os.listdir(current)
        if part in entries:
            current = os.path.join(current, part)
        else:
            part_lower = part.lower()
            matched = None
            for entry in entries:
                if entry.lower() == part_lower:
                    matched = entry
                    break
            if matched:
                current = os.path.join(current, matched)
            else:
                return None
    return current


def find_local_asset(rel_path: str) -> str | None:
    """
    Locates asset locally with case-insensitivity and path alias fallbacks:
    1. Direct case-insensitive lookup in WWW_DIR
    2. Try prefixing 'flash/' if missing (e.g. 'ui/...' -> 'flash/ui/...')
    3. Resolve localized request tables against the flat request/ exports
    4. If .swf, check 'flash/ui/portugal/swf/<name>' and 'flash/<name>'
    """
    local = find_case_insensitive(WWW_DIR, rel_path)
    if local and os.path.isfile(local):
        return local

    clean_rel = rel_path.lstrip('/')
    if not clean_rel.startswith('flash/'):
        local = find_case_insensitive(WWW_DIR, f"flash/{clean_rel}")
        if local and os.path.isfile(local):
            return local

    # The core prefixes localized tables with LANGUAGE, while our exported
    # tables are stored directly in request/ (e.g. portugal/TemplateAllList.xml).
    parts = clean_rel.replace('\\', '/').split('/')
    if (len(parts) == 3 and parts[0].lower() == 'request'
            and parts[1] not in ('', '.', '..') and parts[2].lower().endswith('.xml')):
        local = find_case_insensitive(WWW_DIR, f"request/{parts[2]}")
        if local and os.path.isfile(local):
            return local

    if clean_rel.lower().endswith('.swf'):
        bname = os.path.basename(clean_rel)
        local = find_case_insensitive(WWW_DIR, f"flash/ui/portugal/swf/{bname}")
        if local and os.path.isfile(local):
            return local
        local = find_case_insensitive(WWW_DIR, f"flash/{bname}")
        if local and os.path.isfile(local):
            return local

    return None


def fetch_upstream_asset(rel_path: str, save_path: str) -> bytes | None:
    """
    Attempts to download a missing asset from the official upstream CDN.
    Caches the file locally on success so subsequent requests are instantaneous.
    Tries both rel_path and flash/rel_path.
    """
    clean_rel = rel_path.lstrip('/')
    candidate_urls = [f"{UPSTREAM_CDN}/{clean_rel}"]
    if not clean_rel.startswith('flash/'):
        candidate_urls.append(f"{UPSTREAM_CDN}/flash/{clean_rel}")

    for url in candidate_urls:
        req = urllib.request.Request(url, headers=UPSTREAM_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    data = resp.read()
                    try:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(data)
                        print(f"[+] Cached upstream asset: /{clean_rel} ({len(data)} bytes from {url})")
                    except Exception as e:
                        print(f"[!] Warning: Failed to write cached asset {save_path}: {e}")
                    return data
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"[-] Upstream HTTP {e.code} for {url}")
        except Exception as e:
            print(f"[-] Upstream fetch failed for {url}: {e}")
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

    def serve_file(self, filepath: str):
        try:
            f = open(filepath, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return
        try:
            fs = os.fstat(f.fileno())
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(filepath))
            self.send_header('Content-Length', str(fs[6]))
            self.end_headers()
            shutil.copyfileobj(f, self.wfile)
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            f.close()

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
        clean_path = urllib.parse.unquote(self.path.split('?')[0].split('#')[0])

        # Normalize UI double slashes: /ui// -> /ui/portugal/
        if '/ui//' in clean_path:
            clean_path = clean_path.replace('/ui//', '/ui/portugal/')
        elif 'ui//' in clean_path:
            clean_path = clean_path.replace('ui//', 'ui/portugal/')

        # Collapse duplicate slashes
        clean_path = re.sub(r'/+', '/', clean_path)
        clean_lower = clean_path.lower()

        # Handle IP API endpoint
        if clean_path.startswith('/api/ip'):
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
        if clean_path in ('', '/', '/index.html'):
            clean_path = '/player.html'

        # Route known endpoints
        if 'loginselectlist' in clean_lower:
            clean_path = '/request/LoginSelectList.ashx'
        elif 'createlogin' in clean_lower:
            clean_path = '/request/CreateLogin.ashx'
        elif clean_lower.rsplit('/', 1)[-1] in ('serverlist.xml', 'serverlist.ashx', 'loadserverlist.ashx'):
            clean_path = '/request/ServerList.xml'
        elif 'serverconfig' in clean_lower:
            clean_path = '/request/ServerConfig.xml'
        elif 'votesubmit' in clean_lower:
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<?xml version="1.0" encoding="utf-8" ?>\n<Result value="true" message="Success">\n    <Item result="1" />\n</Result>\n')
            return

        rel_path = clean_path.lstrip('/')

        # Determine host/ports for rewriting if needed
        host_header = self.headers.get('Host', '')
        req_host = host_header.split(':')[0].strip() or '127.0.0.1'
        cdn_port = self.server.server_port
        game_port = int(os.environ.get('DDT_GAME_PORT', '9200'))
        needs_rewrite = (
            req_host not in ('127.0.0.1', 'localhost')
            or cdn_port != 8080
            or game_port != 9200
        )

        # Handle tables loaded through CompressTextLoader.
        if is_compressed_text_file(clean_path):
            local_file = find_local_asset(rel_path)
            if local_file and os.path.isfile(local_file):
                with open(local_file, 'rb') as f:
                    body = f.read()
                if needs_rewrite:
                    target_host = '127.0.0.1' if req_host in ('127.0.0.1', 'localhost') else req_host
                    body = body.replace(b'127.0.0.1:8080', f'{target_host}:{cdn_port}'.encode('utf-8'))
                    body = body.replace(b'127.0.0.1', target_host.encode('utf-8'))
                    if game_port != 9200:
                        body = body.replace(b'Port="9200"', f'Port="{game_port}"'.encode('utf-8'))
                if body.lstrip().startswith(b'<'):
                    body = encode_compress_text(body)
                self.send_response(200)
                self.send_header('Content-Type', 'text/xml')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            else:
                # Fallback for missing compressed XML
                fallback_xml = b'<?xml version="1.0" encoding="utf-8" ?>\n<Result value="true" message="Success">\n</Result>\n'
                body = encode_compress_text(fallback_xml)
                self.send_response(200)
                self.send_header('Content-Type', 'text/xml')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

        local_file = find_local_asset(rel_path)

        # Dynamically rewrite host/ports for Tailscale or fallback CDN/Game ports
        if needs_rewrite and local_file and os.path.isfile(local_file):
            base_lower = os.path.basename(local_file).lower()
            if base_lower in ('player.html', 'config.xml', 'serverlist.xml', 'loadserverlist.ashx'):
                target_host = '127.0.0.1' if req_host in ('127.0.0.1', 'localhost') else req_host
                with open(local_file, 'rb') as f:
                    body = f.read()
                body = body.replace(b'127.0.0.1:8080', f'{target_host}:{cdn_port}'.encode('utf-8'))
                body = body.replace(b'127.0.0.1', target_host.encode('utf-8'))
                if game_port != 9200:
                    body = body.replace(b'Port="9200"', f'Port="{game_port}"'.encode('utf-8'))
                self.send_response(200)
                self.send_header('Content-Type', self.guess_type(local_file))
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

        # If local file exists, serve it directly
        if local_file and os.path.isfile(local_file):
            self.serve_file(local_file)
            return

        # Missing asset: try dynamic upstream caching
        is_asset = (
            not clean_path.startswith('/request/') and
            (any(clean_path.startswith(p) for p in ('/flash/', '/image/', '/sound/', '/ui/', '/map/', '/art/', '/res/'))
             or os.path.splitext(clean_path)[1].lower() in ('.swf', '.png', '.jpg', '.jpeg', '.gif', '.flv', '.mp3', '.txt', '.xml', '.bin', '.zip'))
        )
        if is_asset:
            save_dest = os.path.normpath(os.path.join(WWW_DIR, rel_path))
            cached_data = fetch_upstream_asset(rel_path, save_dest)
            if cached_data is not None:
                self.send_response(200)
                self.send_header('Content-Type', self.guess_type(save_dest))
                self.send_header('Content-Length', str(len(cached_data)))
                self.end_headers()
                self.wfile.write(cached_data)
                return

        # Missing API request under /request/ or general XML/ASHX/ASPX fallback
        if clean_path.startswith('/request/') or clean_path.endswith(('.xml', '.ashx', '.aspx')):
            self.send_response(200)
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.end_headers()
            fallback_xml = b'<?xml version="1.0" encoding="utf-8" ?>\n<Result value="true" message="Success">\n</Result>\n'
            self.wfile.write(fallback_xml)
            return

        self.send_error(404, f"File not found: {clean_path}")


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = (sys.platform != 'win32')


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
    print(f"[+] Assets hosted:  /flash/DDT_Loading.swf, /flash/2.png, /config.xml")
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
