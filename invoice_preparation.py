import os
import shutil
import asyncio
import time
import json
from zipfile import ZipFile
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from lxml import etree

import constants

XML_FIRST_LINE = '<?xml version="1.0" encoding="UTF-8"?>'
XML_SECOND_LINE = '<?xml-stylesheet type="text/xsl" href="Scheme/styl.xsl"?>'

XSL_STYLE_FILE = './Data/Scheme/styl.xsl'

MAXIMUM_NUMBER_OF_ASYNCHRONOUS_PROCESSES = 10

def extract_files(archive_directory_path, old_archive_directory_path, invoice_xml_directory_path):

    files = os.listdir(archive_directory_path)

    if not files:
        print("Folder is empty!")
        return False

    filename = files[0]

    source_archive_path = os.path.join(archive_directory_path, filename)

    print(source_archive_path)
    
    with ZipFile(source_archive_path, 'r') as zip_object:
        zip_object.extractall(path=invoice_xml_directory_path)

    destination_archive_path = os.path.join(old_archive_directory_path, filename)

    shutil.move(source_archive_path, destination_archive_path)

    print(f"Archive moved to {old_archive_directory_path}")

    return True


def edit_xml_files(invoice_xml_directory_path):

    files = os.listdir(invoice_xml_directory_path)

    if not files:
        print("Folder is empty!")
        return
    
    for file in files:
        if file.endswith('.xml') and file != 'wyroznik.xml':

            filepath = os.path.join(invoice_xml_directory_path, file)

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.readlines()

            # Deleting original version of a file
            os.remove(filepath)

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

            destination_path = os.path.join(invoice_xml_directory_path, file)

            with open(destination_path, 'w', encoding='utf-8') as f:
                f.writelines(new_content)

    print("Files successfully edited")


# Sychroniczna (pierwsza wersja)
def save_xml_as_pdf(invoice_xml_directory_path, invoice_pdf_directory_path):
    
    try:
        parser = etree.XMLParser(no_network=False, resolve_entities=True)
        access_control = etree.XSLTAccessControl(read_network=True, read_file=True)

        with sync_playwright() as p:

            browser = p.chromium.launch(args=['--allow-file-access-from-files'])
            page = browser.new_page()

            xsl_dom = etree.parse(XSL_STYLE_FILE, parser=parser)
            transform = etree.XSLT(xsl_dom, access_control=access_control)

            for file in os.listdir(invoice_xml_directory_path):
                
                if file.endswith('.xml'):
                    print(f"Preparing PDF for {file}")

                    xml_path = os.path.join(invoice_xml_directory_path, file)

                    xml_dom = etree.parse(xml_path, parser=parser)

                    result_html = transform(xml_dom)
                    html_string = etree.tostring(result_html, method='html', encoding='unicode')

                    print("HTML prepared")
                    
                    pdf_filename = file.replace('.xml', '.pdf')
                    pdf_path = os.path.join(invoice_pdf_directory_path, pdf_filename)


                    page.set_content(html_string, wait_until="networkidle")

                    page.pdf(
                        path = pdf_path,
                        format='A4',
                        print_background=True
                    )

            browser.close()

    except Exception as e:
        print(f"Error occured: {e}")


async def process_file(browser, file, transformer, parser, semaphore, invoice_xml_directory_path, invoice_pdf_directory_path):

    async with semaphore:
        xml_path = os.path.join(invoice_xml_directory_path, file)

        xml_dom = etree.parse(xml_path, parser=parser)

        result_html = transformer(xml_dom)
        html_string = etree.tostring(result_html, method='html', encoding='unicode')

        page = await browser.new_page()
        await page.set_content(html_string, wait_until="load")

        pdf_filename = file.replace('.xml', '.pdf')
        pdf_path = os.path.join(invoice_pdf_directory_path, pdf_filename)

        await page.pdf(
            path = pdf_path,
            format='A4',
            print_background=True
        )

        await page.close()

        print(f"Ready: {file}")


# Asynchroniczna (szybsza wersja)
async def save_xml_as_pdf_async(invoice_xml_directory_path, invoice_pdf_directory_path):
    start_time = time.time()

    parser = etree.XMLParser(no_network=False, resolve_entities=True)
    access_control = etree.XSLTAccessControl(read_network=True, read_file=True)

    xsl_dom = etree.parse(XSL_STYLE_FILE, parser=parser)
    transformer = etree.XSLT(xsl_dom, access_control=access_control)

    semaphore = asyncio.Semaphore(MAXIMUM_NUMBER_OF_ASYNCHRONOUS_PROCESSES)

    end_time = time.time()

    print(f"1. Process Execution time: {end_time - start_time} seconds")

    start_time = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        tasks = []

        for file in os.listdir(invoice_xml_directory_path):
            if file.endswith('.xml'):
                tasks.append(
                    process_file(browser, file, transformer, parser, semaphore, invoice_xml_directory_path, invoice_pdf_directory_path)
                )

        if tasks:
            await asyncio.gather(*tasks)
        
        await browser.close()

    end_time = time.time()

    print(f"2. Process Execution time: {end_time - start_time} seconds")

if __name__ == "__main__":
    
    start_time = time.time()

    print("Invoice preparation started")

    with open(constants.DATA_FILE_PATH, 'r') as file:
        entities = json.load(file)

    for entity in entities:

        name = entity['name']

        archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.ARCHIVE_DIRECTORY}"
        old_archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.OLD_ARCHIVE_DIRECTORY}"
        invoice_xml_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_XML_DIRECTORY}"
        invoice_pdf_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_PDF_DIRECTORY}"

        print(f"Processing invoices belonging to: {name}")

        print("\n1. Unzipping the archive with invoices")
        is_archive_present = extract_files(archive_directory_path, old_archive_directory_path, invoice_xml_directory_path)

        if is_archive_present:

            print("\n2. Editing the XML files so that it is possible to visualize them")
            edit_xml_files(invoice_xml_directory_path)

            print("\n3. Save XML invoices as PDF")
            asyncio.run(save_xml_as_pdf_async(invoice_xml_directory_path, invoice_pdf_directory_path))

    end_time = time.time()

    print(f"\nTotal execution time: {end_time - start_time} seconds")