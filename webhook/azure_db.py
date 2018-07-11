import os

import pydocumentdb.document_client as document_client
from dotenv import load_dotenv

load_dotenv()

# credentials Azure CosmoDB from .env
AZURE_URL = os.getenv("AZURE_URL")
AZURE_PASSWORD = os.getenv("AZURE_PASSWORD")

# database and collection
config = {
    "MONGO_DATABASE": "options",
    "MONGO_COLLECTION": "optionsData"
}


def get_docs():
    # connection to database Azure CosmoDB
    client = document_client.DocumentClient(AZURE_URL, {"masterKey": AZURE_PASSWORD})

    # select database
    db_id = config["MONGO_DATABASE"]
    db_query = "select * from r where r.id = '{0}'".format(db_id)
    db = list(client.QueryDatabases(db_query))[0]
    db_link = db["_self"]

    # select collection
    coll_id = config["MONGO_COLLECTION"]
    coll_query = "select * from r where r.id = '{0}'".format(coll_id)
    coll = list(client.QueryCollections(db_link, coll_query))[0]
    coll_link = coll["_self"]

    # get needed fields
    docs = list(client.ReadDocuments(coll_link))

    return docs
