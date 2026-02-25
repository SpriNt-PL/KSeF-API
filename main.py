import os
import sys
import subprocess
import time

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "install-browsers":
        import playwright.__main__
        sys.argv = ["playwright", "install", "chromium"]
        playwright.__main__.main()
        sys.exit(0)

from directories_preparation import prepare_directories
from ksef_api import download_invoices
from invoice_preparation import prepare_invoices
from auxiliary_functions import prepare_playwright, prepare_statistics, show_report, save_report_to_file

if __name__ == "__main__":

    try:
        start_time = time.time()
        prepare_playwright()

        prepare_directories()
        failure_list, entities_processed = download_invoices()
        prepare_invoices()

        entities_count = prepare_statistics()

        end_time = time.time()

        elapsed_time = end_time - start_time

        #show_report(failure_list, entities_count, entities_processed)

        save_report_to_file(failure_list, entities_count, entities_processed, elapsed_time)


    except Exception as e:
        print(f"Error {e}")
    finally:
        print("\nEnd of a program")
        input("Press Enter to close the program")
