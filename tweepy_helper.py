import itertools
import json
import pandas as pd
import tweepy as tw
from word_cloud_helper import *
from textblob import TextBlob

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

# Gets a number of tweets and returns dataframes for nodes (hashtags) and edges (hashtag pairs).
# Also returns a word cloud image and data for plotting sentiment analysis summary
def get_tweets(search_string, n_items):
    node_df = pd.DataFrame(columns=["tag", "sentiment", "location"])
    edge_df = pd.DataFrame(columns=["tag", "associated_tag"])

    sentiments = []

    tweets = tw.Cursor(api.search, count=500, q=search_string,
                       show_user=True, tweet_mode="extended").items(n_items)

    for tweet in tweets:
        sentiments.append({'text': tweet.full_text, 'date': tweet.created_at})
        try:
            temp_tags = []
            for _, tag in enumerate(tweet.entities.get('hashtags')):
                temp_tags.append(tag["text"])
                node_df = node_df.append({
                    "tag": tag["text"],
                    "sentiment": TextBlob(tweet.full_text).polarity,
                    "location": tweet.user.location
                }, ignore_index=True)
            res = list(itertools.combinations(temp_tags, 2))
            if res != []:
                for pair in res:
                    edge_df = edge_df.append({
                        "tag": pair[0],
                        "associated_tag": pair[1]
                    }, ignore_index=True)

        except:
            pass

    # Generate word cloud. Sentiment analysis using VADER
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
        tweets_df.at[i, "Sentiment"] = analyze(row.text)

    cloud_path = word_cloud(tweets_df.text)

    hist_data = []
    neg_count = tweets_df[tweets_df['Sentiment'] == 'negative'].count()
    neut_count = tweets_df[tweets_df['Sentiment'] == 'neutral'].count()
    pos_count = tweets_df[tweets_df['Sentiment'] == 'positive'].count()
    hist_data = [neg_count.Sentiment, neut_count.Sentiment, pos_count.Sentiment]

    return node_df, edge_df, cloud_path, hist_data
