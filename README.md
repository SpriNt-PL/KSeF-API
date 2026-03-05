Description

Pipeline designed for the National e-Invoice System (KSeF). This tool automates the retrieval of invoice packages using the API, extracts XML data, and transforms it into human-readable PDF documents.

- XML to PDF transformation: Utilizes XSLT styling and the Playwright (Chromium) engine to render readable PDF documents automaticaly

- Duplicate Prevention: Intelligent tracking system ensures that each invoice is processed only once preventing the situation where particular invoice is later processed twice.

- File management: Across whole execution all files downloaded as well as created during the process, are distributed to proper destination directories ensuring efficieny of futher manual invoice processing.

Configuration

1. Prapare "Data" directory

2. Inside this directory create "data.json" file.

3. Fill "data.json" file according to this pattern:

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

4. Inside "Data" directory create "Scheme" directory and paste there XSD and XSLT files

XSD file: https://ksef.podatki.gov.pl/media/oicluwg2/schemat_fa_vat_rr-1-_v1-0.xsd

XSLT file: http://crd.gov.pl/wzor/2026/02/17/14164/styl.xsl

5. You may need to download WspolneSzablonyWizualizacji_v12-0E.xsl file mentioned in styl.xsl file. Originaly in styl.xsl there is a link to this file however it may be required to download this file manually and paste it to the same "Scheme" directory. Then you must change the original path (url) into local (preferably relative) path.

6. Set proper base path in constants.py

7. You are ready to go!
