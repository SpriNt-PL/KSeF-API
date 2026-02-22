from directories_preparation import prepare_directories
from ksef_api import download_invoices
from invoice_preparation import prepare_invoices

prepare_directories()
download_invoices()
prepare_invoices()