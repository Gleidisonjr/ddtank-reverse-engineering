"""
Unit & Integration Tests for DDTank Local CDN Loading Pipeline.
Tests:
- CompressTextLoader zlib + 7Road byte XOR key encoding.
- Detection of CompressTextLoader vs plain text endpoints.
- Path resolution & aliasing for UI module SWFs across languages.
- Fallback behavior for missing template XMLs.
"""

import unittest
import zlib
import os
import sys
import random
import struct
import threading
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from ddt_local_cdn import (
    encode_compress_text,
    is_compressed_text_file,
    find_local_asset,
    WWW_DIR,
    DDTLocalHandler,
    ThreadingHTTPServer,
)


def decode_client_table(data):
    # Independent implementation of the runtime's CompressTextLoader from
    # DDT_Loading.swf: key [127, 95, 200, 255, 15, 34, 78, 90], first 1024 bytes.
    decoded = bytearray(data)
    key = b'\x7f\x5f\xc8\xff\x0f\x22\x4e\x5a'
    for i in range(min(len(decoded), 1024)):
        decoded[i] ^= key[i % 8]
    return zlib.decompress(decoded)


class TestCDNLoading(unittest.TestCase):
    def test_compress_text_loader_roundtrip(self):
        sample_xml = b'<?xml version="1.0" encoding="utf-8" ?>\n<Result value="true" message="Success">\n    <Item Name="VIPLevelExp" Value="100,500" />\n</Result>\n'
        encoded = encode_compress_text(sample_xml)
        
        # Verify it was transformed and is not plain text
        self.assertFalse(encoded.startswith(b'<?xml'))
        
        self.assertEqual(decode_client_table(encoded), sample_xml)

    def test_large_table_preserves_bytes_after_client_xor_window(self):
        # A short table cannot catch XOR applied beyond the client's window.
        rng = random.Random(205)
        sample = bytes(rng.randrange(256) for _ in range(8192))
        compressed = zlib.compress(sample)
        self.assertGreater(len(compressed), 1024)
        encoded = encode_compress_text(sample)
        self.assertEqual(encoded[1024:], compressed[1024:])
        self.assertEqual(decode_client_table(encoded), sample)

    def test_is_compressed_text_file(self):
        # Tables under /request/*.xml expect CompressTextLoader
        self.assertTrue(is_compressed_text_file('/request/ServerConfig.xml'))
        self.assertTrue(is_compressed_text_file('/request/serverconfig.xml'))
        self.assertTrue(is_compressed_text_file('/request/TemplateAllList.xml'))
        self.assertTrue(is_compressed_text_file('/request/BallList.xml'))
        self.assertTrue(is_compressed_text_file('/request/QuestList.xml'))
        self.assertTrue(is_compressed_text_file('/request/MapServerList.xml'))
        self.assertTrue(is_compressed_text_file('/request/portugal/TemplateAllList.xml'))

        # ServerList.xml / ServerList.ashx uses RequestLoader (plain text)
        self.assertFalse(is_compressed_text_file('/request/ServerList.xml'))
        self.assertFalse(is_compressed_text_file('/request/ServerList.ashx'))
        self.assertFalse(is_compressed_text_file('/request/LoadServerList.ashx'))
        self.assertFalse(is_compressed_text_file('/request/portugal/PetTemplateInfo.xml'))
        self.assertFalse(is_compressed_text_file('/request/PetSkillInfo.xml'))
        self.assertFalse(is_compressed_text_file('/request/PetConfigInfo.xml'))
        self.assertFalse(is_compressed_text_file('/request/PetLevelInfo.xml'))
        self.assertFalse(is_compressed_text_file('/request/TotemHonorTemplate.xml'))

        # User and account API endpoints are plain text
        self.assertFalse(is_compressed_text_file('/request/LoginSelectList.ashx'))
        self.assertFalse(is_compressed_text_file('/request/CreateLogin.ashx'))

        # Root and flash files are plain text
        self.assertFalse(is_compressed_text_file('/config.xml'))
        self.assertFalse(is_compressed_text_file('/flash/characterdefine.xml'))
        self.assertFalse(is_compressed_text_file('/flash/ui/portugal/levelreward.xml'))

    def test_ui_module_swf_resolution(self):
        # Chat SWF aliases
        chat_local = find_local_asset('ui/spain/swf/chat.swf')
        self.assertIsNotNone(chat_local)
        self.assertTrue(os.path.isfile(chat_local))
        self.assertTrue(chat_local.lower().endswith('chat.swf'))

        # CoreI SWF aliases (case insensitive)
        corei_local = find_local_asset('flash/ui/spain/swf/coreI.swf')
        self.assertIsNotNone(corei_local)
        self.assertTrue(os.path.isfile(corei_local))
        self.assertTrue(corei_local.lower().endswith('corei.swf'))

        # PlayerTip SWF aliases
        tip_local = find_local_asset('ui/zh_cn/swf/playerTip.swf')
        self.assertIsNotNone(tip_local)
        self.assertTrue(os.path.isfile(tip_local))
        self.assertTrue(tip_local.lower().endswith('playertip.swf'))


class PlayerMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.movies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'param' and attrs.get('name') == 'movie':
            self.movies.append(attrs['value'])
        elif tag == 'embed':
            self.movies.append(attrs['src'])


class TestStartupHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), DDTLocalHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get(self, path):
        with urllib.request.urlopen(self.base_url + path, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return response.read()

    @patch('ddt_local_cdn.fetch_upstream_asset', side_effect=AssertionError('Startup must use local assets'))
    def test_existing_player_uses_normal_loader_offline(self, upstream):
        markup = PlayerMarkup()
        markup.feed(self.get('/player.html').decode('utf-8'))
        self.assertEqual(markup.movies, ['/flash/DDT_Loading.swf'] * 2)

        # Check the real SWF entry class, not just a 200 response or extension.
        movie = self.get(markup.movies[0])
        self.assertIn(movie[:3], (b'CWS', b'FWS'))
        raw = movie[:8] + zlib.decompress(movie[8:]) if movie[:3] == b'CWS' else movie
        self.assertEqual(len(raw), struct.unpack_from('<I', raw, 4)[0])
        offset = 8 + (5 + 4 * (raw[8] >> 3) + 7) // 8 + 4
        document_class = None
        while offset < len(raw):
            tag = struct.unpack_from('<H', raw, offset)[0]
            offset += 2
            kind, size = tag >> 6, tag & 63
            if size == 63:
                size = struct.unpack_from('<I', raw, offset)[0]
                offset += 4
            if kind == 76:  # SymbolClass: symbol ID 0 is the document class.
                data = raw[offset:offset + size]
                pos = 2
                for _ in range(struct.unpack_from('<H', data)[0]):
                    symbol_id = struct.unpack_from('<H', data, pos)[0]
                    pos += 2
                    end = data.index(0, pos)
                    if symbol_id == 0:
                        document_class = data[pos:end].decode('utf-8')
                    pos = end + 1
            offset += size
        self.assertEqual(document_class, 'DDT_Loading')

        config = ET.fromstring(self.get('/config.xml?rnd=0.1'))
        language = config.find('./config/LANGUAGE')
        self.assertEqual(language.get('value'), 'portugal')
        self.assertEqual(config.find('./config/DISTRIBUTION').get('value'), 'local')
        self.assertIn(f':{self.server.server_port}/flash/', config.find('./config/FLASHSITE').get('value'))

        profile = ET.fromstring(self.get('/request/LoginSelectList.ashx?username=Admin')).find('Item')
        self.assertEqual(profile.get('NickName'), 'Admin')
        # Loading.swf / DDT_Loading enter the trainer when IsFirst <= 1,
        # regardless of the character's Grade or TRAINER_STANDALONE setting.
        self.assertGreater(int(profile.get('IsFirst')), 1)
        # DateUtils.decodeDated splits on T, then indexes the time portion.
        self.assertRegex(profile.get('LastDate'), r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
        self.assertTrue(self.get('/flash/2.png?lv=-1').startswith(b'CWS'))
        self.assertTrue(self.get('/flash/ui/portugal/xml/xml.png?lv=-1').startswith(b'PK'))
        upstream.assert_not_called()

    def test_real_tables_decode_with_the_runtime_loader(self):
        for path in sorted(Path(WWW_DIR, 'request').glob('*.xml')):
            if not is_compressed_text_file('/request/' + path.name):
                continue
            with self.subTest(table=path.name):
                body = self.get('/request/' + path.name + '?rnd=0.1')
                decoded = decode_client_table(body)
                self.assertEqual(ET.fromstring(decoded).tag, ET.parse(path).getroot().tag)

    def test_server_list_stays_plain_with_fallback_ports(self):
        with patch.dict(os.environ, {'DDT_GAME_PORT': '9299'}):
            server_list = ET.fromstring(self.get('/request/ServerList.ashx?rnd=0.1'))
        self.assertEqual(server_list.find('Item').get('IP'), '127.0.0.1')
        self.assertEqual(server_list.find('Item').get('Port'), '9299')

    def test_map_server_list_is_a_compressed_table_not_a_login_endpoint(self):
        # A substring match on "serverlist" used to redirect this request to
        # the plain channel list, causing Flash Error #2058 during startup.
        decoded = decode_client_table(self.get('/request/mapserverlist.xml?rnd=0.1'))
        self.assertEqual(decoded, Path(WWW_DIR, 'request', 'MapServerList.xml').read_bytes())
        server = ET.fromstring(decoded).find('Item')
        self.assertEqual(server.get('ServerID'), '1')
        self.assertEqual([int(value) for value in server.get('OpenMap').split(',')], [1, 2, 3, 4])
        self.assertIsNone(server.get('Port'))

    def test_localized_tables_use_exported_data(self):
        for name in ('TemplateAllList.xml', 'LoadItemsCategory.xml', 'QuestList.xml'):
            with self.subTest(table=name):
                decoded = decode_client_table(self.get('/request/portugal/' + name.lower() + '?rnd=0.1'))
                self.assertEqual(decoded, Path(WWW_DIR, 'request', name).read_bytes())

    def test_text_loader_tables_remain_plain_xml(self):
        for path in ('portugal/PetTemplateInfo.xml', 'portugal/PetSkillInfo.xml',
                     'PetConfigInfo.xml', 'PetLevelInfo.xml', 'TotemHonorTemplate.xml'):
            with self.subTest(table=path):
                body = self.get('/request/' + path)
                self.assertTrue(body.startswith(b'<?xml'))
                self.assertEqual(ET.fromstring(body).tag, 'Result')

    def test_startup_currency_template_exists(self):
        decoded = decode_client_table(self.get('/request/portugal/TemplateAllList.xml'))
        templates = ET.fromstring(decoded).find('ItemTemplate')
        currency = templates.find("Item[@TemplateID='-4300']")
        self.assertIsNotNone(currency, 'FirstRechargeManager requires GOLDENGRAINS_ID during startup')
        self.assertTrue(currency.get('Name'))

    def test_http_login_includes_the_player_record(self):
        # LoginAnalyzer reads the first Item before it opens the TCP session.
        result = ET.fromstring(self.get('/request/Login.ashx?ip=127.0.0.1'))
        player = result.find('Item')
        self.assertEqual(result.get('value'), 'true')
        self.assertIsNotNone(player)
        self.assertEqual(player.get('NickName'), 'Admin')
        self.assertEqual(player.get('IsCreatedMarryRoom'), 'false')


if __name__ == '__main__':
    unittest.main()
