# Catalog Web App 

## Prerequisites
- python installed
- flask installed `(pip install flask)`
- sqlalchemy installed `(pip install sqlalchemy)`
- oauth2client installed `(pip install oauth2client)`
- httplib2 installed `(pip install httplib2)`
- requests installed `(pip install requests)`

## Running
In order to Start the webapp execute the catalog.py file with python. A database sample (catalog.db) is given. It is possible to start with an empty db, in order to do this, remove the catalog.db file and execute database-init.py. This will create an empty database. Since you need categories to use the app, the least you have to do now, is to edit the init.py file to create at least one category.

## Endpoints
A Json endpoint is provided under the address:"localhost:8000/catalog.json"

## Credits
Most of the code is taken from the udacity courses, related to this project.