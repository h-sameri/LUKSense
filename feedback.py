from flask import g
import decimal


class Feedback:

    def __init__(self):
        self.average_quality = 0
        self.quality_count = 0
        self.malicious_count = 0
        self.misleading_count = 0
        self.genuine_count = 0
        self.total_count = 0
        self.malicious_percent = 0
        self.misleading_percent = 0
        self.genuine_percent = 0

    def calculate_feedback(self, nft_id):
        self.calculate_feedback_cron(nft_id, g.cur)

    def calculate_feedback_cron(self, nft_id, cur):
        cur.execute('SELECT AVG(quality_feedback), COUNT(quality_feedback) FROM purchase WHERE quality_feedback!=%s AND nft_id=%s;',
                      (-1, nft_id))
        quality = cur.fetchone()
        if quality is not None:
            self.quality_count = quality[1]
            if self.quality_count > 0:
                self.average_quality = round(decimal.Decimal(quality[0]))
        ###
        cur.execute('SELECT honesty_feedback, COUNT(honesty_feedback) FROM purchase WHERE nft_id=%s GROUP BY honesty_feedback;',
                      (nft_id,))
        honesty = cur.fetchall()
        for row in honesty:
            if row[0] == 1:
                self.malicious_count = row[1]
            elif row[0] == 2:
                self.misleading_count = row[1]
            elif row[0] == 3:
                self.genuine_count = row[1]
        self.total_count = self.malicious_count + self.misleading_count + self.genuine_count
        if self.total_count > 0:
            self.malicious_percent = round(decimal.Decimal((self.malicious_count*100)/self.total_count))
            self.misleading_percent = round(decimal.Decimal((self.misleading_count*100)/self.total_count))
            self.genuine_percent = round(decimal.Decimal((self.genuine_count*100)/self.total_count))
