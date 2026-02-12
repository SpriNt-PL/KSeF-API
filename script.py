import requests
import os
from dotenv import load_dotenv

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

def inicjacja_uwierzytelniania():
    challange_url = f"{PROD_URL}/auth/challenge"

    response = requests.post(challange_url)
    response.raise_for_status()

    print(f"Response code: {response.status_code}")

    challenge_data = response.json()
    challenge_str = challenge_data['challenge']
    timestamp = challenge_data['timestamp']

    print(f"Sukces! Otrzymano challenge: {challenge_str}")
    print(f"Timestamp serwera: {timestamp}")

    return challenge_str, timestamp

def uwierzytelnianie_z_tokenem(nip, token, challange, timestamp):

    url = "https://api.ksef.mf.gov.pl/v2/auth/ksef-token"

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

    load_dotenv()

    nip = os.getenv("NIP")
    token = os.getenv("TOKEN") 
    print(f"\nNIP = {nip}, TOKEN = {token}")

    print("2. Uwierzytelnianie tokenem")
    uwierzytelnianie_z_tokenem(nip, token, challange, timestamp)