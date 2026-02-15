import os
from zipfile import ZipFile

ARCHIVE_INPUT_FOLDER = './Invoices/Archive'
ARCHIVE_OUTPUT_FOLDER = './Invoices/Extracted'

def extract_files():
    files = os.listdir(ARCHIVE_INPUT_FOLDER)

    if not files:
        print("Folder is empty!")
        return

    filename = files[0]

    filepath = os.path.join(ARCHIVE_INPUT_FOLDER, filename)

    print(filepath)
    
    with ZipFile(filepath, 'r') as zip_object:
        zip_object.extractall(path=ARCHIVE_OUTPUT_FOLDER)


if __name__ == "__main__":
    print("Invoice preparation started")

    print("\n 1. Unzipping the archive with invoices")
    extract_files()

