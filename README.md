# Degiro Screener

Build a list of cherry picked stoks from DEGIRO broker.
Please export the environment variables GT_DG_USERNAME and GT_DG_PASSWORD as your DEGIRO login and password, before launching Jupyter Lab.
The computation may be long, please be patient.

The first block downloads and put in cache the data from DEGIRO and eventually Yahoo! finance, then build the raw dataframe of all stocks.
The second block perform the ranking in order to establish the hall of fame based on a secret sauce.
The last block filters out and displays the final result. Please read the "readme.rtf" to get the meaning of the columns.
