import os

import pydocumentdb.document_client as document_client
from dotenv import load_dotenv

load_dotenv()

# credentials Azure CosmosDB from .env
DB_URL = os.getenv("DB_URL")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# database and collection
config_options = {
    "COSMOS_DATABASE": "options",
    "COSMOS_COLLECTION": "optionsData"
}
config_voting = {
    "COSMOS_DATABASE": "voting",
    "COSMOS_COLLECTION": "votingData"
}

# connection to database Azure CosmosDB
client = document_client.DocumentClient(DB_URL, {"masterKey": DB_PASSWORD})


def get_docs_from_db(config):
    """
    Function for get documents from collection in the database
    :param config: dictionary with values of database's name and collections's name
    :return: list of documents
    """
    values = ("dbs", config["COSMOS_DATABASE"], "colls", config["COSMOS_COLLECTION"])
    collection_link = "/".join(values)
    # get needed fields
    docs = list(client.ReadDocuments(collection_link))

    return docs


def put_docs_to_db(doc, config):
    """
    Put document to the database
    :param doc: document
    :param config: dictionary with values of database's name and collections's name
    :return:
    """
    values = ("dbs", config["COSMOS_DATABASE"], "colls", config["COSMOS_COLLECTION"])
    collection_link = "/".join(values)
    client.CreateDocument(collection_link, doc)


def quick_replies():
    """
    Get options for voting from database and create a dictionary with quick replies
    :return: dictionary with quick replies
    """
    docs = get_docs_from_db(config_options)
    quick_replies = []
    for doc in docs:
        reply = {
            "content_type": "text",
            "title": str(doc["title"]),
            "payload": str(doc["payload"])
        }
        quick_replies.append(reply)
    return quick_replies


def results_voting(config):
    """
    Get a count of each vote and create a result of voting
    :param config: dictionary with values of database's name and collections's name
    :return: string with results of voting
    """
    values = ("dbs", config["COSMOS_DATABASE"], "colls", config["COSMOS_COLLECTION"])
    collection_link = "/".join(values)
    docs = quick_replies()
    result = ""
    for doc in docs:
        query = "SELECT VALUE COUNT(1) FROM Votings v WHERE v.vote = '{0}'".format(doc["title"])
        count = list(client.QueryDocuments(collection_link, query))[0]
        result += doc["title"] + " = " + str(count) + "\n"
    return result
