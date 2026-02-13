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

    print(f"Certyfikat ważny do {response_data['validTo']}")

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

    if response.status_code == 202:
        response_data = response.json()
        print(f"Token ważny do: {response_data['authenticationToken']['validUntil']}")
        return response_data['authenticationToken']['token'], response_data['referenceNumber']


    else:
        print(response_data)

        return None
    

def status_uwierzytelniania(session_token, reference_number):

    url = f"{PROD_URL}/auth/{reference_number}"

    headers = {
        "Authorization": f"Bearer {session_token}"
    }

    response = requests.get(url, headers=headers)

    print(f"Response code: {response.status_code}")

    if response.status_code == 200:
        response_data = response.json()

        print(response_data['authenticationMethod'])
        print(response_data['status']['code'])
        print(response_data['status']['description'])


def pobieranie_tokenow_dostepowych(session_token):

    url = f"{PROD_URL}/auth/token/redeem"

    headers = {
        "Authorization": f"Bearer {session_token}"
    }

    response = requests.post(url, headers=headers)

    print(f"Response code: {response.status_code}")

    if response.status_code == 200:
        response_data = response.json()

        print(f"Access token ważny do: {response_data['accessToken']['validUntil']}")
        print(f"Refresh token ważny do: {response_data['refreshToken']['validUntil']}")

        return response_data['accessToken']['token'], response_data['refreshToken']['token']


def szyfrowanie_eksportu(certificate):
    symmetric_key = os.urandom(32)

    initialization_vector = os.urandom(16)

    cert_bytes = base64.b64decode(certificate)
    cert_obj = x509.load_der_x509_certificate(cert_bytes)
    public_key = cert_obj.public_key()

    encrypted_key = public_key.encrypt(symmetric_key, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    ))

    encrypted_key_b64 = base64.b64encode(encrypted_key).decode('utf-8')
    initialization_vector_b64 = base64.b64encode(initialization_vector).decode('utf-8')

    return encrypted_key_b64, initialization_vector_b64, symmetric_key, initialization_vector


def eksport_faktur(encrypted_key_b64, initialization_vector_b64, access_token):

    url = f"{PROD_URL}/invoices/exports"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    query_payload = {
        "encryption": {
            "encryptedSymmetricKey": f"{encrypted_key_b64}",
            "initializationVector": f"{initialization_vector_b64}"
        },
        "filters": {
            "subjectType": "Subject2", 
            "dateRange": {
                "dateType": "Invoicing",
                "from": "2026-02-01T00:00:00Z",
                #"to": "2026-02-13T23:59:59Z"
            }
        }
    }

    response = requests.post(url, headers=headers, json=query_payload)

    print(f"Response code: {response.status_code}")

    if response.status_code == 201:
        response_data = response.json()

        return response_data['referenceNumber']
    else:
        return None


def statusu_eksportu(reference_number, access_token):

    url = f"{PROD_URL}/invoices/exports/{reference_number}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    print(f"Response code: {response.status_code}")

    if response.status_code == 200:

        response_data = response.json()

        print(response_data['status']['code'])
        print(response_data['status']['description'])

        if response_data['status']['code'] == 200:
            print(response_data['package']['invoiceCount'])
            print(response_data['package']['size'])


if __name__ == "__main__":
    print("Program wystartował.\n")
    
    print("1. Inicjacja uwierzytelniania")
    challange, timestamp = inicjacja_uwierzytelniania()

    print("\n2. Pobieranie certyfikatow")
    certificate = pobieranie_certyfikatow()

    load_dotenv()

    nip = os.getenv("NIP")
    token = os.getenv("TOKEN") 

    print(f"\n3. Uwierzytelnianie tokenem (NIP = {nip} oraz TOKEN = {token})")

    encrypted_token = szyfrowanie_encryptedToken(token, timestamp, certificate)
    session_token, reference_number = uwierzytelnianie_z_tokenem(nip, challange, encrypted_token)
    status_uwierzytelniania(session_token, reference_number)

    print("\n4. Pobieranie tokenów dostępowych")

    access_token, refresh_token = pobieranie_tokenow_dostepowych(session_token)

    print("\n4. Pobieranie faktur")

    encrypted_key_b64, initialization_vector_b64, symmetric_key, initialization_vector = szyfrowanie_eksportu(certificate)
    package_reference_number = eksport_faktur(encrypted_key_b64, initialization_vector_b64, access_token)

    statusu_eksportu(package_reference_number, access_token)
