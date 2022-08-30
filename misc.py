from flask import g


def get_misc(user, custom_from=1, row_per_page=69):
    g.cur.execute('SELECT transaction_time, transaction_type, amount, payload FROM misc_tx WHERE user_id=%s LIMIT %s OFFSET %s;',
                  (user, row_per_page, (custom_from-1)*row_per_page))
    return g.cur.fetchall()


def apply_misc(user, transaction_type, amount, payload):
    apply_misc_cron(user, transaction_type, amount, payload, g.cur)


def apply_misc_cron(user, transaction_type, amount, payload, cur):
    if amount == 0:
        return False
    elif amount < 0:
        try:
            cur.execute('SELECT balance FROM users WHERE id=%s', (user,))
            balance = cur.fetchone()[0]
            if balance < -amount:
                return False
        except:
            return False
    ###
    cur.execute('INSERT INTO misc_tx (user_id, transaction_type, amount, payload) VALUES (%s, %s, %s, %s);',
                (user, transaction_type, amount, payload))
    cur.execute('UPDATE users SET balance=balance+%s WHERE id=%s',
                (amount, user))
    return True
