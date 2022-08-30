import urllib3
import json


class Web3Storage:

    def __init__(self):
        self.http = urllib3.PoolManager()

    def upload_single(self, file_name, file_path):
        headers = {
            "Content-Type": "multipart/form-data"
        }
        with open(file_path) as fp:
            file_data = fp.read()
        res = self.http.request(
            "POST",
            "http://127.0.0.1:9595/upload",
            headers=headers,
            fields={
                "upload": (file_name, file_data)
            }
        )
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def get_status(self, cid):
        res = self.http.request('GET',
                                'http://127.0.0.1:9595/cid/' + cid + '/status')
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')
