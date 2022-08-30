from flask import g

class Common:

    def __init__(self, current_user):
        if current_user.is_authenticated:
            self.cu = current_user
        else:
            self.cu = None

    def current_user(self):
        return self.cu

    def get_announcement(self):
        if self.cu is None:
            return (0,0)
        else:
            g.cur.execute('SELECT COUNT(*), MAX(id) FROM announcement WHERE creation_time > (SELECT last_login_time FROM users WHERE id=%s);', (self.cu.get_id(),))
            return g.cur.fetchone()
