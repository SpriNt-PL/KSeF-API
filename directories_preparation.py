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


def create_archive_directories(entities):

    for entity in entities:
        name = entity['name']

        archive_directory = f"{constants.INVOICE_DIRECTORY}/{name}/Archive"

        if os.path.isdir(archive_directory):
            print(f"Archive directory in {name} exists.")

        else:
            os.mkdir(archive_directory)
            print(f"Archive directory in {name} created.")


if __name__ == "__main__":

    print("\n1. Create main invoice directory")
    create_invoice_directory()

    with open(constants.DATA_FILE, 'r') as file:
        entities = json.load(file)

    print("\n2. Create entity directories")
    create_entities_directories(entities)

    print("\n3. Create archive directories")
    create_archive_directories(entities)