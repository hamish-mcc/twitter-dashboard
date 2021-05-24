import re
import tweepy as tw
import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob

# Authentification to access twitter API
consumer_key="5AfsZ6y76lBk51bl5VxKRKr9z"
consumer_secret="kPvYIeJUHep4gMm4nCaqgLDV1XVBk21X64PU68yVgPcIpr1239"
access_token="3051136448-tXFWPFzTi6kh4Y6dnnOlIbsl0xknTmie8TGrONJ"
access_token_secret="3YdVrZoV4QgJmQGfc1WSdCkownTyq0k23tGsxmPCTyRSQ"
def initialize():
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify = True)
    return api

# Cleaning the tweets
def remove_pattern(input_txt, pattern):
    r = re.findall(pattern, input_txt)
    for i in r:
        input_txt = re.sub(i, '', input_txt)        
    return input_txt

def clean_tweets(tweets):
    #remove twitter Return handles (RT @xxx:)
    tweets = np.vectorize(remove_pattern)(tweets, "RT @[\w]*:") 
    
    #remove twitter handles (@xxx)
    tweets = np.vectorize(remove_pattern)(tweets, "@[\w]*")
    
    #remove URL links (httpxxx)
    tweets = np.vectorize(remove_pattern)(tweets, "https?://[A-Za-z0-9./]*")
    
    #remove special characters, numbers, punctuations (except for #)
    tweets = np.core.defchararray.replace(tweets, "[^a-zA-Z]", " ")
    
    return tweets

def analyze(text):
    score = SentimentIntensityAnalyzer().polarity_scores(text)
    if score['neg'] >  score['pos']:
        return "negative"
    elif score['pos'] > score['neg']:
        return "positive"
    elif score['pos'] == score['neg']:
        return "neutral"