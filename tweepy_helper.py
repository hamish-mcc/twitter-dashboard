import tweepy as tw
import pandas as pd
from textblob import TextBlob
import itertools
import json

# Load keys from configuration
with open("credentials.json") as credentials:
    keys = json.load(credentials)

consumer_key = keys["api_key"]
consumer_secret = keys["api_secret_key"]
access_token = keys["access_token"]
access_token_secret = keys["access_token_secret"]

# Complete OAUTH with API
auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tw.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


# Gets a number of tweets and returns dataframes for nodes (hashtags) and edges (hashtag pairs)
def get_tweets(search_string, n_items):
    node_df = pd.DataFrame(columns=["tag", "sentiment"])
    edge_df = pd.DataFrame(columns=["tag", "associated_tag"])

    tweets = tw.Cursor(api.search, count=500, q=search_string,
                              show_user=True, tweet_mode="extended").items(n_items)

    for tweet in tweets:
        try:
            temp_tags = []
            for _, tag in enumerate(tweet.entities.get('hashtags')):
                temp_tags.append(tag["text"])
                node_df = node_df.append({"tag": tag["text"], "sentiment": TextBlob(
                    tweet.full_text).polarity}, ignore_index=True)
            res = list(itertools.combinations(temp_tags, 2))
            if res != []:
                for pair in res:
                    edge_df = edge_df.append(
                        {"tag": pair[0], "associated_tag": pair[1]}, ignore_index=True)
        except:
            pass

    return node_df, edge_df
