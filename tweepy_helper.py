import tweepy as tw
import pandas as pd
from textblob import TextBlob
import itertools
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import geopandas as gpd
import tweepy as tw
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dash.dependencies import Input, Output
from helpers import *

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
    place_df = pd.DataFrame(columns=["tweet", "place"])

    #natalias
    sentiments = []

    tweets = tw.Cursor(api.search, count=500, q=search_string,
                              show_user=True, tweet_mode="extended").items(n_items)

    for tweet in tweets:
        sentiments.append({'text': tweet.full_text, 'date': tweet.created_at})
        place_df = place_df.append({"tweet":tweet.full_text,"place":tweet.user.location},ignore_index = True)
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

    #wordcloud stuff

    tweets_df = pd.DataFrame.from_dict(sentiments)
    tweets_df.text = clean_tweets(tweets_df.text)

    scores = []
    for i in range(tweets_df['text'].shape[0]):
        compound = SentimentIntensityAnalyzer().polarity_scores(tweets_df.text[i])['compound']
        positive = SentimentIntensityAnalyzer().polarity_scores(tweets_df.text[i])['pos']
        neutral = SentimentIntensityAnalyzer().polarity_scores(tweets_df.text[i])['neu']
        negative = SentimentIntensityAnalyzer().polarity_scores(tweets_df.text[i])['neg']
        scores.append({
            'compound': compound,
            'positive': positive,
            'neutral': neutral,
            'negative': negative
        })


    for i, row in tweets_df.iterrows():
        tweets_df.at[i, "analysis"] = analyze(row.text)

    scores_df = pd.DataFrame.from_dict(scores)
    fig_word_cloud = word_cloud(tweets_df.text)

    df = tweets_df.analysis
    histfig = px.histogram(df, nbins=5)


    return node_df, edge_df, place_df, histfig
