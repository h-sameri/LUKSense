import re, os
from flask import g
from cryptography.fernet import Fernet
from datetime import datetime
from werkzeug.utils import secure_filename

import security, file_util, crypto
from file import FileNFT, File
from nft_doc import NFTDoc


fernet = Fernet(b'3kIgMPqxUad9mrG_ctxyniRLnX8sNkGtH9HJ0W3tVNA=')


def upload_and_process_path(source_file_path, upload_dir, nft_id, es):
    return upload_and_process_path_cron(source_file_path, upload_dir, nft_id, es, g.cur)


def upload_and_process_path_cron(source_file_path, upload_dir, nft_id, es, cur):
    file_data = open(source_file_path, 'rb').read()
    file_name = os.path.basename(source_file_path)
    return upload_and_process_form_cron(file_data, file_name, upload_dir, nft_id, es, cur)


def upload_and_process_form(file_data, file_name, upload_dir, nft_id, es):
    return upload_and_process_form_cron(file_data, file_name, upload_dir, nft_id, es, g.cur)


def upload_and_process_form_cron(file_data, file_name, upload_dir, nft_id, es, cur):
    file_name = security.rename_file_if_needed(secure_filename(file_name))
    file_path = os.path.join(upload_dir, file_name)
    collision_iter = 0
    has_collision = True
    if int(len(file_data)) == 0:
        return 0
    while has_collision:
        file_hash = crypto.sha256_hash(file_data) \
                    + str(collision_iter).zfill(5)
        cur.execute('SELECT path, size FROM file WHERE hash=%s;', (file_hash,))
        candidate_file = cur.fetchone()
        if candidate_file is None:
            has_collision = False
        else:
            if candidate_file[1] == int(len(file_data)/1000):
                # duplicate file found across the network
                has_collision = False
                collision_iter = -1
            else:
                collision_iter += 1
    filename_iter = 0
    while os.path.exists(file_path):
        file_path = os.path.join(upload_dir, str(filename_iter) + '_' + file_name)
        filename_iter += 1
    if collision_iter != -1:
        type_general = file_util.magic_from_buffer(file_data)
        file_util.save(file_path, file_data)
        cur.execute('INSERT INTO file (hash, path, size, type_general) VALUES (%s, %s, %s, %s);',
                      (file_hash, file_path, int(len(file_data)/1000), type_general))
    cur.execute('SELECT nft_id, file_hash FROM file_nft WHERE nft_id=%s AND file_hash=%s;',
                  (nft_id, file_hash))
    duplicate_file = cur.fetchone()
    if duplicate_file is None:
        cur.execute('INSERT INTO file_nft (nft_id, file_hash, file_name) VALUES (%s, %s, %s);',
                      (nft_id, file_hash, file_name))
        if not is_preview_cron(nft_id, cur):
            nft_doc = NFTDoc(id=nft_id, cur=cur)
            nft_doc.set_files(get_files_cron(nft_id, cur))
            es.update(body=nft_doc.upload_files(), id=nft_id)
        else:
            parent_id = get_id_by_preview_cron(nft_id, cur)
            nft_doc = NFTDoc(id=parent_id, cur=cur)
            nft_doc.set_preview_files(get_files_cron(nft_id, cur))
            es.update(body=nft_doc.upload_preview_files(), id=parent_id)
        return 1
    else:
        return 0


def status_check(status_str):
    if status_str == 'ACTIVE' or status_str == 'DEMOLISHED':
        return status_str
    else:
        return 'ACTIVE'


def strip_whitespace(nft_string):
    new_string = re.sub('\s+', ' ', nft_string).strip()
    if len(new_string) > 0:
        return new_string
    else:
        return None


def honesty_feedback_check(rating_str):
    if rating_str == 'MALICIOUS':
        return 1
    elif rating_str == 'MISLEADING':
        return 2
    elif rating_str == 'GENUINE':
        return 3
    else:
        return -1


def honesty_feedback_reversal(rating_int):
    if rating_int == 1:
        return 'MALICIOUS'
    elif rating_int == 2:
        return 'MISLEADING'
    elif rating_int == 3:
        return 'GENUINE'
    else:
        return 'NONE'


def quality_feedback_check(rating_str):
    if rating_str == '1':
        return 1
    elif rating_str == '2':
        return 2
    elif rating_str == '3':
        return 3
    elif rating_str == '4':
        return 4
    elif rating_str == '5':
        return 5
    else:
        return -1


def quality_feedback_reversal(rating_int):
    if rating_int == 1:
        return '1'
    elif rating_int == 2:
        return '2'
    elif rating_int == 3:
        return '3'
    elif rating_int == 4:
        return '4'
    elif rating_int == 5:
        return '5'
    else:
        return '0'


def get_files(nft_id):
    return get_files_cron(nft_id, g.cur)


def get_files_cron(nft_id, cur):
    cur.execute('SELECT file_nft.file_hash, file_nft.status, file_nft.file_name, file.size, file.creation_time, file.type_general FROM file_nft, file WHERE file_nft.file_hash = file.hash AND file_nft.nft_id=%s ORDER BY file.creation_time DESC;', (nft_id,))
    files = cur.fetchall()
    file_nfts = []
    for file in files:
        file_nft = FileNFT(nft_id=nft_id, file_hash=file[0],
                          status=file[1], file_name=file[2])
        file_nft.set_file(File(file[0], None, file[3], file[5], file[4]))
        file_nfts.append(file_nft)
    return file_nfts


def get_id_by_preview(preview_id):
    get_id_by_preview_cron(preview_id, g.cur)


def get_id_by_preview_cron(preview_id, cur):
    cur.execute('SELECT preview_of FROM nft WHERE id=%s;', (preview_id,))
    preview_of = cur.fetchone()
    if preview_of is not None:
        return preview_of[0]
    else:
        return None


def get_preview_id(nft_id):
    return get_preview_id_cron(nft_id, g.cur)


def get_preview_id_cron(nft_id, cur):
    cur.execute('SELECT id FROM nft WHERE preview_of=%s;', (nft_id,))
    preview_id = cur.fetchone()
    if preview_id is not None:
        return preview_id[0]
    else:
        return None


def is_preview(nft_id):
    is_preview_cron(nft_id, g.cur)


def is_preview_cron(nft_id, cur):
    cur.execute('SELECT status FROM nft WHERE id=%s;', (nft_id,))
    status = cur.fetchone()
    if status[0] == 'PREVIEW':
        return True
    else:
        return False


def get_last_update_time(nft_id):
    return get_last_update_time_cron(nft_id, g.cur)


def get_last_update_time_cron(nft_id, cur):
    cur.execute('SELECT MAX(creation_time) FROM file WHERE hash IN (SELECT file_hash FROM file_nft WHERE nft_id=%s);',
                  (nft_id,))
    update_time = cur.fetchone()
    if update_time is None:
        return None
    else:
        return update_time[0]


def convert_all_number_signs_to_links(description):
    return re.sub(r'\s#0*([\d]+)',
                  r' <a href="/nft/\g<1>">#\g<1></a>',
                  ' ' + description)[1:]


def convert_all_at_signs_to_links(description):
    return re.sub(r'\s@([\w]+)',
                  r' <a href="/user/\g<1>">@\g<1></a>',
                  ' ' + description)[1:]


def apply_markup(description):
    description = convert_all_number_signs_to_links(description)
    description = convert_all_at_signs_to_links(description)
    return description


def generate_token(user, path, name, time):
    # ts = datetime.strptime(time, '%Y-%m-%d %H:%M:%S.%f').timestamp()
    ts = time.timestamp()
    if datetime.now().timestamp() - ts > -666 * 24 * 60 * 60:
        token = fernet.encrypt(bytes(user.get_id()+'|'+path+'|'+name, 'utf-8'))
        return get_slave(user) + '/get/' + str(token, 'utf-8')
    else:
        return None


def get_slave(user):
    slaves = ['http://salve0:port',
              'http://slave1:port']
    if user.get_prestige() > 0:
        return slaves[1]
    else:
        return slaves[0]


def get_nft_owner(nft_id):
    get_nft_owner_cron(nft_id, g.cur)


def get_nft_owner_cron(nft_id, cur):
    try:
        cur.execute('SELECT owner FROM nft WHERE id=%s;', (nft_id,))
        return cur.fetchone()[0]
    except:
        return None
