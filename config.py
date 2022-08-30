import db
from flask import g


class Config:

    # env = {'DEV', 'LIVE'}
    def __init__(self, env, db_url):
        conn = db.get_connection(db_url)
        cur = conn.cursor()
        cur.execute('SELECT type, key, value FROM config WHERE env=%s;',
                              (env,))
        conf_array = cur.fetchall()
        self.conf_dic = {}
        for conf in conf_array:
            if conf[0] == 'STR':
                self.conf_dic[conf[1]] = conf[2]
            elif conf[0] == 'INT':
                self.conf_dic[conf[1]] = int(conf[2])
        cur.close()
        conn.close()

    def get(self, key):
        return self.conf_dic.get(key)

    def reload(self, env):
        g.cur.execute('SELECT type, key, value FROM config WHERE env=%s;',
                    (env,))
        conf_array = g.cur.fetchall()
        self.conf_dic = {}
        for conf in conf_array:
            if conf[0] == 'STR':
                self.conf_dic[conf[1]] = conf[2]
            elif conf[0] == 'INT':
                self.conf_dic[conf[1]] = int(conf[2])