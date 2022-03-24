# Degiro Screener

## About
Build a list of cherry picked stocks from the DEGIRO broker, based on the API https://github.com/Chavithra/degiro-connector


## "degiro_screener.ipynb" on Jupyter Lab
Please export the environment variables GT_DG_USERNAME and GT_DG_PASSWORD as your DEGIRO login and password, before launching Jupyter Lab.

- The first block downloads and put in cache the data from DEGIRO and eventually Yahoo! finance, then build the raw dataframe of all stocks. You should get as little as 15000 stocks there!
- The second block perform the ranking in order to establish the hall of fame based on a secret sauce. All you CPUs will be used during the computation, it may be long depending on your gear.
- The last block filters out and displays the final result. __Please read the "readme.rtf" to get the meaning of the columns.__

## Cache maintenance
Downloaded data stay forever to avoid to much load on DEGIRO. You have to remove the cache manually ( rm .cachedb* )  to get fresh data.
