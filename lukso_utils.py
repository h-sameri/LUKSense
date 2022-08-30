base_api = "http://localhost:3000"
import requests
import json


def check_signature(signature, address) -> bool:
    url = base_api + "/is_signature_valid"
    payload = json.dumps({
        "signature": signature,
        "address": address
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json().get('is_valid', False)


def get_sign_message(address):
    url = base_api + "/get_message?up=" + address
    response = requests.request("GET", url)
    return response.json()


def get_user_profile(address):
    url = base_api + "/fetch_up?up=" + address
    response = requests.request("GET", url)
    return response.json()

