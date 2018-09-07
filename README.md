# Catalog Web App 

## Prerequisites
- python installed
- flask installed `(pip install flask)`
- sqlalchemy installed `(pip install sqlalchemy)`
- oauth2client installed `(pip install oauth2client)`
- httplib2 installed `(pip install httplib2)`
- requests installed `(pip install requests)`

## Running
In order to Start the webapp execute the catalog.py file with python and navigate to locahost:8000 in a browser of your choice. A database sample (catalog.db) is given. It is possible to start with an empty db, in order to do this:
  1. Remove the catalog.db file
  2. Execute python database-init.py. This will create an empty database.
  3. Create Dummy Data with python init.py (In order to customize the initial data, you have to manipulate this file)

## Endpoints
A Json endpoint is provided under the address:"localhost:8000/catalog.json"

A Json endpoint for a single item is reachable under "localhost:8000/<category_name>/<item_name>.json".
Correct capitalization is important.

## Credits
Most of the code is taken from the udacity courses, related to this project.
