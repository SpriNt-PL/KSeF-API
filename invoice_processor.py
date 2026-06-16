import json
import textwrap
import os
import shutil
import re
import time
import asyncio
from zipfile import ZipFile
from playwright.async_api import async_playwright
from lxml import etree

import constants

XML_FIRST_LINE = '<?xml version="1.0" encoding="UTF-8"?>'
XML_SECOND_LINE = '<?xml-stylesheet type="text/xsl" href="Scheme/styl.xsl"?>'

MAXIMUM_NUMBER_OF_ASYNCHRONOUS_PROCESSES = 4

class InvoiceProcessor:
    def __init__(self, name, supervisor_name):
        # Entity details
        self._name = name
        self._supervisor_name = supervisor_name

        self._is_archive_present = None
        self._new_files = []


        # Paths to directories
        self._archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.ARCHIVE_DIRECTORY}"
        self._old_archive_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.OLD_ARCHIVE_DIRECTORY}"
        self._invoice_xml_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_XML_DIRECTORY}"
        self._invoice_pdf_directory_path = f"{constants.INVOICE_DIRECTORY_PATH}/{name}/{constants.INVOICE_PDF_DIRECTORY}"
        self._supervisor_directory_path = f"{constants.OUTPUT_DIRECTORY_PATH}/{supervisor_name}"

    # Returns a list of only new files which are not present in the destination directory
    def _choose_only_new_files(self, zip_file_list, destination_file_list):
        new_files = list(set(zip_file_list).difference(destination_file_list))

        return new_files


    def _extract_files(self):
        all_items = os.listdir(self._archive_directory_path)

        # Filtering only zip files (just in case something with other extension appears there)
        zip_files = [f for f in all_items if f.endswith('.zip')]

        if not zip_files:
            print("Folder is empty (no zip files found)!")
            return False

        invoice_xml_directory_file_list = os.listdir(self._invoice_xml_directory_path)
        all_new_files = []

        for zip_file in zip_files:

            source_archive_path = os.path.join(self._archive_directory_path, zip_file)
            print(f"Processing archive: {source_archive_path}")
            
            with ZipFile(source_archive_path, 'r') as zip_object:
                # Obtaining list of only new files and extracting them into invoice_xml_directory
                file_list = zip_object.namelist()
                new_files = self._choose_only_new_files(file_list, invoice_xml_directory_file_list)
                for file in new_files:
                    zip_object.extract(file, path=self._invoice_xml_directory_path)

            all_new_files.extend(new_files)
            invoice_xml_directory_file_list.extend(new_files)

            # Moving extracted zip to the archive 
            destination_archive_path = os.path.join(self._old_archive_directory_path, zip_file)
            shutil.move(source_archive_path, destination_archive_path)
            print(f"Archive moved to {self._old_archive_directory_path}")


        if len(all_new_files) > 0:
            print(f"Total of new files extracted: {len(all_new_files)}")
        else:
            print("No new files found in any of the archives.")

        self._new_files = all_new_files

        return True
    

    def _add_proper_xml_headers(self):
        print(f"Editing following files: {self._new_files}")

        if not self._new_files:
            print("No new files to edit.")
            return
        
        for file in self._new_files:
            if file.endswith('.xml') and file != 'wyroznik.xml':

                filepath = os.path.join(self._invoice_xml_directory_path, file)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.readlines()

                # Logic which ensures that header will be added in a proper way
                if content and content[0].startswith('<?xml'):
                    
                    # Finding index of '>'
                    end_index = content[0].find('>')

                    # Cutting everything before '>' character including it
                    if end_index != -1:
                        content[0] = content[0][end_index + 1:]

                # Adding new header
                new_content = [XML_FIRST_LINE + '\n' + XML_SECOND_LINE + '\n'] + content

                # Saving edited file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(new_content)

        print("Files successfully edited")

    
    def _add_ksef_number(self):
        print(f"Editing following files: {self._new_files}")

        for file in self._new_files:
            if file.endswith('.xml') and file != 'wyroznik.xml':
                numer_ksef = os.path.splitext(file)[0]
                filepath = os.path.join(self._invoice_xml_directory_path, file)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                pattern = r"(</(([a-zA-Z0-9]+):)?KodFormularza>)"

                match = re.search(pattern, content)

                if match:
                    full_closing_tag = match.group(1)
                    prefix_with_colon = match.group(2) if match.group(2) else ""

                    new_tag = f"<{prefix_with_colon}NumerKSeF>{numer_ksef}</{prefix_with_colon}NumerKSeF>"

                    separator = "\n    " if "\n" in content else ""

                    replacement = f"{full_closing_tag}{separator}{new_tag}"

                    new_content = content.replace(full_closing_tag, replacement, 1)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                else:
                    print(f"Error KodFormularza not found {file}")


    async def _process_file(self, context, file, transformer, parser, semaphore):

        async with semaphore:
            xml_path = os.path.join(self._invoice_xml_directory_path, file)

            xml_dom = etree.parse(xml_path, parser=parser)

            result_html = transformer(xml_dom)
            html_string = etree.tostring(result_html, method='html', encoding='unicode')

            page = await context.new_page()

            try:

                await page.set_content(html_string, wait_until="domcontentloaded")

                pdf_bytes = await page.pdf(
                    format='A4',
                    print_background=True
                )

                pdf_filename = file.replace('.xml', '.pdf')

                pdf_path_1 = os.path.join(self._invoice_pdf_directory_path, pdf_filename)
                with open(pdf_path_1, 'wb') as f:
                    f.write(pdf_bytes)

                pdf_path_2 = os.path.join(self._supervisor_directory_path, pdf_filename)
                with open(pdf_path_2, 'wb') as f:
                    f.write(pdf_bytes)

                print(f"Ready: {file}")

            except Exception as e:
                print(f"Error in file {file}: {e}")

        
            finally:
                await page.close()

    
    async def _save_xml_as_pdf_async(self):
        start_time = time.time()

        parser = etree.XMLParser(no_network=False, resolve_entities=True)
        access_control = etree.XSLTAccessControl(read_network=True, read_file=True)

        xsl_dom = etree.parse(constants.XSL_STYLE_FILE, parser=parser)
        transformer = etree.XSLT(xsl_dom, access_control=access_control)

        semaphore = asyncio.Semaphore(MAXIMUM_NUMBER_OF_ASYNCHRONOUS_PROCESSES)

        end_time = time.time()

        print(f"1. Process Execution time: {end_time - start_time} seconds")

        start_time = time.time()
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, 
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--single-process"]
            )

            try:
                async with await browser.new_context() as context:
                    
                    tasks = []

                    for file in self._new_files:
                        if file.endswith('.xml'):
                            tasks.append(
                                self._process_file(context, file, transformer, parser, semaphore)
                            )

                    print("Collecting all concurrent processes")
                    if tasks:
                        await asyncio.gather(*tasks)

                    print("All tasks finished inside context.")

            finally:
                print("Force-closing the browser...")
                try:
                    start_time = time.time()

                    await asyncio.wait_for(context.close(), timeout=10.0)
                    await asyncio.wait_for(browser.close(), timeout=10.0)

                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f"Browser closed in {elapsed_time:.2f}.")
                except asyncio.TimeoutError:
                    print("Browser close timed out - proceeding anyway.")

        end_time = time.time()

        print(f"2. Process Execution time: {end_time - start_time} seconds")

    
    def prepare_invoices(self):
        communicate = f"""
        =================================================================
        Processing invoices belonging to: {self._name}
        =================================================================
        """

        print(textwrap.dedent(communicate))

        print("1. Unzipping the archive with invoices")
        is_content = self._extract_files()

        if not is_content:
            return False
        
        print("\n2. Editing the XML files so that it is possible to visualize them")
        self._add_proper_xml_headers()

        print("\n3. Add KSeF number to each new invoice")
        self._add_ksef_number()

        print("\n4. Save XML invoices as PDF")
        asyncio.run(self._save_xml_as_pdf_async())



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