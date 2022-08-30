from wtforms import ValidationError
import urllib3
import json


class ImageCaptcha:

    def __init__(self):
        self.http = urllib3.PoolManager()

    def get_json(self):
        res = self.http.request('GET', '127.0.0.1:6633/generate_json')
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')

    def check(self, puzzle_id, answer):
        if answer is None or len(answer) == 0:
            return False
        res = self.http.request('GET',
                                '127.0.0.1:6633/check_json/' + puzzle_id + '/' + answer)
        return json.loads(res.data.decode('utf-8'), encoding='utf-8')['pass']

    @staticmethod
    def get_puzzle_id(puzzle):
        return puzzle['id']

    @staticmethod
    def get_question(puzzle):
        return puzzle['question']

    @staticmethod
    def get_options(puzzle):
        choices = []
        options_arr = puzzle['options']
        for option_dic in options_arr:
            choices.append((option_dic['id'],
                            '<img src="data:image/jpeg;charset=utf-8;base64,' + option_dic['base64'] + '"/>'))
        return choices

    def test(self):
        # call generate json
        options = [{
            'base64' : '...',
            'id' : '1'
        }, {
            'base64' : '...',
            'id' : '2'
        }]


class VerySimpleCaptcha:

    @staticmethod
    def get_question():
        return 'Prove you\'re a human: Who invented Bitcoin?'

    @staticmethod
    def check(answer):
        possibilities = ['satoshi nakamoto', 'satoshi', 'nakamoto']
        stopwords = ['mr', 'sir']
        answer = answer.lower()
        for stopword in stopwords:
            answer = answer.replace(stopword, '')
        if answer.strip() not in possibilities:
            raise ValidationError('We don\'t know such a person.')
