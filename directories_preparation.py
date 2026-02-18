import os

INVOICE_FOLDER = './Invoices'

def create_directries_structure():

    if os.path.isdir(INVOICE_FOLDER):
        print("Main invoice directory exists.")
    
    else:
        os.mkdir(INVOICE_FOLDER)
        print("Main invoice directory created.")

if __name__ == "__main__":
    create_directries_structure()