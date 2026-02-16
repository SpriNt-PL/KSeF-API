import os
import shutil
import asyncio
import pathlib
from zipfile import ZipFile
from playwright.async_api import async_playwright

RENDER_TIME_DELAY = 1000 # miliseconds

ARCHIVE_FOLDER = './Invoices/Archives'
EXTRACTED_FOLDER = './Invoices/Extracted'
OLD_ARCHIVE_FOLDER = './Invoices/Old_Archives'
PREPARED_XML_INVOICES_FOLDER = './Invoices/Prepared_XML_Invoices'
PDF_INVOICES_FOLDER = './Invoices/PDF_Invoices'

XML_FIRST_LINE = '<?xml version="1.0" encoding="UTF-8"?>'
XML_SECOND_LINE = '<?xml-stylesheet type="text/xsl" href="Scheme/styl.xsl"?>'

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
    
    for file in files:
        if file.endswith('.xml') and file != 'wyroznik.xml':

            filepath = os.path.join(EXTRACTED_FOLDER, file)

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.readlines()

            # Logic which ensures that prefix will be added in a proper way
            if content and content[0].startswith('<?xml'):
                
                row = content[0]
                i = 0

                while i < len(row):
                    character = row[i]

                    if character == '>':
                        break

                    i += 1

                content[0] = row[i+1:]

            new_content = [XML_FIRST_LINE + '\n' + XML_SECOND_LINE + '\n'] + content

            destination_path = os.path.join(PREPARED_XML_INVOICES_FOLDER, file)

            with open(destination_path, 'w', encoding='utf-8') as f:
                f.writelines(new_content)

    print("Files successfully edited")


async def save_xml_as_pdf():
    async with async_playwright() as p:

        browser = await p.chromium.launch(args=['--allow-file-access-from-files'])
        page = await browser.new_page()

        for file in os.listdir(PREPARED_XML_INVOICES_FOLDER):
            xml_path = os.path.join(PREPARED_XML_INVOICES_FOLDER, file)
            xml_path_abs = os.path.abspath(xml_path)
            
            pdf_path = os.path.join(PDF_INVOICES_FOLDER, file)

            file_url = pathlib.Path(xml_path_abs).as_uri()

            print(f"Preparing PDF for {file}")

            await page.goto(file_url)

            await page.wait_for_timeout(RENDER_TIME_DELAY)

            await page.pdf(
                path = pdf_path,
                format='A4',
                print_background=True
            )

        await browser.close()


if __name__ == "__main__":
    print("Invoice preparation started")

    print("\n 1. Unzipping the archive with invoices")
    extract_files()

    print("\n 2. Editing the XML files so that it is possible to visualize them")
    edit_xml_files()

    print("\n 3. Save XML invoices as PDF")
    asyncio.run(save_xml_as_pdf())

