from flask import g
from decimal import *
from lukso_utils import get_user_profile


class User:

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_announcement(self):
        g.cur.execute(
            'SELECT COUNT(*), MAX(id) FROM announcement WHERE creation_time > (SELECT last_login_time FROM users WHERE id=%s);',
            (self.id,))
        return g.cur.fetchone()

    def get_nft_revenue(self):
        g.cur.execute(
            'SELECT SUM(price) FROM purchase WHERE user_id!=%s AND nft_id IN (SELECT id FROM nft WHERE owner=%s);',
            (self.id, self.id))
        nft_revenue = g.cur.fetchone()
        if nft_revenue[0] is not None:
            return nft_revenue[0]
        else:
            return 0

    def get_nft_expenditure(self):
        g.cur.execute(
            'SELECT SUM(price) FROM purchase WHERE user_id=%s AND nft_id NOT IN (SELECT id FROM nft WHERE owner=%s);',
            (self.id, self.id))
        nft_expenditure = g.cur.fetchone()
        if nft_expenditure[0] is not None:
            return -nft_expenditure[0]
        else:
            return 0

    def get_id(self):
        return self.id

    def get_balance(self):
        return self.balance


    def get_prestige(self):
        return self.prestige

    def get_name(self):
        return self.name

    def get_profile_image_url(self):
        return f"https://2eff.lukso.dev/ipfs/{self.profile_image_url.replace('ipfs://', '')}"

    def get_description(self):
        return self.description

    def get(self, id):
        g.cur.execute('SELECT id, balance, prestige, creation_time '
                      'FROM users WHERE id = %s;', (id,))
        user = g.cur.fetchone()
        if user is None:
            return None
        else:
            self.id = user[0]
            self.balance = user[1]
            self.prestige = user[2]
            self.creation_date = user[3]
            # Fetch Other UserData Form Universal Profile
            g.cur.execute('SELECT id, name, description, profile_image_url '
                          'FROM universal_profiles WHERE id = %s;', (id,))
            up = g.cur.fetchone()
            self.name = up[1]
            self.description = up[2]
            self.profile_image_url = up[3]
            return self
