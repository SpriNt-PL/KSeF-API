from datetime import datetime, timedelta
import os
import sys
import subprocess
import time
import json

import constants
from ksef_api_client import KsefApiClient

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "install-browsers":
        import playwright.__main__
        sys.argv = ["playwright", "install", "chromium"]
        playwright.__main__.main()
        sys.exit(0)

from directories_preparation import prepare_directories
from invoice_preparation import prepare_invoices
from auxiliary_functions import prepare_playwright, prepare_statistics, show_report, save_report_to_file

DAYS_BACK = 60

if __name__ == "__main__":

    try:
        # Program starts, starting counting time
        start_time = time.time()
        print("Program started.\n")

        # Prepare browser engine (unless it is not installed)
        prepare_playwright()

        # Create directories structure
        prepare_directories()

        # Getting current date and time
        now = datetime.now()
        print(f"Today is {now}")

        # Defining from how many days in past do we want to download invoices
        date_from = (now - timedelta(days=DAYS_BACK)).replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"Downloading invoices not older than {date_from}")

        # Importing data.json
        with open(constants.DATA_FILE_PATH, 'r') as file:
            supervision_scopes = json.load(file)

        failure_list = []
        entities_processed = 0

        # Loop over each supervision scope (e.g. "John Doe" supervises "Goodfood" and "BestCars" entities and 
        # the bundle of these entities is called scope)
        for scope in supervision_scopes:
            
            # Loop over entity in scope
            for entity in scope['entity']:
                name = entity['name']
                nip = entity['nip']
                token = entity['token']

                ksef_client = KsefApiClient(name, nip, token, date_from)

                # If KSeF Client did not succeed then add name of currently process entity to the failure list
                success = ksef_client.download_invoices()
                if not success:
                    failure_list.append(name)

                entities_processed += 1

        # ---TO BE CHANGED--- After downloading packages (archives) with invoices in XML convert them into PDFs
        prepare_invoices()

        entities_count = prepare_statistics()

        # Calculating program execution time
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Saving the report 
        save_report_to_file(failure_list, entities_count, entities_processed, elapsed_time)

        print(f"\nTotal execution time: {elapsed_time:.2f} seconds")


    except Exception as e:
        print(f"Error {e}")
    finally:
        print("\nEnd of a program")
        input("Press Enter to close the program")
