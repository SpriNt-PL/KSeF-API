from directories_preparation import prepare_directories
from ksef_api import download_invoices
from invoice_preparation import prepare_invoices
from auxiliary_functions import prepare_playwright

if __name__ == "__main__":

    try:
        prepare_playwright()
        prepare_directories()
        download_invoices()
        prepare_invoices()
    except Exception as e:
        print(f"Error {e}")
    finally:
        print("\nEnd of a program")
        input("Press Enter to close the program")
