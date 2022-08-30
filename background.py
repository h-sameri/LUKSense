import psycopg2
from psycopg2.extras import DictCursor
from elastic import Elastic
from config import Config
import security, nft_util
import os, datetime, time

# env = {'DEV', 'LIVE'}
luksense_env = 'DEV'

if luksense_env == 'LIVE':
    db_url = 'postgres://127.0.0.1:5432/mainnet'
else:
    db_url = 'postgres://127.0.0.1:5432/testnet'

conf = Config(luksense_env, db_url)
index_name = conf.get('index_name')


def auto_poster(base_path, nft_id):
    upload_dir = os.path.join(conf.get('storage_location'),
                              datetime.date.today().strftime('%y%m'),
                              datetime.date.today().strftime('%d'))
    print(upload_dir)
    if not os.path.isdir(upload_dir):
        os.makedirs(upload_dir)
    file_list = os.listdir(base_path)
    print(file_list)
    owner = nft_util.get_nft_owner_cron(nft_id, cur)
    print(owner)
    if security.can_upload_file_cron(owner, nft_id, len(file_list), cur):
        for file in file_list:
            source_path = os.path.join(base_path, file)
            print(source_path)
            res = nft_util.upload_and_process_path_cron(source_path, upload_dir, nft_id, es, cur)
            print(res)
            s = os.path.getsize(source_path)/(1024*1024)
            print(s)
            time.sleep(s)
    else:
        print('cannot upload')


conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
conn.autocommit = True
cur = conn.cursor()
es = Elastic(index_name=index_name)

# RUN HERE
auto_poster('/user/share/luksense/auto', 0)

cur.close()
conn.close()

print('CRON FINISHED')

