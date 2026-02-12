import requests
import os
import base64
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

def inicjacja_uwierzytelniania():
    url = f"{PROD_URL}/auth/challenge"

    response = requests.post(url)
    response.raise_for_status()

    print(f"Response code: {response.status_code}")

    challenge_data = response.json()
    challenge_str = challenge_data['challenge']
    timestamp = challenge_data['timestampMs']

    print(f"Sukces! Otrzymano challenge: {challenge_str}")
    print(f"Timestamp serwera: {timestamp}")

    return challenge_str, timestamp


def pobieranie_certyfikatow():
    
    url = f"{PROD_URL}/security/public-key-certificates"

    response = requests.get(url)

    response_data = response.json()
    response_data = response_data[0]

    return response_data['certificate']


def szyfrowanie_encryptedToken(token, timestamp, certificate):

    plain_text = f"{token}|{timestamp}".encode('utf-8')

    cert_bytes = base64.b64decode(certificate)
    cert_obj = x509.load_der_x509_certificate(cert_bytes)
    public_key = cert_obj.public_key()

    encrypted = public_key.encrypt(plain_text, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    ))

    encrypted_token_b64 = base64.b64encode(encrypted).decode('utf-8')
    
    return encrypted_token_b64


def uwierzytelnianie_z_tokenem(nip, challange, encrypted_token):

    url = f"{PROD_URL}/auth/ksef-token"

    query_payload = {
        "challenge": f"{challange}",
        "contextIdentifier": {
            "type": "Nip",
            "value": f"{nip}"
        },
        "encryptedToken": f"{encrypted_token}"
    }

    response = requests.post(url, json=query_payload)
    print(f"Response code: {response.status_code}")

    response_data = response.json()
    print(response_data)


    if response.status_code != 202:
        print(response_data)


if __name__ == "__main__":
    print("Program wystartował.\n")
    
    print("1. Inicjacja uwierzytelniania")
    challange, timestamp = inicjacja_uwierzytelniania()

    print("\n2. Pobieranie ")
    certificate = pobieranie_certyfikatow()

    load_dotenv()

    nip = os.getenv("NIP")
    token = os.getenv("TOKEN") 

    print(f"\n3. Uwierzytelnianie tokenem (NIP = {nip} oraz TOKEN = {token})")
    encrypted_token = szyfrowanie_encryptedToken(token, timestamp, certificate)
    uwierzytelnianie_z_tokenem(nip, challange, encrypted_token)