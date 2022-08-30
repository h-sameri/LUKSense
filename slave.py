from flask import Flask, send_file
from datetime import datetime
from cryptography.fernet import Fernet


fernet = Fernet(b'3kIgMPqxUad9mrG_ctxyniRLnX8sNkGtH9HJ0W3tVNA=')
app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    return 'LUKSense Slave'


@app.route('/get/<token>', methods=['POST', 'GET'])
def get(token):
    # token = user|path|name
    plain_token = str(fernet.decrypt(bytes(token, 'utf-8')), 'utf-8')
    token_parts = plain_token.split('|')
    if len(token_parts) == 3:
        user = token_parts[0]
        path = token_parts[1]
        name = token_parts[2]
        diff = datetime.now().timestamp() - fernet.extract_timestamp(bytes(token, 'utf-8'))
        if diff < 13*60*60:
            return send_file(path, as_attachment=True, attachment_filename=name)
        else:
            error = 'token expired'
    else:
        error = 'tampered token'
    return error


if __name__ == '__main__':
    app.run()
