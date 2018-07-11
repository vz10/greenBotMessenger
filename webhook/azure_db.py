import os

import pydocumentdb.document_client as document_client
from dotenv import load_dotenv

load_dotenv()

# credentials Azure CosmoDB from .env
AZURE_URL = os.getenv("AZURE_URL")
AZURE_PASSWORD = os.getenv("AZURE_PASSWORD")

# database and collection
config_options = {
    "MONGO_DATABASE": "options",
    "MONGO_COLLECTION": "optionsData"
}
config_vote = {
    "MONGO_DATABASE": "voting",
    "MONGO_COLLECTION": "votingData"
}

# connection to database Azure CosmoDB
client = document_client.DocumentClient(AZURE_URL, {"masterKey": AZURE_PASSWORD})


def get_docs_from_db(config):
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


# Put data to CosmoDB
def put_data_db(doc):
    values = ("dbs", config_vote["MONGO_DATABASE"], "colls", config_vote["MONGO_COLLECTION"])
    collection_link = "/".join(values)
    client.CreateDocument(collection_link, doc)
