import pymongo
import mysql.connector
from datetime import datetime, timedelta
from mysql.connector import Error
from .connections import get_mysql_conn, get_mongodb_conn

class TwitterQueries:
    def __init__(self):
        self.mysql_connection = get_mysql_conn()
        self.mongo_db = get_mongodb_conn(collection="tweet_data")

    def get_user_ids_by_name(self, user_name):
        if not self.mysql_connection:
            print("MySQL connection is not established.")
            return []
        try:
            query = "SELECT id_str FROM users WHERE name LIKE %s ESCAPE '\\';"
            with self.mysql_connection.cursor() as cursor:
                search_pattern = f"%{user_name.replace('%', '\\%').replace('_', '\\_')}%"
                cursor.execute(query, (search_pattern,))
                results = cursor.fetchall()
                return [row[0] for row in results]
        except mysql.connector.Error as e:
            print(f"Error fetching user IDs: {e}")
            return []

    def fetch_tweets_by_criteria(self, query, sort_fields=None, time_frame=None):
        if not self.mongo_db:
            print("MongoDB connection is not established.")
            return []
        if time_frame:
            now = datetime.now()
            time_delta = {
                '1day': now - timedelta(days=1),
                '1week': now - timedelta(weeks=1),
                '1month': now - timedelta(days=30)
            }.get(time_frame, now)
            query["created_at"] = {"$gte": time_delta}

        sort_criteria = [(field, pymongo.DESCENDING if direction == 'desc' else pymongo.ASCENDING) 
                         for field, direction in (sort_fields.items() if sort_fields else [('created_at', 'desc')])]
        return list(self.mongo_db.tweet_data.find(query).sort(sort_criteria))

    def search_tweets_by_username(self, username, sort_fields=None, time_frame=None):
        user_ids = self.get_user_ids_by_name(username)
        if not user_ids:
            print(f"No users found for the name: {username}")
            return []
        return self.fetch_tweets_by_criteria({"user": {"$in": user_ids}}, sort_fields, time_frame)

    def search_tweets_by_hashtag(self, hashtag_query, sort_fields=None, time_frame=None):
        tweet_ids = self.fetch_tweet_ids_by_hashtag(hashtag_query)
        if not tweet_ids:
            print("No tweets found for hashtag:", hashtag_query)
            return []
        return self.fetch_tweets_by_criteria({"id_str": {"$in": tweet_ids}}, sort_fields, time_frame)

    def fetch_tweet_ids_by_hashtag(self, hashtag_query):
        if not self.mysql_connection:
            print("MySQL connection is not established.")
            return []
        try:
            query = "SELECT tweet_id FROM hashtags WHERE hashtag = %s;"
            with self.mysql_connection.cursor() as cursor:
                cursor.execute(query, (hashtag_query,))
                results = cursor.fetchall()
                return [result[0] for result in results]
        except Error as e:
            print(f"Error fetching tweet IDs: {e}")
            return []

    def fetch_and_display_tweets(self, search_term, search_type='hashtag', sort_fields=None, time_frame=None):
        tweets = []
        if search_type == 'hashtag':
            tweets = self.search_tweets_by_hashtag(search_term, sort_fields, time_frame)
        elif search_type == 'username':
            tweets = self.search_tweets_by_username(search_term, sort_fields, time_frame)
        else:
            print(f"Invalid search type specified: {search_type}")

        if tweets:
            print(f"Tweets for {search_type} '{search_term}':")
            for tweet in tweets:
                print(tweet)
        else:
            print(f"No tweets found for {search_type} '{search_term}'.")

    def search_and_sort_users(self, search_term, sort_by='followers_count'):
        if not self.mysql_connection:
            print("MySQL connection is not established.")
            return []
        try:
            query = "SELECT id_str, name, followers_count, last_post_timestamp FROM users WHERE name LIKE %s ORDER BY " + sort_by + " DESC;"
            with self.mysql_connection.cursor() as cursor:
                search_pattern = f"%{search_term.replace('%', '\\%').replace('_', '\\_')}%"
                cursor.execute(query, (search_pattern,))
                results = cursor.fetchall()
                return [{'user_id': row[0], 'name': row[1], 'followers_count': row[2], 'last_post_timestamp': row[3]} for row in results]
        except mysql.connector.Error as e:
            print(f"Error searching and sorting users: {e}")
            return []
