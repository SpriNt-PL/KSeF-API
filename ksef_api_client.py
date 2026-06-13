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

# Client based on official KSeF API PR instruction
# https://api.ksef.mf.gov.pl/docs/v2/index.html 

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

DAYS_BACK = 60

EXPORT_DELAY_TIME = 5
ACCESS_TOKENS_DELAY_TIME = 5

MAX_ATTEMPTS = 5

class KsefApiClient:
    def __init__(self, name, nip, token, date_from):
        # Entity session details
        self._name = name
        self._nip = nip
        self._token = token
        self._date_from = date_from

        # Introduced on "1. Certifying initialization" step
        self._challenge = None
        self._timestamp = None

        # Introduced on "2. Download certificates" step
        self._certificate_KsefTokenEncryption = None
        self._certificate_SymmetricKeyEncryption = None

        # Introduced on "3. Certifying using token" step
        self._encrypted_token = None
        self._session_token = None
        self._reference_number = None

        # Introduced on "4. Downloading access tokens" step
        self._access_token = None
        self._refresh_token = None

        # Introduced on "5. Downloading invoices" step
        self._encrypted_key_b64 = None 
        self._initialization_vector_b64 = None
        self._symmetric_key = None
        self._initialization_vector = None
        self._package_reference_number = None
        self._parts_data = None

    # Step name in instrucion: "Inicjalizacja uwierzytelnienia"
    # Generates unique challange required in the next certifying step
    def certifying_initiation(self):
        url = f"{PROD_URL}/auth/challenge"

        # Sending the request
        response = requests.post(url)
        response.raise_for_status()

        print(f"Response code: {response.status_code}")

        # Reading content of the response
        challenge_data = response.json()
        self._challenge = challenge_data['challenge']
        self._timestamp = challenge_data['timestampMs']

        print(f"Recieved challenge: {self._challenge}")
        print(f"Server timestamp: {self._timestamp}")

    # Step name in instrucion: "Pobranie certyfikatów"
    # Returns informations about public keys required for encrypting data before sending to KSeF system 
    def download_certificates(self):
        url = f"{PROD_URL}/security/public-key-certificates"

        # Sending the request
        response = requests.get(url)

        # Reading content of the response
        response_data = response.json()
        response_data_KsefTokenEncryption = response_data[0]
        response_data_SymmetricKeyEncryption = response_data[1]
        self._certificate_KsefTokenEncryption = response_data_KsefTokenEncryption['certificate']
        self._certificate_SymmetricKeyEncryption = response_data_SymmetricKeyEncryption['certificate']

        print(f"Certificate 'KsefTokenEncryption' valid until {response_data_KsefTokenEncryption['validTo']}")
        print(f"Certificate 'SymmetricKeyEncryption' valid until {response_data_SymmetricKeyEncryption['validTo']}")

    
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

    # Step name in instrucion: "Uwierzytelnienie z wykorzystaniem tokena KSeF"
    # Starts certifying using previously generated KSeF token
    def certifying_with_token(self):
        url = f"{PROD_URL}/auth/ksef-token"

        # Preparing the request's payload
        query_payload = {
            "challenge": f"{self._challenge}",
            "contextIdentifier": {
                "type": "Nip",
                "value": f"{self._nip}"
            },
            "encryptedToken": f"{self._encrypted_token}"
        }

        # Sending the request
        response = requests.post(url, json=query_payload)
        print(f"Response code: {response.status_code}")

        # Reading content of the response if status code is 202 (positive)
        if response.status_code == 202:
            response_data = response.json()
            print(f"Token ważny do: {response_data['authenticationToken']['validUntil']}")
            self._session_token = response_data['authenticationToken']['token']
            self._reference_number = response_data['referenceNumber']
            return True

        else:
            print(response_data)
            return False
        
    # Step name in instrucion: "Pobranie statusu uwierzytelniania"
    # Checks current certifying status
    def certifying_status(self):
        url = f"{PROD_URL}/auth/{self._reference_number}"

        # Preparing header needed for the request
        headers = {
            "Authorization": f"Bearer {self._session_token}"
        }

        # Sending the request
        response = requests.get(url, headers=headers)

        print(f"Response code: {response.status_code}")

        # Reading content of the response if status code is 200 (positive)
        if response.status_code == 200:
            response_data = response.json()

            print(response_data['authenticationMethod'])
            print(response_data['status']['code'])
            print(response_data['status']['description'])
    
    # Step name in instrucion: "Pobranie tokenów dostępowych"
    # Downloads access token and refresh token generated after successful certifying process
    def download_access_tokens(self):

        url = f"{PROD_URL}/auth/token/redeem"

        # Preparing header needed for the request
        headers = {
            "Authorization": f"Bearer {self._session_token}"
        }

        # Sending the request
        response = requests.post(url, headers=headers)

        print(f"Response code: {response.status_code}")

        # Reading content of the response if status code is 200 (positive)
        if response.status_code == 200:
            response_data = response.json()

            self._access_token = response_data['accessToken']['token']
            self._refresh_token = response_data['refreshToken']['token']

            print(f"Access token valid until: {response_data['accessToken']['validUntil']}")
            print(f"Refresh token valid until: {response_data['refreshToken']['validUntil']}")

    
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

    # Step name in instrucion: "Eksport paczki faktur"
    # Starts process of finding invoices in KSeF System based on the provided filters and initiates the preparation of package containing them
    def invoice_export(self):
        url = f"{PROD_URL}/invoices/exports"

        # Preparing header needed for the request
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        # Date paresed for the purpose of the filtering by date
        from_str = self._date_from.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Preparing the request's payload containing filters
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

        # Sending the request
        response = requests.post(url, headers=headers, json=query_payload)

        print(f"Response code: {response.status_code}")

        # Reading content of the response if status code is 201 (positive)
        if response.status_code == 201:
            response_data = response.json()

            self._package_reference_number = response_data['referenceNumber']

    # Step name in instrucion: "Pobranie statusu eksportu paczki faktur"
    # Returns information wheather the package was prepared to be downloaded   
    def export_status(self):

        url = f"{PROD_URL}/invoices/exports/{self._package_reference_number}"

        # Preparing header needed for the request
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        while True:
            
            # Sending the request
            response = requests.get(url, headers=headers)

            print(f"Response code: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()

                export_status = response_data['status']['code']

                # Reading content of the response if status code is 200 (positive)
                if export_status == 200:
                    print("Package ready to be downloaded.")
                    print(response_data['package']['invoiceCount'])
                    print(response_data['package']['size'])

                    if response_data['package']['invoiceCount'] > 0:
                        self._parts_data = response_data['package']['parts']
                    
                    return True
                    
                # Wait if package is still being prepared
                elif export_status == 100:
                    print(f"Package is still being prepared. Retrying in {EXPORT_DELAY_TIME} seconds.")
                    time.sleep(EXPORT_DELAY_TIME)
                    continue
                
                # Any other code means that export process failed
                else:
                    print("Export error")
                    return False

            # Abort is the response failed.
            else:
                "Response error"
                return False
            
    # Downloads all packages for the entity
    def download_package(self):
        
        # Iterate over each package
        for part in self._parts_data:

            url = part['url']
            part_name = part['partName']

            print(part_name)

            # Sending the request
            response = requests.get(url)

            print(f"Response code: {response.status_code}")

            if response.status_code != 200:
                return False

            # Reading the encrypted package content
            encrypted_content = response.content

            # Decrypting the package content
            cipher = Cipher(algorithms.AES(self._symmetric_key), modes.CBC(self._initialization_vector)) 
            decryptor = cipher.decryptor()

            padded_data = decryptor.update(encrypted_content) + decryptor.finalize()

            unpadder = aes_padding.PKCS7(128).unpadder()

            try:
                decrypted_zip = unpadder.update(padded_data) + unpadder.finalize()

                part_name = part_name[:-8]

                # Saving the decrypted archive in the proper Archive directory
                output_path = f"{constants.INVOICE_DIRECTORY_PATH}/{self._name}/{constants.ARCHIVE_DIRECTORY}/{part_name}.zip"

                with open(output_path, "wb") as f:
                    f.write(decrypted_zip)

                print(f"Saved in {output_path}")

            except Exception as e:
                print(f"Decipher error: {e}")
                return False

        return True # Remember about this
        
    # Step name in instrucion: "Unieważnienie aktualnej sesji uwierzytelnienia"
    # Ends current session
    def end_session(self):

        url = f"{PROD_URL}/auth/sessions/current"

        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }

        response = requests.delete(url, headers=headers)

        print(f"Response code: {response.status_code}")

        if response.status_code == 204:
            print("Session ended successfully")

    
    # Invoice downloading process orchestrator
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
        # End the process if the status above is False
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

        # End the process is at least one of the tokens are missing
        if self._access_token is None or self._refresh_token is None:
                print("Unable to download access tokens. Skipping to the next entity")
                return False
        
        print("\n5. Downloading invoices")
        self.encrypt_export()
        self.invoice_export()
        is_exported = self.export_status()
        
        is_downloaded = False
        if is_exported and self._parts_data is not None:
            is_downloaded = self.download_package()
        
        print("\n6. Ending session")
        self.end_session()

        return is_downloaded


# For the testing purpose
if __name__ == '__main__':
    start_time = time.time()

    print("Program started.\n")

    now = datetime.now()
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