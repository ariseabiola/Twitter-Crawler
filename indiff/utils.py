"""Module contains functions for different processes.
From reading a file from a csv_file to building a graph.
"""

import datetime
import os
import pickle
import random
import re
import string
from itertools import count

import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from sqlitedict import SqliteDict
from textblob import TextBlob


def get_keywords_from_file(keywords_file):
    """[summary]

    Arguments:
        keywords_file {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    keywords = set()

    with open(keywords_file, 'r') as f:
        for line in f:
            keywords.add(line.lower())

    return keywords


def split_text(tweet_text):
    # this is probably where you are going to do the whole word frequency thing
    tokenizer = TweetTokenizer(strip_handles=True)
    pattern_1 = r'https?://[^\s<>"]+|www\.[^\s<>"]+|\S+@\S+'
    pattern_2 = r'\w+'

    prog_1 = re.compile(pattern_1)
    prog_2 = re.compile(pattern_2)

    tokens = set(tokenizer.tokenize(tweet_text))
    no_links = {token.lower() for token in tokens if not prog_1.match(token)}
    no_pun = {token for token in no_links if prog_2.match(token)}
    final = {token for token in no_pun if token not in stopwords.words(
        'english') + ['rt']}

    # returns a list of keywords in one message
    # consider return a generator maybe?
    return list(final)


def clean_tweet(tweet):
    '''
    Utility function to clean tweet text by removing links, special characters
    using simple regex statements.
    '''
    return ' '.join(re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)",
                           " ", tweet))


def sentiment(tweet):
    # create TextBlob object of passed tweet text
    analysis = TextBlob(clean_tweet(tweet))
    # set sentiment
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity == 0:
        return 'neutral'
    else:
        return 'negative'


def save_trace(trace_obj, filepath):
    """ Construct a save as from the filepath to the csv used to prepare data
    """

    basename = os.path.basename(filepath)
    filename, _ = os.path.splitext(basename)
    new_filename = filename + '.trace'
    save_to = os.path.dirname(os.path.dirname(os.path.dirname(filepath)))
    save_as = os.path.join(save_to, new_filename)

    with open(save_as, 'wb') as f:
        pickle.dump(trace_obj, f, pickle.HIGHEST_PROTOCOL)
    print("INFO: Trace successfully saved {}".format(save_as))


def load_trace(filepath):
    """ Look for a trace object from the filepath to the csv used to prepare
    data """
    data = None

    basename = os.path.basename(filepath)
    filename, _ = os.path.splitext(basename)
    new_filename = filename + '.trace'

    dir_ = os.path.dirname(os.path.dirname(os.path.dirname(filepath)))
    trace_obj = os.path.join(dir_, new_filename)

    with open(trace_obj, 'rb') as f:
        data = pickle.load(f)

    return data


def generate_random_id(length=10):
    '''Returns a unique string of specified length'''
    identifier = ""
    for _ in range(length):
        identifier = identifier + random.choice(string.ascii_letters)
    return identifier


def get_tweets_from_file(api, file_path, database_file_path, chunksize=100,
                         tablename='tweet-objects'):
    """ Given a csv file containing tweet ids,
    fetch the tweet and save to sqlite db
    """
    if chunksize > 100:
        raise ValueError('Can only allow 100 tweet ids per request.')

    total_count = 0
    # todo: revisit counter
    chunks = pd.read_csv(file_path, header=None,
                         chunksize=chunksize, squeeze=True)
    with SqliteDict(database_file_path, tablename=tablename) as tweets_table:
        for chunk in chunks:
            statuses = api.statuses_lookup(chunk.tolist())
            for count_, status in zip(count(start=1), statuses):
                tweet_id = status.id_str
                # if this doesn't wort, try its private json extension
                tweets_table[tweet_id] = status
                tweets_table.commit()
            total_count += count_

    print('++  Total number of tweets: {}\n'.format(total_count))
    return total_count


def construct_datetime_from_str(s):
    if '-' in s and '/' in s:
        raise ValueError(
            f'Incorrect date seprator. Found a mix of "-" and "/" in {s}.')
    if '-' not in s and '/' not in s:
        raise ValueError(f'Expected a date seperator ["-" or "/"] in {s}.')

    if '-' in s:
        if s.count('-') != 2:
            raise ValueError('Date seperator "-" used is more than 2')
        s = s.split('-')
    if '/' in s:
        if s.count('/') != 2:
            raise ValueError('Date seperator "/" used is more than 2')
        s = s.split('/')

    return datetime.datetime(int(s[0]), int(s[1]), int(s[2]))
