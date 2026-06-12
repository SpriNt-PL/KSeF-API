import requests
import time
import json
import textwrap
import base64
import os
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as aes_padding


import constants

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

DAYS_BACK = 60

EXPORT_DELAY_TIME = 5
ACCESS_TOKENS_DELAY_TIME = 5

MAX_ATTEMPTS = 5

class KsefApiClient:
    def __init__(self, name, nip, token, date_from, failure_list):
        self._name = name
        self._nip = nip
        self._token = token
        self._date_from = date_from

        self._challenge = None
        self._timestamp = None
        self._certificate_KsefTokenEncryption = None
        self._certificate_SymmetricKeyEncryption = None
        self._encrypted_token = None
        self._session_token = None
        self._reference_number = None
        self._access_token = None
        self._refresh_token = None
        self._encrypted_key_b64 = None 
        self._initialization_vector_b64 = None
        self._symmetric_key = None
        self._initialization_vector = None
        self._package_reference_number = None
        self._parts_data = None

        self._failure_list = failure_list


    def certifying_initiation(self):
        url = f"{PROD_URL}/auth/challenge"

        response = requests.post(url)
        response.raise_for_status()

        print(f"Response code: {response.status_code}")

        challenge_data = response.json()

        self._challenge = challenge_data['challenge']
        self._timestamp = challenge_data['timestampMs']

        print(f"Recieved challenge: {self._challenge}")
        print(f"Server timestamp: {self._timestamp}")


    def download_certificates(self):
        
        url = f"{PROD_URL}/security/public-key-certificates"

        response = requests.get(url)

        response_data = response.json()
        response_data_KsefTokenEncryption = response_data[0]
        response_data_SymmetricKeyEncryption = response_data[1]

        print(f"Certificate 'KsefTokenEncryption' valid until {response_data_KsefTokenEncryption['validTo']}")
        print(f"Certificate 'SymmetricKeyEncryption' valid until {response_data_SymmetricKeyEncryption['validTo']}")

        self._certificate_KsefTokenEncryption = response_data_KsefTokenEncryption['certificate']
        self._certificate_SymmetricKeyEncryption = response_data_SymmetricKeyEncryption['certificate']

    
    def creating_encryptedToken(self):

        plain_text = f"{self._token}|{self._timestamp}".encode('utf-8')

        cert_bytes = base64.b64decode(self._certificate_KsefTokenEncryption)
        cert_obj = x509.load_der_x509_certificate(cert_bytes)
        public_key = cert_obj.public_key()

        encrypted = public_key.encrypt(plain_text, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        ))

        self._encrypted_token = base64.b64encode(encrypted).decode('utf-8')

    
    def certifying_with_token(self):

        url = f"{PROD_URL}/auth/ksef-token"

        query_payload = {
            "challenge": f"{self._challenge}",
            "contextIdentifier": {
                "type": "Nip",
                "value": f"{self._nip}"
            },
            "encryptedToken": f"{self._encrypted_token}"
        }

        response = requests.post(url, json=query_payload)
        print(f"Response code: {response.status_code}")

        if response.status_code == 202:
            response_data = response.json()
            print(f"Token ważny do: {response_data['authenticationToken']['validUntil']}")
            self._session_token = response_data['authenticationToken']['token']
            self._reference_number = response_data['referenceNumber']
            return True

        else:
            print(response_data)
            return False
        
    
    def certifying_status(self):

        url = f"{PROD_URL}/auth/{self._reference_number}"

        headers = {
            "Authorization": f"Bearer {self._session_token}"
        }

        response = requests.get(url, headers=headers)

        print(f"Response code: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()

            print(response_data['authenticationMethod'])
            print(response_data['status']['code'])
            print(response_data['status']['description'])
    

    def download_access_tokens(self):

        url = f"{PROD_URL}/auth/token/redeem"

        headers = {
            "Authorization": f"Bearer {self._session_token}"
        }

        response = requests.post(url, headers=headers)

        print(f"Response code: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()

            print(f"Access token valid until: {response_data['accessToken']['validUntil']}")
            print(f"Refresh token valid until: {response_data['refreshToken']['validUntil']}")

            self._access_token = response_data['accessToken']['token']
            self._refresh_token = response_data['refreshToken']['token']

    
    def encrypt_export(self):
        self._symmetric_key = os.urandom(32)

        self._initialization_vector = os.urandom(16)

        cert_bytes = base64.b64decode(self._certificate_SymmetricKeyEncryption)
        cert_obj = x509.load_der_x509_certificate(cert_bytes)
        public_key = cert_obj.public_key()

        encrypted_key = public_key.encrypt(self._symmetric_key, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        ))

        self._encrypted_key_b64 = base64.b64encode(encrypted_key).decode('utf-8')
        self._initialization_vector_b64 = base64.b64encode(self._initialization_vector).decode('utf-8')


    def invoice_export(self):

        url = f"{PROD_URL}/invoices/exports"

        from_str = self._date_from.strftime('%Y-%m-%dT%H:%M:%SZ')

        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        query_payload = {
            "encryption": {
                "encryptedSymmetricKey": f"{self._encrypted_key_b64}",
                "initializationVector": f"{self._initialization_vector_b64}"
            },
            "filters": {
                "subjectType": "Subject2", 
                "dateRange": {
                    "dateType": "Invoicing",
                    "from": from_str,
                    # "from": "2026-04-01T00:00:00Z",
                    # "to": "2026-02-15T23:59:59Z"
                }
            }
        }

        response = requests.post(url, headers=headers, json=query_payload)

        print(f"Response code: {response.status_code}")

        if response.status_code == 201:
            response_data = response.json()

            self._package_reference_number = response_data['referenceNumber']

        
    def export_status(self):

        url = f"{PROD_URL}/invoices/exports/{self._package_reference_number}"

        headers = {
            "Authorization": f"Bearer {self._access_token}"
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

                    if response_data['package']['invoiceCount'] > 0:
                        self._parts_data = response_data['package']['parts']
                    
                    return True
                    
                
                elif export_status == 100:
                    print(f"Package is still being prepared. Retrying in {EXPORT_DELAY_TIME} seconds.")
                    time.sleep(EXPORT_DELAY_TIME)
                    continue

                else:
                    print("Export error")
                    return False

            else:
                "Response error"
                return False
            
    
    def download_package(self):

        for part in self._parts_data:

            url = part['url']
            part_name = part['partName']

            print(part_name)

            response = requests.get(url)

            print(f"Response code: {response.status_code}")

            if response.status_code != 200:
                return False

            encrypted_content = response.content

            cipher = Cipher(algorithms.AES(self._symmetric_key), modes.CBC(self._initialization_vector)) 
            decryptor = cipher.decryptor()

            padded_data = decryptor.update(encrypted_content) + decryptor.finalize()

            unpadder = aes_padding.PKCS7(128).unpadder()

            try:
                decrypted_zip = unpadder.update(padded_data) + unpadder.finalize()

                part_name = part_name[:-8]

                output_path = f"{constants.INVOICE_DIRECTORY_PATH}/{self._name}/{constants.ARCHIVE_DIRECTORY}/{part_name}.zip"

                with open(output_path, "wb") as f:
                    f.write(decrypted_zip)

                print(f"Saved in {output_path}")

            except Exception as e:
                print(f"Decipher error: {e}")
                return False

            return True # Remember about this
        

    def end_session(self):

        url = f"{PROD_URL}/auth/sessions/current"

        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        response = requests.delete(url, headers=headers)

        print(f"Response code: {response.status_code}")

        if response.status_code == 204:
            print("Session ended successfully")

    
    def get_failure_list(self):
        return self._failure_list


    def download_invoices(self):

        communicate = f"""
        =================================================================
        Downloading invoice package for {self._name}
        =================================================================
        """

        print(textwrap.dedent(communicate))

        print("1. Certifying initiation")
        self.certifying_initiation()

        print("\n2. Downloading certificates")
        self.download_certificates()

        print(f"\n3. Certifying using token (NIP = {self._nip} oraz TOKEN = {self._token})")
        self.creating_encryptedToken()
        status = self.certifying_with_token()
        if not status:
            return False 

        self.certifying_status()

        print("\n4. Downloading access tokens")
        self.download_access_tokens()

        # Ensuring that access tokens will be downloaded (allowed attempts)
        attempts = 0
        while (self._access_token is None or self._refresh_token is None) and attempts < MAX_ATTEMPTS:
            print(f"Unable to download access tokens. Retrying in {ACCESS_TOKENS_DELAY_TIME}. {MAX_ATTEMPTS - attempts} attempts left.")
            attempts += 1
            time.sleep(ACCESS_TOKENS_DELAY_TIME)
            self.download_access_tokens()

        if self._access_token is None or self._refresh_token is None:
                print("Unable to download access tokens. Skipping to the next entity")
                return False
        
        print("\n5. Downloading invoices")
        self.encrypt_export()
        self.invoice_export()
        is_exported = self.export_status()

        if is_exported:
            if self._parts_data != None:
                is_downloaded = self.download_package()

        if not is_downloaded:
            if self._parts_data != None:
                self._failure_list.append(name)
        
        print("\n6. Ending session")
        self.end_session()


if __name__ == '__main__':
    start_time = time.time()

    print("Program started.\n")

    now = datetime.now(timezone.utc)
    print(f"Today is {now}")

    date_from = (now - timedelta(days=DAYS_BACK)).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Downloading invoices not older than {date_from}")

    with open(constants.DATA_FILE_PATH, 'r') as file:
        supervision_scopes = json.load(file)

    failure_list = []
    entities_processed = 0

    for scope in supervision_scopes:

        for entity in scope['entity']:
            name = entity['name']
            nip = entity['nip']
            token = entity['token']

            ksef_client = KsefApiClient(name, nip, token, date_from, failure_list)

            ksef_client.download_invoices()

    end_time = time.time()

    print(f"\nTotal execution time: {end_time - start_time} seconds")