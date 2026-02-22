import requests
import os
import base64
import time
import json
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as aes_padding

import constants

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

EXPORT_DELAY_TIME = 5

# Inicjacja uwierzytelniania
def certifying_initiation():
    url = f"{PROD_URL}/auth/challenge"

    response = requests.post(url)
    response.raise_for_status()

    print(f"Response code: {response.status_code}")

    challenge_data = response.json()
    challenge_str = challenge_data['challenge']
    timestamp = challenge_data['timestampMs']

    print(f"Recieved challenge: {challenge_str}")
    print(f"Server timestamp: {timestamp}")

    return challenge_str, timestamp

# Pobieranie certyfikatow
def download_certificates():
    
    url = f"{PROD_URL}/security/public-key-certificates"

    response = requests.get(url)

    response_data = response.json()
    response_data_KsefTokenEncryption = response_data[0]
    response_data_SymmetricKeyEncryption = response_data[1]

    print(f"Certificate 'KsefTokenEncryption' valid until {response_data_KsefTokenEncryption['validTo']}")
    print(f"Certificate 'SymmetricKeyEncryption' valid until {response_data_SymmetricKeyEncryption['validTo']}")

    certificate_KsefTokenEncryption = response_data_KsefTokenEncryption['certificate']
    certificate_SymmetricKeyEncryption = response_data_SymmetricKeyEncryption['certificate']

    return certificate_KsefTokenEncryption, certificate_SymmetricKeyEncryption

# Szyfrowanie encryptedToken
def creating_encryptedToken(token, timestamp, certificate):

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

# Uwierzytelnianie z tokenem
def certifying_with_token(nip, challange, encrypted_token):

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
    

# Status uwierzytelniania
def certifying_status(session_token, reference_number):

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


# Pobieranie tokenów dostępowych
def download_access_tokens(session_token):

    url = f"{PROD_URL}/auth/token/redeem"

    headers = {
        "Authorization": f"Bearer {session_token}"
    }

    response = requests.post(url, headers=headers)

    print(f"Response code: {response.status_code}")

    if response.status_code == 200:
        response_data = response.json()

        print(f"Access token valid until: {response_data['accessToken']['validUntil']}")
        print(f"Refresh token valid until: {response_data['refreshToken']['validUntil']}")

        return response_data['accessToken']['token'], response_data['refreshToken']['token']


# Szyfrowanie eksportu
def encrypt_export(certificate):
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


# Eksport faktur
def invoice_export(encrypted_key_b64, initialization_vector_b64, access_token, date_from):

    url = f"{PROD_URL}/invoices/exports"

    from_str = date_from.strftime('%Y-%m-%dT%H:%M:%SZ')

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
                "from": from_str,
                #"from": "2026-02-01T00:00:00Z",
                #"to": "2026-02-15T23:59:59Z"
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


# Status exportu 
def export_status(reference_number, access_token):

    url = f"{PROD_URL}/invoices/exports/{reference_number}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    while True:

        response = requests.get(url, headers=headers)

        print(f"Response code: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()

            export_status = response_data['status']['code']

            if export_status == 200:
                print("Package ready to be downloaded.")
                print(response_data['package']['invoiceCount'])
                print(response_data['package']['size'])

                parts_data = response_data['package']['parts']

                return True, parts_data
            
            elif export_status == 100:
                print(f"Package is still being prepared. Retrying in {EXPORT_DELAY_TIME} seconds.")
                time.sleep(EXPORT_DELAY_TIME)
                continue

            else:
                print("Export error")
                return False, None

        else:
            "Response error"
            return False, None


# Pobieranie paczki
def download_package(parts_data, symmetric_key, initialization_vector, entity_name):

    for part in parts_data:

        url = part['url']
        part_name = part['partName']

        print(part_name)

        response = requests.get(url)

        print(f"Response code: {response.status_code}")

        if response.status_code != 200:
            return

        encrypted_content = response.content

        cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(initialization_vector)) 
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(encrypted_content) + decryptor.finalize()

        unpadder = aes_padding.PKCS7(128).unpadder()

        try:
            decrypted_zip = unpadder.update(padded_data) + unpadder.finalize()

            part_name = part_name[:-8]

            output_path = f"{constants.INVOICE_DIRECTORY_PATH}/{entity_name}/{constants.ARCHIVE_DIRECTORY}/{part_name}.zip"

            with open(output_path, "wb") as f:
                f.write(decrypted_zip)

            print(f"Saved in {output_path}")

        except Exception as e:
            print(f"Decipher error: {e}")


def end_session(access_token):

    url = f"{PROD_URL}/auth/sessions/current"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.delete(url, headers=headers)

    print(f"Response code: {response.status_code}")

    if response.status_code == 204:
        print("Session ended successfully")


def download_invoices():
    start_time = time.time()

    print("Program started.\n")

    now = datetime.now(timezone.utc)
    print(f"Today is {now}")

    date_from = (now - timedelta(days=21)).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Downloading invoices not older than {date_from}")

    with open(constants.DATA_FILE_PATH, 'r') as file:
        supervision_scopes = json.load(file)

    for scope in supervision_scopes:

        for entity in scope['entity']:

            name = entity['name']
            nip = entity['nip']
            token = entity['token']

            print(f"\nDownloading invoice package for {name}")
        
            print("\n1. Certifying initiation")
            challange, timestamp = certifying_initiation()

            print("\n2. Downloading certificates")
            certificate_KsefTokenEncryption, certificate_SymmetricKeyEncryption  = download_certificates()

            print(f"\n3. Certifying using token (NIP = {nip} oraz TOKEN = {token})")

            encrypted_token = creating_encryptedToken(token, timestamp, certificate_KsefTokenEncryption)
            session_token, reference_number = certifying_with_token(nip, challange, encrypted_token)
            certifying_status(session_token, reference_number)

            print("\n4. Downloading access tokens")

            access_token, refresh_token = download_access_tokens(session_token)

            print("\n5. Downloading invoices")

            encrypted_key_b64, initialization_vector_b64, symmetric_key, initialization_vector = encrypt_export(certificate_SymmetricKeyEncryption)
            package_reference_number = invoice_export(encrypted_key_b64, initialization_vector_b64, access_token, date_from)

            isExported, parts_data = export_status(package_reference_number, access_token)

            if isExported:
                download_package(parts_data, symmetric_key, initialization_vector, name)

            print("\n6. Ending session")
            end_session(access_token)

    end_time = time.time()

    print(f"\nTotal execution time: {end_time - start_time} seconds")

if __name__ == "__main__":

    download_invoices()
