from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import sha256


def get_hash(password):  # deprecated
    full_hash = generate_password_hash(password=password,
                                       method='pbkdf2:sha256:666666',
                                       salt_length=13)
    hash = full_hash.split('$')
    return hash[1] + hash[2]


def check_hash(hash, password):
    full_hash = 'pbkdf2:sha256:666666$' + hash[:13] + '$' + hash[13:]
    return check_password_hash(pwhash=full_hash, password=password)


def sha256_hash(data):
    return sha256(data).hexdigest()
