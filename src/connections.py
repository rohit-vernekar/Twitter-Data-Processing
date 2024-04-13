import logging.config
import time

import certifi
import mysql.connector
from pymongo import MongoClient

from config import mysql_config, mongodb_config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


def get_mysql_conn(attempts=3, delay=2):
    attempt = 1
    while attempt < attempts + 1:
        try:
            return mysql.connector.connect(host=mysql_config["host"],
                                           user=mysql_config["user"],
                                           passwd=mysql_config["password"],
                                           database=mysql_config["db"],
                                           port=mysql_config["port"])
        except (mysql.connector.Error, IOError) as err:
            if attempts == attempt:
                logger.info("Failed to connect, exiting without a connection: %s", err)
                raise err
            logger.info(
                "Connection failed: %s. Retrying (%d/%d)...",
                err,
                attempt,
                attempts - 1,
            )
            time.sleep(delay ** attempt)
            attempt += 1


def get_mongodb_conn(collection: str, attempts=3, delay=2):
    attempt = 1
    mongo_conn_string = f'mongodb+srv://{mongodb_config["user"]}:{mongodb_config["password"]}@{mongodb_config["host"]}/?retryWrites=true&w=majority&appName=Cluster0'
    while attempt < attempts + 1:
        try:
            client = MongoClient(mongo_conn_string, tlsCAFile=certifi.where())
            db = client[mongodb_config["db"]]
            tweets_collection = db[collection]
            logger.debug("Connected to MongoDB")
            return tweets_collection
        except Exception as err:
            if attempts == attempt:
                logger.info("Failed to connect to MongoDB, exiting without a connection: %s", err)
                raise err
            logger.info(
                "MongoDB Connection failed: %s. Retrying (%d/%d)...",
                err,
                attempt,
                attempts - 1,
            )
            time.sleep(delay ** attempt)
            attempt += 1
