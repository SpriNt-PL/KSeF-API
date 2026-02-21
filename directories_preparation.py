import os
import json

import constants

def create_invoice_directory(base_path):

    if os.path.isdir(base_path):
        print("Main invoice directory exists.")
    
    else:
        os.mkdir(base_path)
        print("Main invoice directory created.")

def create_entities_directories(supervision_scopes):

    for scope in supervision_scopes:

        for entity in scope['entity']:

            name = entity['name']

            entity_directory = f"{constants.INVOICE_DIRECTORY_PATH}/{name}"

            if os.path.isdir(entity_directory):
                print(f"{name} directory exists.")

            else:
                os.mkdir(entity_directory)
                print(f"{name} directory created.")


def create_essential_directories_for_each_entity(supervision_scopes):

    for scope in supervision_scopes:

        for entity in scope['entity']:

            name = entity['name']

            archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.ARCHIVE_DIRECTORY}"

            invoice_xml_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_XML_DIRECTORY}"

            invoice_pdf_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_PDF_DIRECTORY}"

            old_archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.OLD_ARCHIVE_DIRECTORY}"

            if os.path.isdir(archive_directory_path):
                print(f"Archive directory in {name} exists.")

            else:
                os.mkdir(archive_directory_path)
                print(f"Archive directory in {name} created.")

            if os.path.isdir(invoice_xml_directory_path):
                print(f"Invoice_XML directory in {name} exists.")

            else:
                os.mkdir(invoice_xml_directory_path)
                print(f"Invoice_XML directory in {name} created.")

            if os.path.isdir(invoice_pdf_directory_path):
                print(f"Invoice_PDF directory in {name} exists.")

            else:
                os.mkdir(invoice_pdf_directory_path)
                print(f"Invoice_PDF directory in {name} created.")

            if os.path.isdir(old_archive_directory_path):
                print(f"Old_Archive directory in {name} exists.")

            else:
                os.mkdir(old_archive_directory_path)
                print(f"Old_Archive directory in {name} created.")


def create_directory_for_each_supervisor(base_path, supervision_scopes):

    for scope in supervision_scopes:

        supervisior = scope['supervisor']

        supervisor_directory_path = f"{base_path}/{supervisior}"

        if os.path.isdir(supervisor_directory_path):
                print(f"Old_Archive directory in {supervisior} exists.")

        else:
            os.mkdir(supervisor_directory_path)
            print(f"Old_Archive directory in {supervisior} created.")




if __name__ == "__main__":

    print("\nPreparing working directory for file processing")

    print("\n1. Create main invoice directory")
    create_invoice_directory(constants.INVOICE_DIRECTORY_PATH)

    with open(constants.DATA_FILE_PATH, 'r') as file:
        supervision_scopes = json.load(file)

    print("\n2. Create entity directories")
    create_entities_directories(supervision_scopes)

    print("\n3. Create essential directories directories for each entity")
    create_essential_directories_for_each_entity(supervision_scopes)

    print("\nPreparing main output directory from where invoices are being processed manually")

    print("\n1. Create main invoice directory")
    create_invoice_directory(constants.OUTPUT_DIRECTORY_PATH)

    print("\n2. Create directory for each supervisor")
    create_directory_for_each_supervisor(constants.OUTPUT_DIRECTORY_PATH, supervision_scopes)



