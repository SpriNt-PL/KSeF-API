import os
import json

import constants

def create_invoice_directory():

    if os.path.isdir(constants.INVOICE_DIRECTORY):
        print("Main invoice directory exists.")
    
    else:
        os.mkdir(constants.INVOICE_DIRECTORY)
        print("Main invoice directory created.")

def create_entities_directories(entities):

    for entity in entities:
        name = entity['name']

        entity_directory = f"{constants.INVOICE_DIRECTORY}/{name}"

        if os.path.isdir(entity_directory):
            print(f"{name} directory exists.")

        else:
            os.mkdir(entity_directory)
            print(f"{name} directory created.")


def create_essential_directories_for_each_entity(entities):

    for entity in entities:
        name = entity['name']

        archive_directory = f"{constants.INVOICE_DIRECTORY}/{name}/{constants.ARCHIVE_DIRECTORY}"

        invoice_xml_directory = f"{constants.INVOICE_DIRECTORY}/{name}/{constants.INVOICE_XML_DIRECTORY}"

        invoice_pdf_directory = f"{constants.INVOICE_DIRECTORY}/{name}/{constants.INVOICE_PDF_DIRECTORY}"

        old_archive_directory = f"{constants.INVOICE_DIRECTORY}/{name}/{constants.OLD_ARCHIVE_DIRECTORY}"

        if os.path.isdir(archive_directory):
            print(f"Archive directory in {name} exists.")

        else:
            os.mkdir(archive_directory)
            print(f"Archive directory in {name} created.")

        if os.path.isdir(invoice_xml_directory):
            print(f"Invoice_XML directory in {name} exists.")

        else:
            os.mkdir(invoice_xml_directory)
            print(f"Invoice_XML directory in {name} created.")

        if os.path.isdir(invoice_pdf_directory):
            print(f"Invoice_PDF directory in {name} exists.")

        else:
            os.mkdir(invoice_pdf_directory)
            print(f"Invoice_PDF directory in {name} created.")

        if os.path.isdir(old_archive_directory):
            print(f"Old_Archive directory in {name} exists.")

        else:
            os.mkdir(old_archive_directory)
            print(f"Old_Archive directory in {name} created.")
        


if __name__ == "__main__":

    print("\n1. Create main invoice directory")
    create_invoice_directory()

    with open(constants.DATA_FILE, 'r') as file:
        entities = json.load(file)

    print("\n2. Create entity directories")
    create_entities_directories(entities)

    print("\n3. Create essential directories directories for each entity")
    create_essential_directories_for_each_entity(entities)