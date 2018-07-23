# -*- coding: utf-8 -*-
from collections import Counter
import os

from pydocumentdb import document_client
from dotenv import load_dotenv

load_dotenv()

# credentials Azure CosmosDB from .env
DB_URL = os.getenv("DB_URL")
DB_PASSWORD = os.getenv("DB_PASSWORD")


class BaseDocument(object):
    # connection to database Azure CosmosDB
    _client = document_client.DocumentClient(DB_URL, {"masterKey": DB_PASSWORD})

    @classmethod
    def _collection_link(cls):
        values = ("dbs", cls.config["COSMOS_DATABASE"], "colls", cls.config["COSMOS_COLLECTION"])
        return "/".join(values)

    @classmethod
    def get_docs(cls):
        """
        Method for get documents from collection in the database
        :return: list of documents
        """
        docs = list(cls._client.ReadDocuments(cls._collection_link()))
        return docs

    @classmethod
    def put_docs(cls, doc):
        """
        Put document to the database
        :param doc: document
        :return:
        """
        cls._client.CreateDocument(cls._collection_link(), doc)

    @classmethod
    def upsert_docs(cls, doc):
        """
        Put document to the database
        :param doc: document
        :return:
        """
        cls._client.UpsertDocument(cls._collection_link(), doc)

    @classmethod
    def clear_docs(cls):
        """
        Delete all documents in the collection
        :return:
        """
        query = "SELECT VALUE v.id FROM Votings v"
        docs = list(cls._client.QueryDocuments(cls._collection_link(), query))
        links = list()
        [links.append("{}/docs/{}".format(cls._collection_link(), doc)) for doc in docs]
        [cls._client.DeleteDocument(link) for link in links]


class Options(BaseDocument):
    config = {
        "COSMOS_DATABASE": "options",
        "COSMOS_COLLECTION": "optionsData"
    }

    @classmethod
    def get_quick_replies(cls):
        """
        Get options for voting from database and create a dictionary with quick replies
        :return: dictionary with quick replies
        """
        docs = cls.get_docs()
        replies = []
        for doc in docs:
            reply = {
                "content_type": "text",
                "title": doc["title"],
                "payload": doc["payload"]
            }
            replies.append(reply)
        return replies


Options.QUICK_REPLIES = Options.get_quick_replies()  # To avoid request to DB every time we need options


class Vote(BaseDocument):
    config = {
        "COSMOS_DATABASE": "voting",
        "COSMOS_COLLECTION": "votingData"
    }

    @classmethod
    def _voting_counter(cls):
        query = "SELECT VALUE v.vote FROM Votings v"
        return Counter(cls._client.QueryDocuments(cls._collection_link(), query))

    @classmethod
    def get_voting_results(cls):
        """
        Get a count of each vote and create a result of voting
        :return: string with results of voting
        """
        c = cls._voting_counter()
        if c:
            total = reduce((lambda votes, count: votes + count), (count for v, count in c.most_common()))
            result = ""
            for v, c in c.most_common():
                count = "{:.1f}".format(float(c * 100) / total) if float(c * 100) % total != 0 else c * 100 / total
                result += "{}% for '{}' {}\n".format(count, v.split()[-2], v.split()[-1])
            return result
        return "No votes"

    @classmethod
    def get_top_score(cls):
        c = cls._voting_counter()
        return c.most_common(1)[0][0] if c else None

    @classmethod
    def get_user_vote_or_empty(cls, sender_id):
        """
        Get vote of user
        :param sender_id: the id of sender
        :return: dict (user vote or empty)
        """
        query = "SELECT * FROM Votings v WHERE v.sender_id = '{0}'".format(sender_id)
        res = list(cls._client.QueryDocuments(cls._collection_link(), query))
        return {} if not res else res[0]

    @classmethod
    def get_participators(cls):
        query = "SELECT VALUE v.sender_id FROM Votings v"
        return list(cls._client.QueryDocuments(cls._collection_link(), query))


class Sensors(BaseDocument):
    config = {
        "COSMOS_DATABASE": "sensors",
        "COSMOS_COLLECTION": "sensorData"
    }
    data_mapper = (
        ('Temperature', 'temperature'),
        ('Humidity', 'humidity'),
        ('Light', 'light'),
        ('CO2', 'co2'),
    )

    @classmethod
    def get_latest_data(cls):
        """
        Get sensors data
        :return: string with latest sensors data
        """
        query = "SELECT TOP 1 * FROM Sensors s ORDER BY s.timestamp DESC"
        res = list(cls._client.QueryDocuments(cls._collection_link(), query))
        if res:
            res = res[0]
            output = '\n'.join(["{}: {:.1f}".format(x[0], res[x[1]]) for x in cls.data_mapper if res.get(x[1])])
            return output
