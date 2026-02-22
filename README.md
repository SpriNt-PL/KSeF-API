# KSeF-API

Fix:
Problem z:
4. Downloading access tokens
Response code: 400
Traceback (most recent call last):
  File "C:\Moje\KSeF_API\KSeF-API\script.py", line 337, in <module>
    access_token, refresh_token = download_access_tokens(session_token)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot unpack non-iterable NoneType object

Muszę zabezpieczyć sytuacje błędów w api
Tutaj powyżej api nie zwróciło kodu 200 więc nie uzyskałem tokenów


