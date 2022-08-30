import psycopg2
from psycopg2.extras import DictCursor
from elastic import Elastic
from nft_doc import NFTDoc
from feedback import Feedback
from config import Config
import file_util, nft_util, trophy
import math, time

# env = {'DEV', 'LIVE'}
luksense_env = 'DEV'

if luksense_env == 'LIVE':
    db_url = 'postgres://127.0.0.1:5432/mainnet'
else:
    db_url = 'postgres://127.0.0.1:5432/testnet'

conf = Config(luksense_env, db_url)
index_name = conf.get('index_name')


# type_general | type_mime | type_detailed
def set_file_types():
    cur.execute('SELECT hash, path FROM file;')
    files = cur.fetchall()
    for file in files:
        file_type = file_util.magic_from_file(file[1])
        cur.execute('UPDATE file SET type_general=%s WHERE hash=%s;',
                    (file_type, file[0]))
    print(len(files))


def assign_trophy():
    cur.execute("SELECT id FROM users WHERE prestige > 0;")
    users = cur.fetchall()
    for user in users:
        trophy.set_trophy_cron(user[0],
                               'Alturist',
                               trophy.evaluate_alturist_cron(user[0], cur),
                               cur)
        trophy.set_trophy_cron(user[0],
                               'Pundit',
                               trophy.evaluate_pundit_cron(user[0], cur),
                               cur)


def assign_prestige():
    penalty_dic = {} # TODO use it in future
    ban_list = []
    epsilon = 0.01

    cur.execute('SELECT DISTINCT owner FROM nft;')
    users = cur.fetchall()

    user_dic = {}
    for user in users:
        cur.execute('SELECT price, quality_feedback, honesty_feedback FROM purchase WHERE nft_id IN (SELECT id FROM nft WHERE owner=%s) AND (honesty_feedback!=%s OR quality_feedback!=%s);',
                    (user[0], -1, -1))
        rows = cur.fetchall()
        prestige_raw = 0
        for row in rows:
            if row[0] == 0:
                nft_price = epsilon
            else:
                nft_price = row[0]
            if row[1] > -1:
                quality_feedback = row[1]
            else:
                quality_feedback = 1
            if row[2] > -1:
                honesty_feedback = row[2]
            else:
                honesty_feedback = 3
            prestige_raw += math.sqrt(nft_price)*((quality_feedback-1)/2) + math.sqrt(nft_price)*(honesty_feedback-3)
        user_dic[user[0]] = prestige_raw

    for user in ban_list:
        user_dic[user] = -1

    max_raw_prestige = float('-inf')
    for key, value in user_dic.items():
        if value > max_raw_prestige:
            max_raw_prestige = value

    threshold = 13
    denominator = int(max_raw_prestige/threshold)
    print(max_raw_prestige)
    print(denominator)
    if denominator < 1:
        denominator = 1

    for key, value in user_dic.items():
        if value > 0:
            prestige = int(value/denominator)+1
            if prestige > 13:
                prestige = 13
            cur.execute('UPDATE users SET prestige=%s WHERE id=%s;',
                        (prestige, key))
        elif value == 0:
            cur.execute('UPDATE users SET prestige=%s WHERE id=%s;',
                        (0, key))
        else:
            prestige = int(value/denominator)-1
            if prestige < -13:
                prestige = -13
            cur.execute('UPDATE users SET prestige=%s WHERE id=%s;',
                        (prestige, key))


def sync_all_nft_docs_with_elasticsearch():
    chunk = 500
    offset = 0
    nfts_left = True
    while nfts_left:
        cur.execute('SELECT id, owner, name, description, price, status, creation_time FROM nft WHERE status!=%s ORDER BY id OFFSET %s LIMIT %s;',
                    ('PREVIEW', offset, chunk))
        offset += chunk
        nfts = cur.fetchall()
        if len(nfts) == 0:
            nfts_left = False
        for nft in nfts:
            update_time = nft_util.get_last_update_time_cron(nft[0], cur)
            if update_time is None:
                update_time = nft[6]
            nft_doc = NFTDoc(id=nft[0],
                             owner=nft[1],
                             name=nft[2],
                             description=nft[3],
                             price=nft[4],
                             status=nft[5],
                             creation_time=nft[6],
                             preview_of=None,
                             update_time=update_time)
            nft_doc.set_files(nft_util.get_files_cron(nft[0], cur))
            preview_id = nft_util.get_preview_id_cron(nft[0], cur)
            if preview_id is not None:
                nft_doc.set_preview_files(nft_util.get_files_cron(preview_id, cur))
            feedback = Feedback()
            feedback.calculate_feedback_cron(nft[0], cur)
            nft_doc.set_feedback(feedback)
            print(nft[0])
            es.index(body=nft_doc.get_nft(), id=nft_doc.id)


def sync_all_nft_previews_with_elasticsearch():
    chunk = 500
    offset = 0
    nfts_left = True
    while nfts_left:
        cur.execute('SELECT id FROM nft WHERE status!=%s ORDER BY id OFFSET %s LIMIT %s;',
                    ('PREVIEW', offset, chunk))
        offset += chunk
        nfts = cur.fetchall()
        if len(nfts) == 0:
            nfts_left = False
        for nft in nfts:
            update_time = nft_util.get_last_update_time_cron(nft[0], cur)
            if update_time is None:
                update_time = time.time()
            nft_doc = NFTDoc(id=nft[0], update_time=update_time)
            preview_id = nft_util.get_preview_id_cron(nft[0], cur)
            if preview_id is not None:
                nft_doc.set_preview_files(nft_util.get_files_cron(preview_id, cur))
                print(nft[0])
                try:
                    es.update(body=nft_doc.upload_preview_files_cron(), id=nft_doc.id)
                except:
                    print('empty preview')


def test_case_1():
    user_list=['user1', 'user2']
    cur.execute("SELECT nft_id, honesty_feedback, quality_feedback FROM purchase WHERE user_id='userX' AND honesty_feedback > -1 AND quality_feedback > -1 ORDER BY nft_id DESC;")
    nfts = cur.fetchall()
    print(len(nfts))
    for user in user_list:
        cur.execute("SELECT balance FROM users WHERE id=%s", (user,))
        balance = cur.fetchone()[0]
        cur.execute("SELECT nft_id FROM purchase WHERE user_id=%s;", (user,))
        user_nfts = cur.fetchall()
        for nft in nfts:
            purchased = False
            for pb in user_nfts:
                if nft[0] == pb[0]:
                    purchased = True
                    break
            if not purchased:
                cur.execute("SELECT price, owner FROM nft WHERE id=%s;", (nft[0],))
                fetched_nft = cur.fetchone()
                price = fetched_nft[0]
                owner = fetched_nft[1]
                if owner == user:
                    print('serious problem')
                elif balance/1000 > price:
                    balance = balance - price
                    cur.execute('UPDATE users SET balance=balance-%s WHERE id=%s;',
                                  (price, user))
                    cur.execute('INSERT INTO purchase (user_id, nft_id, price, honesty_feedback, quality_feedback) VALUES (%s, %s, %s, %s, %s);',
                                  (user, nft[0], price, nft[1], nft[2]))
                    cur.execute('UPDATE users SET balance=balance+%s WHERE id=%s;',
                                  (price, owner))
                    print(user + ' with balance=' + str(balance) + ' purchased ' + str(nft[0]) + ' for ' + str(price) + '.')
    for nft in nfts:
        if nft[0] > 8653:
            continue
        update_time = nft_util.get_last_update_time_cron(nft[0], cur)
        if update_time is None:
            update_time = time.time()
        fb = Feedback()
        fb.calculate_feedback_cron(nft[0], cur)
        nft_doc = NFTDoc(id=id, update_time=update_time)
        nft_doc.set_feedback(fb)
        try:
            es.update(body=nft_doc.rate_nft(), id=nft[0])
        except Exception as e:
            print(e)
        print(str(nft[0]) + ' updated.')
    return True


conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
conn.autocommit = True
cur = conn.cursor()
es = Elastic(index_name=index_name)

assign_prestige()
assign_trophy()

cur.close()
conn.close()

print('CRON FINISHED')

