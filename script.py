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

def uwierzytelnianie_z_tokenem(challange, timestamp):
    return

if __name__ == "__main__":
    print("Program wystartował.")
    challange, timestamp = inicjacja_uwierzytelniania()

    load_dotenv()

    nip = os.getenv("NIP")
    print(nip)