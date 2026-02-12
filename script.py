import requests
import os
from dotenv import load_dotenv

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

def inicjacja_uwierzytelniania():
    url = f"{PROD_URL}/auth/challenge"

    response = requests.post(url)
    response.raise_for_status()

    print(f"Response code: {response.status_code}")

    challenge_data = response.json()
    challenge_str = challenge_data['challenge']
    timestamp = challenge_data['timestamp']

    print(f"Sukces! Otrzymano challenge: {challenge_str}")
    print(f"Timestamp serwera: {timestamp}")

    return challenge_str, timestamp


def pobieranie_certyfikatow():
    
    url = f"{PROD_URL}/security/public-key-certificates"

    response = requests.get(url)

    response_data = response.json()
    response_data = response_data[0]

    return response_data['certificate']


def uwierzytelnianie_z_tokenem(nip, token, challange, timestamp):

    url = f"{PROD_URL}/auth/ksef-token"

    query_payload = {
        "challenge": f"{challange}",
        "contextIdentifier": {
            "type": "Nip",
            "value": f"{nip}"
        },
        "encryptedToken": f"{token}|{timestamp}"
    }

    response = requests.post(url, json=query_payload)
    print(f"Response code: {response.status_code}")

    if response.status_code != 202:
        response_data = response.json()

        print(response_data)


if __name__ == "__main__":
    print("Program wystartował.\n")
    
    print("1. Inicjacja uwierzytelniania")
    challange, timestamp = inicjacja_uwierzytelniania()

    print("\n2. Pobieranie ")
    pobieranie_certyfikatow()

    load_dotenv()

    nip = os.getenv("NIP")
    token = os.getenv("TOKEN") 

    print(f"\n3. Uwierzytelnianie tokenem (NIP = {nip} oraz TOKEN = {token})")
    uwierzytelnianie_z_tokenem(nip, token, challange, timestamp)