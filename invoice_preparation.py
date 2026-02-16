import os
import shutil
import asyncio
import timeit
from zipfile import ZipFile
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
    
    try:
        parser = etree.XMLParser(no_network=False, resolve_entities=True)
        access_control = etree.XSLTAccessControl(read_network=True, read_file=True)

        async with async_playwright() as p:

            browser = await p.chromium.launch(args=['--allow-file-access-from-files'])
            page = await browser.new_page()

            for file in os.listdir(PREPARED_XML_INVOICES_FOLDER):
                
                if file.endswith('.xml'):
                    print(f"Preparing PDF for {file}")

                    xml_path = os.path.join(PREPARED_XML_INVOICES_FOLDER, file)

                    xml_dom = etree.parse(xml_path, parser=parser)
                    xsl_dom = etree.parse(XSL_STYLE_FILE, parser=parser)

                    transform = etree.XSLT(xsl_dom, access_control=access_control)

                    result_html = transform(xml_dom)
                    html_string = etree.tostring(result_html, method='html', encoding='unicode')

                    print("HTML prepared")
                    
                    pdf_filename = file.replace('.xml', '.pdf')
                    pdf_path = os.path.join(PDF_INVOICES_FOLDER, pdf_filename)


                    await page.set_content(html_string, wait_until="networkidle")

                    await page.pdf(
                        path = pdf_path,
                        format='A4',
                        print_background=True
                    )

            await browser.close()

    except Exception as e:
        print(f"Error occured: {e}")




if __name__ == "__main__":
    start_time = timeit.timeit()

    print("Invoice preparation started")

    print("\n 1. Unzipping the archive with invoices")
    extract_files()

    print("\n 2. Editing the XML files so that it is possible to visualize them")
    edit_xml_files()

    print("\n 3. Save XML invoices as PDF")
    asyncio.run(save_xml_as_pdf())

    end_time = timeit.timeit()

    print(f"Execution time: {end_time - start_time} seconds")

