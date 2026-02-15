import os
import shutil
from zipfile import ZipFile

ARCHIVE_FOLDER = './Invoices/Archives'
EXTRACTED_FOLDER = './Invoices/Extracted'
OLD_ARCHIVE_FOLDER = './Invoices/Old_Archives'

def extract_files():
    files = os.listdir(ARCHIVE_FOLDER)

    if not files:
        print("Folder is empty!")
        return

    filename = files[0]

    source_archive_path = os.path.join(ARCHIVE_FOLDER, filename)

    print(source_archive_path)
    
    with ZipFile(source_archive_path, 'r') as zip_object:
        zip_object.extractall(path=EXTRACTED_FOLDER)

    destination_archive_path = os.path.join(OLD_ARCHIVE_FOLDER, filename)

    shutil.move(source_archive_path, destination_archive_path)

    print(f"Archive moved to {OLD_ARCHIVE_FOLDER}")


def edit_xml_files():
    files = os.listdir(EXTRACTED_FOLDER)

    if not files:
        print("Folder is empty!")
        return
    
    


if __name__ == "__main__":
    print("Invoice preparation started")

    print("\n 1. Unzipping the archive with invoices")
    extract_files()

