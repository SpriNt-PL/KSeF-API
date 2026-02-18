import os
import json

DATA_DIRECTORY = './Data/data.json'

INVOICE_DIRECTORY = './Invoices' 

def create_invoice_directory():

    if os.path.isdir(INVOICE_DIRECTORY):
        print("Main invoice directory exists.")
    
    else:
        os.mkdir(INVOICE_DIRECTORY)
        print("Main invoice directory created.")

def create_entities_directories():

    with open(DATA_DIRECTORY, 'r') as file:
        entities = json.load(file)

    for entity in entities:
        name = entity['name']

        entity_directory = f"{INVOICE_DIRECTORY}/{name}"

        if os.path.isdir(entity_directory):
            print(f"{name} directory exists.")

        else:
            os.mkdir(entity_directory)
            print(f"{name} directory created.")
    


if __name__ == "__main__":

    print("\n1. Create main invoice directory")
    create_invoice_directory()

    print("\n2. Create entity directories")
    create_entities_directories()