# KSeF API Invoice Processor & Certificate Authorization

[![KSeF API](https://img.shields.io/badge/KSeF--API-v2.0-green.svg)](https://ksef.podatki.gov.pl/)

An automated Python pipeline designed for Poland's **National e-Invoice System (KSeF - Krajowy System e-Faktur)**. This tool automates authorization using client certificates, batch invoice package downloads, XML extraction, deduplication, and high-fidelity rendering into human-readable **PDF documents** via XSLT transformations and Playwright (headless Chromium).

## Key Features

* **Certificate Authorization & API Integration**: Securely authenticates with the official KSeF API environment using X.509 client certificates and API tokens.
* **Automated Batch Download**: Retrieves and unpacks bulk e-invoice archives (`.zip` / `.xml`) for multiple tax entities (NIP).
* **XML to PDF Rendering**: Uses XSLT stylesheets (`styl.xsl`, `schemat.xsd`, `WspolneSzablonyWizualizacji`) and Playwright Chromium to render pixel-perfect PDF versions of official Polish structured invoices.
* **Intelligent Deduplication**: Tracks previously processed invoice identifiers to ensure zero duplicate PDF generation or downstream double-processing.
* **Structured Directory Management**: Automatically organizes downloaded packages, extracted XMLs, generated PDFs, and log archives into clean entity-specific directory trees.
* **Multi-Entity & Multi-Supervisor Support**: Handles multiple organizations/NIPs under different management profiles seamlessly via unified JSON configuration.

## Getting Started

### Option A: Pre-built Executable (`.exe`)
1. **Download the Release**:
   Go to the [Releases](../../releases) page and download the latest `Invoice_Downloader.zip` archive.

2. **Extract Archives**:
   Unpack the `.zip` file. You will find the pre-configured folder structure ready to use:
   ```text
   ├── Invoice Downloader.exe
   ├── config.ini
   └── Data/
       ├── data.json
       ├── Certificate/   <-- Place your .crt and .key files here
       └── Scheme/        <-- Contains pre-downloaded XSD / XSLT files
    ```

3. **Fill Configuration**:
    *   Open `config.ini` and set your certificate password.
    *   Open `Data/data.json` and fill in your NIP and API Token details.
    *   Place your `.crt` and `.key` certificate files into `Data/Certificate/`.

4. **Run**  
    Double-click `Invoice Downloader.exe` or execute via terminal:
    ```bash
    Invoice Downloader.exe
    ```

### Option B: Run from Source (Python)

### Prerequisites 
* **Python 3.8+**
* Active **KSeF API Certificate / Token** (Test or Production environment)

### Libraries
* Create virtual environment (Optional):
    ```bash
    python -m venv .venv
    ```
* Install the following libraries using this:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration Setup

1. **Create Directory Structure**  
   Create a directory named `Data` in your root folder and subfolders named `Certificate`, `Scheme` inside it:
   ```text
   ├── config.ini
   └── Data/
       ├── data.json
       ├── Certificate/
       └── Scheme/
   ```

2. **Configure data.json**  
    Inside the `Data` directory, create a `data.json` file and structure it as follows:
    ```json
    [
        {
            "supervisor": "Name Surname",
            "entity": [
                {
                    "name": "To be filled",
                    "nip": 1234567890,
                    "token": "To be filled"
                }
            ]
        }
    ]
    ```

3. **Add Certificate**  
    Inside `Data/Certificate/` directory paste two certificate files with following extensions:
    *   `.crt`
    *   `.key`


4. **Download Schema & Stylesheets**  
    Save the following files inside the `Data/Scheme/` directory:

    **XSD file:** https://ksef.podatki.gov.pl/media/oicluwg2/schemat_fa_vat_rr-1-_v1-0.xsd

    **XSLT file:** http://crd.gov.pl/wzor/2026/02/17/14164/styl.xsl

5. **Resolve Local XSLT Dependencies**  
    Download the dependent asset `WspolneSzablonyWizualizacji_v12-0E.xsl` (referenced inside `styl.xsl`) and save it to the `Data/Scheme/` directory as well. Then, open `styl.xsl` and update the external URL reference to point to your local relative file path:
    
    ```xml
    <!-- Update from remote URL to local relative path -->
    <xsl:include href="WspolneSzablonyWizualizacji_v12-0E.xsl"/>
    ```

6. **Set Constants**  
    Open constants.py and set the proper base path variable for your execution environment.

7. **Create Config File**  
    In the root folder create `config.ini` with the following structure and fill it with proper data:
    ```text
    [paths]
    ; Path direct paths to those folders / files
    data_directory = ./Data
    service_invoice_directory = ./Invoices
    main_invoice_directory = ./Faktury
    report_file = ./raport.txt
    
    [certificate]
    password = to be filled
    ```

8. **Run**  
    You are all set to run the application!
    ```bash
    py main.py
    ```
