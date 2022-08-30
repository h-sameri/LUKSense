from flask import g

reserved_usernames = []

def nft_name_is_not_duplicate(user_id, nft_name, nft_id):
    g.cur.execute('SELECT id FROM nft WHERE owner=%s AND name=%s;',
                  (user_id, nft_name))
    dup_id = g.cur.fetchone()
    print(dup_id)
    if dup_id is None:
        return True
    else:
        if str(dup_id[0]) == nft_id:
            return True
        else:
            return False


def can_create_user(user_id):
    if user_id in reserved_usernames:
        return False
    else:
        for ch in user_id:
            if ch not in 'abcdefghijklmnopqrstuvwxyz_0123456789':
                return False
        return True


def rename_file_if_needed(secure_name):
    if len(secure_name) == 0:
        return 'nameless'
    elif '.' not in secure_name:
        return 'unknown.' + secure_name.lower()
    else:
        # name, extension = os.path.splitext(secure_name)
        # return name + extension.lower()
        return secure_name.lower()


def can_upload_file(user_id, nft_id, file_count):
    return can_upload_file_cron(user_id, nft_id, file_count, g.cur)


def can_upload_file_cron(user_id, nft_id, file_count, cur):
    cur.execute('SELECT owner FROM nft WHERE id=%s;', (nft_id,))
    owner = cur.fetchone()
    if owner is None:
        return False
    if len(owner) < 1:
        return False
    if owner[0] != user_id:
        return False
    cur.execute('SELECT COUNT(*) FROM file_nft WHERE nft_id=%s;', (nft_id,))
    current_count = cur.fetchone()
    if current_count[0] + file_count > 666:
        return False
    else:
        return True


def can_rate_nft(user_id):
    g.cur.execute('SELECT prestige FROM users WHERE id=%s;', (user_id,))
    prestige = g.cur.fetchone()
    if prestige is not None:
        if prestige[0] > 0:
            return True
        else:
            return False
    else:
        return False


def msg_nft_limit(user_id, prestige):
    if prestige < -2:
        year, month, week, day, hour = 2, 1, 1, 1, 1
    elif prestige < -1:
        year, month, week, day, hour = 4, 2, 1, 1, 1
    elif prestige < 0:
        year, month, week, day, hour = 6, 2, 1, 1, 1
    elif prestige < 1:
        year, month, week, day, hour = 20, 12, 4, 2, 1
    elif prestige < 2:
        year, month, week, day, hour = 100, 50, 20, 8, 4
    elif prestige < 3:
        year, month, week, day, hour = 500, 100, 50, 12, 6
    elif prestige < 4:
        year, month, week, day, hour = 1000, 200, 100, 15, 8
    else:
        year, month, week, day, hour = 10000, 1000, 250, 50, 10
    g.cur.execute('SELECT COUNT(*) AS c FROM nft WHERE owner=%s AND status!=%s AND creation_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft WHERE owner=%s AND status!=%s AND creation_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft WHERE owner=%s AND status!=%s AND creation_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft WHERE owner=%s AND status!=%s AND creation_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft WHERE owner=%s AND status!=%s AND creation_time > NOW() - INTERVAL %s ORDER BY c;',
                 (user_id, 'PREVIEW', '1 YEAR', user_id, 'PREVIEW', '1 MONTH', user_id, 'PREVIEW', '1 WEEK', user_id, 'PREVIEW', '1 DAY', user_id, 'PREVIEW', '1 HOUR'))
    counts = g.cur.fetchall()
    if counts[0][0] >= hour:
        return 'Your prestige is ' + str(prestige) + '. You can\'t create more than ' + str(hour) + ' NFT(s) every hour. Earn more prestige or wait.'
    elif counts[1][0] >= day:
        return 'Your prestige is ' + str(prestige) + '. You can\'t create more than ' + str(day) + ' NFT(s) every day. Earn more prestige or wait.'
    elif counts[2][0] >= week:
        return 'Your prestige is ' + str(prestige) + '. You can\'t create more than ' + str(week) + ' NFT(s) every week. Earn more prestige or wait.'
    elif counts[3][0] >= month:
        return 'Your prestige is ' + str(prestige) + '. You can\'t create more than ' + str(month) + ' NFT(s) every month. Earn more prestige or wait.'
    elif counts[4][0] >= year:
        return 'Your prestige is ' + str(prestige) + '. You can\'t create more than ' + str(year) + ' NFT(s) every year. Earn more prestige or wait.'
    else:
        return 'allowed'


def msg_edit_limit(nft_id, prestige):
    if prestige < 0:
        year, month, week, day, hour = 4, 2, 2, 2, 2
    elif prestige < 1:
        year, month, week, day, hour = 8, 4, 2, 2, 2
    elif prestige < 2:
        year, month, week, day, hour = 8, 4, 4, 2, 2
    elif prestige < 3:
        year, month, week, day, hour = 16, 8, 8, 4, 4
    elif prestige < 4:
        year, month, week, day, hour = 32, 16, 8, 4, 4
    else:
        year, month, week, day, hour = 64, 32, 16, 8, 8
    g.cur.execute('SELECT COUNT(*) AS c FROM nft_edit_history WHERE nft_id=%s AND edit_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft_edit_history WHERE nft_id=%s AND edit_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft_edit_history WHERE nft_id=%s AND edit_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft_edit_history WHERE nft_id=%s AND edit_time > NOW() - INTERVAL %s UNION ALL SELECT COUNT(*) AS c FROM nft_edit_history WHERE nft_id=%s AND edit_time > NOW() - INTERVAL %s ORDER BY c;',
                  (nft_id, '1 YEAR', nft_id, '1 MONTH', nft_id, '1 WEEK', nft_id, '1 DAY', nft_id, '1 HOUR'))
    counts = g.cur.fetchall()
    if counts[0][0] >= hour:
        return 'Your prestige is ' + str(prestige) + '. You can\'t edit a nft more than ' + str(hour) + ' times every hour. Earn more prestige or wait.'
    elif counts[1][0] >= day:
        return 'Your prestige is ' + str(prestige) + '. You can\'t edit a nft more than ' + str(day) + ' times every day. Earn more prestige or wait.'
    elif counts[2][0] >= week:
        return 'Your prestige is ' + str(prestige) + '. You can\'t edit a nft more than ' + str(week) + ' times every week. Earn more prestige or wait.'
    elif counts[3][0] >= month:
        return 'Your prestige is ' + str(prestige) + '. You can\'t edit a nft more than ' + str(month) + ' times every month. Earn more prestige or wait.'
    elif counts[4][0] >= year:
        return 'Your prestige is ' + str(prestige) + '. You can\'t edit a nft more than ' + str(year) + ' times every year. Earn more prestige or wait.'
    else:
        return 'allowed'


def msg_price_rational(prestige, price):
    if prestige < -1:
        max_price = 0
    elif prestige < 0:
        max_price = 0
    elif prestige < 1:
        max_price = 0
    elif prestige < 2:
        max_price = 10
    elif prestige < 3:
        max_price = 100
    elif prestige < 10:
        max_price = prestige * 100
    else:
        max_price = 1000
    if price <= max_price:
        return 'rational'
    else:
        return "Your prestige is " + str(prestige) + ". Your NFTs can't be priced over " + str(max_price) + " LYX. Earn more prestige to increase your prices."


def prune_query(raw_query):
    if raw_query is None:
        return None
    else:
        raw_query = raw_query.replace('-', ' ').replace('_', ' ').replace('.', ' ')
        return ''.join(ch for ch in raw_query if ch.isalnum() or ch == ' ')
