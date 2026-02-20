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

Filtrowanie faktur:
Ściąganie z ostatnich 21 dni z filtrem

Nowa struktura z uwzględnieniem administratorów


