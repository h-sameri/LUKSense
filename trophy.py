from flask import g


def evaluate_alturist_cron(user_id, cur):
    cur.execute('SELECT COUNT(*) FROM nft WHERE price = 0 AND owner=%s AND status=%s AND id IN (SELECT nft_id FROM file_nft);',
                (user_id, 'ACTIVE'))
    nft_count = cur.fetchone()[0]
    if nft_count >= 1000:
        return 3
    elif nft_count >= 100:
        return 2
    elif nft_count >= 10:
        return 1
    else:
        return 0


# def evaluate_obstetrician_cron(user_id, cur):
#    return 0


def evaluate_pundit_cron(user_id, cur):
    cur.execute('SELECT COUNT(*) FROM purchase WHERE (honesty_feedback > 0 OR quality_feedback > 0) AND user_id=%s;',
                (user_id,))
    vote_count = cur.fetchone()[0]
    if vote_count >= 10000:
        return 3
    elif vote_count >= 1000:
        return 2
    elif vote_count >= 100:
        return 1
    else:
        return 0


def set_trophy_cron(user_id, name, level, cur):
    if level > 0:
        cur.execute('INSERT INTO trophy (user_id, name, level) VALUES (%s, %s, %s) ON CONFLICT (user_id, name) DO UPDATE SET level=%s;',
                (user_id, name, level, level))


def get_trophies(user_id):
    g.cur.execute('SELECT name, level FROM trophy WHERE user_id=%s;', (user_id,))
    return Trophy(g.cur.fetchall())


class TrophyStat:

    def __init__(self,
                 all_trophies):
        self.alturist_bronze = 0
        self.alturist_silver = 0
        self.alturist_gold = 0
        self.pundit_bronze = 0
        self.pundit_silver = 0
        self.pundit_gold = 0
        for trophy_stat in all_trophies:
            if trophy_stat[0] == 'Alturist':
                if trophy_stat[1] == 1:
                    self.alturist_bronze = trophy_stat[2]
                elif trophy_stat[1] == 2:
                    self.alturist_silver = trophy_stat[2]
                elif trophy_stat[1] == 3:
                    self.alturist_gold = trophy_stat[2]
            elif trophy_stat[0] == 'Pundit':
                if trophy_stat[1] == 1:
                    self.pundit_bronze = trophy_stat[2]
                elif trophy_stat[1] == 2:
                    self.pundit_silver = trophy_stat[2]
                elif trophy_stat[1] == 3:
                    self.pundit_gold = trophy_stat[2]

    def get_alturist_bronze(self):
        if self.alturist_bronze is not None:
            return self.alturist_bronze
        else:
            return 0

    def get_alturist_silver(self):
        if self.alturist_silver is not None:
            return self.alturist_silver
        else:
            return 0

    def get_alturist_gold(self):
        if self.alturist_gold is not None:
            return self.alturist_gold
        else:
            return 0

    def get_pundit_bronze(self):
        if self.pundit_bronze is not None:
            return self.pundit_bronze
        else:
            return 0

    def get_pundit_silver(self):
        if self.pundit_silver is not None:
            return self.pundit_silver
        else:
            return 0

    def get_pundit_gold(self):
        if self.pundit_gold is not None:
            return self.pundit_gold
        else:
            return 0


class Trophy:

    def __init__(self,
                all_trophies):
        self.bronze = []
        self.silver = []
        self.gold = []
        for trophy in all_trophies:
            if trophy[1] == 1:
                self.bronze.append(trophy[0])
            elif trophy[1] == 2:
                self.silver.append(trophy[0])
            elif trophy[1] == 3:
                self.gold.append(trophy[0])

    def get_bronze(self):
        return self.bronze

    def get_silver(self):
        return self.silver

    def get_gold(self):
        return self.gold
