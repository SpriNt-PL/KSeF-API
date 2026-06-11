import requests
import time
import json
from datetime import datetime, timedelta, timezone


import constants

PROD_URL = "https://api.ksef.mf.gov.pl/v2"

class KsefApiClient:
    def __init__(self, name, nip, token, date_from):
        self._name = name
        self._nip = nip
        self._token = token
        self._date_from = date_from

        self._challange = None
        self._timestamp = None

    def certifying_initiation(self):
        url = f"{PROD_URL}/auth/challenge"

        response = requests.post(url)
        response.raise_for_status()

        print(f"Response code: {response.status_code}")

        challenge_data = response.json()

        self._challange = challenge_data['challenge']
        self._timestamp = challenge_data['timestampMs']

        print(f"Recieved challenge: {self._challange}")
        print(f"Server timestamp: {self._timestamp}")

    def download_invoices(self):
        self.certifying_initiation()



if __name__ == '__main__':
    start_time = time.time()

    print("Program started.\n")

    now = datetime.now(timezone.utc)
    print(f"Today is {now}")

    date_from = (now - timedelta(days=60)).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Downloading invoices not older than {date_from}")

    with open(constants.DATA_FILE_PATH, 'r') as file:
        supervision_scopes = json.load(file)

    for scope in supervision_scopes:

        for entity in scope['entity']:
            name = entity['name']
            nip = entity['nip']
            token = entity['token']

            ksef_client = KsefApiClient(name, nip, token, date_from)

            ksef_client.download_invoices()

    end_time = time.time()

    print(f"\nTotal execution time: {end_time - start_time} seconds")