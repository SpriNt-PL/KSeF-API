import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

DATA_DIRECTORY_PATH = Path(config['paths']['data_directory'])
SERVICE_INVOICE_DIRECTORY_PATH = Path(config['paths']['service_invoice_directory'])
MAIN_INVOICE_DIRECTORY_PATH = Path(config['paths']['main_invoice_directory'])
REPORT_PATH = Path(config['paths']['report_file'])

DATA_FILE_PATH = DATA_DIRECTORY_PATH / 'data.json'
XSL_STYLE_FILE = DATA_DIRECTORY_PATH / 'Scheme' / 'styl.xsl'
CERTIFICATE_DIRECTORY = DATA_DIRECTORY_PATH / 'Certificate'

ARCHIVE_DIRECTORY = 'Archive'
INVOICE_XML_DIRECTORY = 'Invoice_XML'
INVOICE_PDF_DIRECTORY = 'Invoice_PDF'
OLD_ARCHIVE_DIRECTORY = 'Old_Archive'