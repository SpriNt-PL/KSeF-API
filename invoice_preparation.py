import os
import shutil
import asyncio
import time
from zipfile import ZipFile
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from lxml import etree

#RENDER_TIME_DELAY = 1000 # miliseconds

ARCHIVE_FOLDER = './Invoices/Archives'
EXTRACTED_FOLDER = './Invoices/Extracted'
OLD_ARCHIVE_FOLDER = './Invoices/Old_Archives'
PREPARED_XML_INVOICES_FOLDER = './Invoices/Prepared_XML_Invoices'
PDF_INVOICES_FOLDER = './Invoices/PDF_Invoices'

XML_FIRST_LINE = '<?xml version="1.0" encoding="UTF-8"?>'
XML_SECOND_LINE = '<?xml-stylesheet type="text/xsl" href="Scheme/styl.xsl"?>'

XSL_STYLE_FILE = './Invoices/Prepared_XML_Invoices/Scheme/styl.xsl'

MAXIMUM_NUMBER_OF_ASYNCHRONOUS_PROCESSES = 10

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


# Sychroniczna (pierwsza wersja)
def save_xml_as_pdf():
    
    try:
        parser = etree.XMLParser(no_network=False, resolve_entities=True)
        access_control = etree.XSLTAccessControl(read_network=True, read_file=True)

        with sync_playwright() as p:

            browser = p.chromium.launch(args=['--allow-file-access-from-files'])
            page = browser.new_page()

            xsl_dom = etree.parse(XSL_STYLE_FILE, parser=parser)
            transform = etree.XSLT(xsl_dom, access_control=access_control)

            for file in os.listdir(PREPARED_XML_INVOICES_FOLDER):
                
                if file.endswith('.xml'):
                    print(f"Preparing PDF for {file}")

                    xml_path = os.path.join(PREPARED_XML_INVOICES_FOLDER, file)

                    xml_dom = etree.parse(xml_path, parser=parser)

                    result_html = transform(xml_dom)
                    html_string = etree.tostring(result_html, method='html', encoding='unicode')

                    print("HTML prepared")
                    
                    pdf_filename = file.replace('.xml', '.pdf')
                    pdf_path = os.path.join(PDF_INVOICES_FOLDER, pdf_filename)


                    page.set_content(html_string, wait_until="networkidle")

                    page.pdf(
                        path = pdf_path,
                        format='A4',
                        print_background=True
                    )

            browser.close()

    except Exception as e:
        print(f"Error occured: {e}")


async def process_file(browser, file, transformer, parser, semaphore):
    
    async with semaphore:
        xml_path = os.path.join(PREPARED_XML_INVOICES_FOLDER, file)

        xml_dom = etree.parse(xml_path, parser=parser)

        result_html = transformer(xml_dom)
        html_string = etree.tostring(result_html, method='html', encoding='unicode')

        page = await browser.new_page()
        await page.set_content(html_string, wait_until="load")

        pdf_filename = file.replace('.xml', '.pdf')
        pdf_path = os.path.join(PDF_INVOICES_FOLDER, pdf_filename)

        await page.pdf(
            path = pdf_path,
            format='A4',
            print_background=True
        )

        await page.close()

        print(f"Ready: {file}")


# Asynchroniczna (szybsza wersja)
async def save_xml_as_pdf_async():
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

        for file in os.listdir(PREPARED_XML_INVOICES_FOLDER):
            if file.endswith('.xml'):
                tasks.append(
                    process_file(browser, file, transformer, parser, semaphore)
                )

        if tasks:
            await asyncio.gather(*tasks)
        
        await browser.close()

    end_time = time.time()

    print(f"2. Process Execution time: {end_time - start_time} seconds")

if __name__ == "__main__":
    start_time = time.time()

    print("Invoice preparation started")

    print("\n1. Unzipping the archive with invoices")
    extract_files()

    print("\n2. Editing the XML files so that it is possible to visualize them")
    edit_xml_files()

    print("\n3. Save XML invoices as PDF")
    asyncio.run(save_xml_as_pdf_async())

    end_time = time.time()

    print(f"\nTotal execution time: {end_time - start_time} seconds")

