import os

import pydocumentdb.document_client as document_client
from dotenv import load_dotenv

load_dotenv()

# credentials Azure CosmoDB from .env
DB_URL = os.getenv("DB_URL")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# database and collection
config_options = {
    "COSMO_DATABASE": "options",
    "COSMO_COLLECTION": "optionsData"
}
config_voting = {
    "COSMO_DATABASE": "voting",
    "COSMO_COLLECTION": "votingData"
}

# connection to database Azure CosmoDB
client = document_client.DocumentClient(DB_URL, {"masterKey": DB_PASSWORD})


def get_docs_from_db(config):
    """
    Function for get documents from collection in the database
    :param config: dictionary with values of database's name and collections's name
    :return: list of documents
    """
    # select database
    db_id = config["COSMO_DATABASE"]
    db_query = "select * from r where r.id = '{0}'".format(db_id)
    db = list(client.QueryDatabases(db_query))[0]
    db_link = db["_self"]

    # select collection
    coll_id = config["COSMO_COLLECTION"]
    coll_query = "select * from r where r.id = '{0}'".format(coll_id)
    coll = list(client.QueryCollections(db_link, coll_query))[0]
    coll_link = coll["_self"]

    # get needed fields
    docs = list(client.ReadDocuments(coll_link))

    return docs


# Put data to CosmoDB
def put_docs_to_db(doc, config):
    """
    Put document to the database
    :param doc: document
    :param config: dictionary with values of database's name and collections's name
    :return:
    """
    values = ("dbs", config["COSMO_DATABASE"], "colls", config["COSMO_COLLECTION"])
    collection_link = "/".join(values)
    client.CreateDocument(collection_link, doc)
