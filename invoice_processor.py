import json
import textwrap
import os
import shutil
from zipfile import ZipFile

import constants


class InvoiceProcessor:
    def __init__(self, name, supervisor_name):
        # Entity details
        self._name = name
        self._supervisor_name = supervisor_name

        self._is_archive_present = None
        self._new_invoices = []


        # Paths to directories
        self._archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.ARCHIVE_DIRECTORY}"
        self._old_archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.OLD_ARCHIVE_DIRECTORY}"
        self._invoice_xml_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_XML_DIRECTORY}"
        self._invoice_pdf_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_PDF_DIRECTORY}"
        self._supervisor_directory_path = f"{constants.OUTPUT_DIRECTORY_PATH}/{supervisor_name}"

    
    def choose_only_new_files(self, zip_file_list, destination_file_list):

        new_files = list(set(zip_file_list).difference(destination_file_list))

        return new_files


    def extract_files(self):

        files = os.listdir(self._archive_directory_path)

        if not files:
            print("Folder is empty!")
            return False, None

        filename = files[0]

        source_archive_path = os.path.join(self._archive_directory_path, filename)

        print(source_archive_path)

        invoice_xml_directory_file_list = os.listdir(self._invoice_xml_directory_path)
        
        with ZipFile(source_archive_path, 'r') as zip_object:
            file_list = zip_object.namelist()

            new_files = self.choose_only_new_files(file_list, invoice_xml_directory_file_list)

            for file in new_files:
                zip_object.extract(file, path=self._invoice_xml_directory_path)

        if len(new_files) > 0:
            print(f"New files extracted: {new_files}")
        else:
            print("No new files found.")

        destination_archive_path = os.path.join(self._old_archive_directory_path, filename)

        shutil.move(source_archive_path, destination_archive_path)

        print(f"Archive moved to {self._old_archive_directory_path}")

        self._new_invoices = new_files

    
    def prepare_invoices(self):
        communicate = f"""
        =================================================================
        Processing invoices belonging to: {self._name}
        =================================================================
        """

        print(textwrap.dedent(communicate))

        print("1. Unzipping the archive with invoices")
        self.extract_files()


if __name__ == '__main__':
    print("Invoice preparation started")

    # Import data file
    with open(constants.DATA_FILE_PATH, 'r') as file:
        supervision_scope = json.load(file)

    for scope in supervision_scope:
        supervisor_name = scope['supervisor']

        for entity in scope['entity']:
            name = entity['name']

            invoice_processor = InvoiceProcessor(name, supervisor_name)

            invoice_processor.prepare_invoices()