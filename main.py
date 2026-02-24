import os
import sys
import subprocess

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "install-browsers":
        import playwright.__main__
        sys.argv = ["playwright", "install", "chromium"]
        playwright.__main__.main()
        sys.exit(0)

from directories_preparation import prepare_directories
from ksef_api import download_invoices
from invoice_preparation import prepare_invoices
from auxiliary_functions import prepare_playwright, prepare_statistics, show_report

if __name__ == "__main__":

    try:
        prepare_playwright()

        prepare_directories()
        failure_list, entities_processed = download_invoices()
        prepare_invoices()

        entities_count = prepare_statistics()

        show_report(failure_list, entities_count, entities_processed)


    except Exception as e:
        print(f"Error {e}")
    finally:
        print("\nEnd of a program")
        input("Press Enter to close the program")
