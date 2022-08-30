import urllib3
import json


class Lukso:

    def __init__(self, port):
        self.http = urllib3.PoolManager()
        self.address = '127.0.0.1:' + str(port)

    def fetch_up(self, up):
        res = self.http.request('GET', self.address + '/fetch_up?up=' + up)
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def get_metadata(self, lsp7):
        res = self.http.request('GET', self.address + '/get_metadata?lsp7=' + lsp7)
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def upload_metadata(self, name, url, description):
        data = {
            'name': name,
            'url': url,
            'description': description
        }
        res = self.http.request('POST', self.address + '/upload_metadata',
                                headers={'Content-Type': 'application/json'},
                                body=json.dumps(data).encode('utf-8'))
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def upload_metadata_json(self, meta):
        data = {
            'meta': meta
        }
        res = self.http.request('POST', self.address + '/upload_metadata_json',
                                headers={'Content-Type': 'application/json'},
                                body=json.dumps(data).encode('utf-8'))
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def change_metadata(self):
        return

    def new_lsp7(self, name, symbol, creator, meta):
        data = {
            'name': name,
            'symbol': symbol,
            'creator': creator,
            'meta': meta
        }
        res = self.http.request('POST', self.address + '/new_lsp7',
                                headers={'Content-Type': 'application/json'},
                                body=json.dumps(data).encode('utf-8'))
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def mint_lsp7(self, up, lsp7):
        res = self.http.request('GET', self.address + '/mint_lsp7?lsp7=' + lsp7 + '&up=' + up)
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def mint_lsp8(self, up, lsp7):
        res = self.http.request('GET', self.address + '/mint_lsp8?lsp7=' + lsp7 + '&up=' + up)
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

