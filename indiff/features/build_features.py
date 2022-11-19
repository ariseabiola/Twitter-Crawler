from collections import ChainMap, Counter

import numpy as np
import pandas as pd
import progressbar


class Features(object):
    def __init__(self, src_user=None, dest_user=None, keywords=None,
                 node_collection=None, tweet_collection=None, user=None):
        self.src_user = src_user
        self.dest_user = dest_user
        self.keywords = keywords
        self.node_collection = node_collection
        self.tweet_collection = tweet_collection
        self.user = user

    def activity_index(self, user_id, e=30.4*24):
        """[summary]

        Arguments:
            user_id {[type]} -- [description]

        Keyword Arguments:
            e {[type]} -- [description] (default: {30.4*24})

        Returns:
            [type] -- [description]
        """
        number_of_user_messages = len(get_user_published_tweets(
            user_id, self.node_collection))

        if number_of_user_messages < e:
            return number_of_user_messages / e
        else:
            return 1

    def dTR(self, user_id):
        """[summary]

        Arguments:
            user_id {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        # change dv..... mv is okay
        n_dv = number_of_tweets_with_user_mentions(user_id,
                                                   self.node_collection)
        n_mv = len(get_user_published_tweets(user_id, self.node_collection))

        if n_mv > 0:
            return n_dv / n_mv
        else:
            return 0

    def h(self):
        """[summary]

        Returns:
            [type] -- [description]
        """
        src_user_mv = users_ever_mentioned(self.src_user, self.node_collection)
        dest_user_mv = users_ever_mentioned(self.dest_user,
                                            self.node_collection)

        x = src_user_mv.intersection(dest_user_mv)
        y = src_user_mv.union(dest_user_mv)

        if len(y):
            return len(x) / len(y)
        else:
            return 0

    def hM(self):
        """[summary]

        Returns:
            [type] -- [description]
        """
        mvx = users_ever_mentioned(self.src_user, self.node_collection)

        if self.dest_user in mvx:
            return 1
        else:
            return 0

    def mR(self, user_id, meu=200):
        """[summary]

        Arguments:
            user_id {[type]} -- [description]

        Keyword Arguments:
            meu {int} -- [description] (default: {200})

        Returns:
            [type] -- [description]
        """
        n_tmv = len(tweets_mentioned_in(user_id, self.node_collection))

        if n_tmv < meu:
            return n_tmv / meu
        else:
            return 1

    def hK(self, user_id):
        """[summary]

        Arguments:
            user_id {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        user_tweets_keywords = get_keywords_from_user_tweets(
            user_id, self.node_collection)

        if not self.keywords.isdisjoint(user_tweets_keywords):
            return 1
        else:
            return 0

    def A(self, user_id):
        """[summary]

        Arguments:
            user_id {[type]} -- [description]

        Returns:
            [type] -- [description]
        """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        return attr['A']

    def y(self):
        """checks whether there's a diffusion from src to dest

        Arguments:
            src {[type]} -- [description]
            dest {[type]} -- [description]

        Returns:
            int -- return 1 if diffusion exists, else 0
        """
        query = {'_id': self.dest_user}
        attr = self.node_collection.find_one(query)

        if self.src_user in set(attr['all_possible_original_tweet_owners']):
            return 1
        else:
            return 0

    def ratio_of_retweets_to_tweets(self, user_id):
        """ notation 7 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        total_number_of_tweets_retweeted = attr['retweeted_count']
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # TODO: might need to check for divisible by zero
        return total_number_of_tweets_retweeted / total_number_of_tweets

    def avg_number_of_tweets_with_hastags(self, user_id):
        """ notation 8 (ii) (new) """
        n_tweets_with_hashtags = number_of_tweets_with_hashtags(
            user_id, self.node_collection)
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # TODO: might need to check for divisible by zero
        return n_tweets_with_hashtags / total_number_of_tweets

    def avg_number_of_retweets_with_hastags(self, user_id):
        """ notation 8 (i) (new) """
        n_retweets_with_hashtags = retweets_with_hashtags(user_id,
                                                          self.node_collection)
        n_retweeted_tweets = number_of_retweeted_tweets(user_id,
                                                        self.node_collection)

        # todo: might need to check for divisible by zero
        if n_retweeted_tweets:
            return n_retweets_with_hashtags / n_retweeted_tweets
        else:
            return 0

    def avg_number_of_retweets(self, user_id):
        """ number 9 (new) """
        n_retweeted_tweets = number_of_retweeted_tweets(user_id,
                                                        self.node_collection)
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # TODO: might need to check for divisible by zero
        return n_retweeted_tweets / total_number_of_tweets

    def avg_number_of_tweets(self, user_id):
        """ number 10 (new) """
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))
        n_days = get_user_number_of_tweet_days(user_id, self.node_collection)

        if total_number_of_tweets and n_days == 0:
            n_days = 1

        avg = total_number_of_tweets / n_days

        if avg > 1:
            avg = 1

        return avg

    def avg_number_of_mentions_not_including_retweets(self, user_id):
        """ number 11 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        count = attr['tweets_with_others_mentioned_count']
        + attr['quoted_tweets_with_others_mentioned_count']
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # todo: might need to check for divisible by zero
        return count / total_number_of_tweets

    def avg_number_followers(self, user_id):
        """ number 12 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        n_followers = attr['followers_count']

        avg = n_followers / 707

        # bound by 1
        if avg > 1:
            avg = 1

        return avg

    def avg_number_friends(self, user_id):
        """ number 13 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        n_friends = attr['friends_count']

        avg = n_friends / 707

        # bound by 1
        if avg > 1:
            avg = 1

        return avg

    def avg_number_of_mentions(self):
        """ number 14 (new) """
        raise NotImplementedError

    def variance_tweets_per_day(self):
        """ number 15 (new) """
        raise NotImplementedError

    def ratio_of_mentions_to_tweet(self, user_id):
        """ number 16 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        all_tweets_with_mentions_count = attr['tweets_with_others_mentioned_count']
        + attr['retweets_with_others_mentioned_count']
        + attr['quoted_tweets_with_others_mentioned_count']

        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # todo: might need to check for divisible by zero
        return all_tweets_with_mentions_count / total_number_of_tweets

    def avg_url_per_retweet(self, user_id):
        """ number 17 (i) new """
        n_retweeted_tweets_with_url = retweeted_tweets_with_urls(
            user_id, self.node_collection)
        n_retweeted_tweets = number_of_retweeted_tweets(user_id,
                                                        self.node_collection)

        # todo: might need to check for divisible by zero
        if n_retweeted_tweets:
            return n_retweeted_tweets_with_url / n_retweeted_tweets
        else:
            return 0

    def avg_url_per_tweet(self, user_id):
        """ number 17 (ii) new """
        n_tweets_with_url = number_of_tweets_with_urls(user_id,
                                                       self.node_collection)
        + retweeted_tweets_with_urls(user_id, self.node_collection)
        # get_quoted_tweets_with_url
        + quoted_tweets_with_urls(user_id, self.node_collection)

        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # todo: might need to check for divisible by zero
        return n_tweets_with_url / total_number_of_tweets

    def avg_number_of_media_in_retweets(self, user_id):
        """ number 18 (i) new """
        n_retweets_with_media = retweeted_tweets_with_media(
            user_id, self.node_collection)
        n_retweeted_tweets = number_of_retweeted_tweets(user_id,
                                                        self.node_collection)

        # todo: might need to check for divisible by zero
        if n_retweeted_tweets:
            return n_retweets_with_media / n_retweeted_tweets
        else:
            return 0

    def avg_number_of_media_in_tweets(self, user_id):
        """ number 18 (ii) new """
        n_tweets_with_media = number_of_tweets_with_media(user_id,
                                                          self.node_collection)
        # get_retweeted_tweets_with_media + len(quoted_tweets_with_media(self))
        + retweeted_tweets_with_media(user_id, self.node_collection)

        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        # todo: might need to check for divisible by zero
        return n_tweets_with_media / total_number_of_tweets

    def description(self, user_id):
        """ number 19 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        if attr['description']:
            return 1
        else:
            return 0

    def ratio_of_follower_to_friends(self, user_id):
        """ number 20 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        number_of_followers = len(attr['followers_ids'])
        number_of_friends = len(attr['friends_ids'])

        if number_of_friends == 0:
            return 0

        ratio = number_of_followers / number_of_friends

        if ratio > 1:
            ratio = 1

        return ratio

    def ratio_of_favorited_to_tweet(self, user_id):
        """ number 21 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        number_of_favorited_tweets = attr['favorite_tweets_count']
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        return number_of_favorited_tweets / total_number_of_tweets

    def avg_time_before_retweet_quote_favorite(self):
        """ number 23 (new) """
        raise NotImplementedError

    def avg_positive_sentiment_of_tweets(self, user_id):
        """ number 24 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        number_of_positive_sentiments = attr['positive_sentiment_count']
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        return number_of_positive_sentiments / total_number_of_tweets

    def avg_negative_sentiment_of_tweets(self, user_id):
        """ number 24 (new) """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)

        number_of_negative_sentiments = attr['negative_sentiment_count']
        total_number_of_tweets = len(get_user_published_tweets(
            user_id, self.node_collection))

        return number_of_negative_sentiments / total_number_of_tweets

    def ratio_of_tweet_per_time_period(self, user_id):
        """ separate tweets in 4 periods using the hour attribute

            number 25 (new)
        Arguments:
            user_id {[type]} -- [description]
            node_collection {[type]} -- [description]
        """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        return attr['ratio_of_tweet_per_time_period']

    def ratio_of_tweets_that_got_retweeted_per_time_period(self, user_id):
        """ separate tweets in 4 periods using the hour attribute

            number 26 (new)
        Arguments:
            user_id {[type]} -- [description]
            node_collection {[type]} -- [description]
        """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        return attr['ratio_of_tweets_that_got_retweeted_per_time_period']

    def ratio_of_retweet_per_time_period(self, user_id):
        """ separate tweets in 4 periods using the hour attribute

            number 27 (new)
        Arguments:
            user_id {[type]} -- [description]
            node_collection {[type]} -- [description]
        """
        query = {'_id': user_id}
        attr = self.node_collection.find_one(query)
        return attr['ratio_of_retweet_per_time_period']

    def additional_features(self, user_id, user=None):
        return {
            f'{user}_I': self.activity_index(user_id),
            f'{user}_dTR': self.dTR(user_id),
            f'{user}_mR': self.mR(user_id),
            f'{user}_hK': self.hK(user_id),
            f'{user}_A_1': self.A(user_id)[0],
            f'{user}_A_2': self.A(user_id)[1],
            f'{user}_A_3': self.A(user_id)[2],
            f'{user}_A_4': self.A(user_id)[3],
            f'{user}_A_5': self.A(user_id)[4],
            f'{user}_A_6': self.A(user_id)[5],
            f'{user}_ratio_of_retweets_to_tweets':
                self.ratio_of_retweets_to_tweets(user_id),
            f'{user}_avg_number_of_tweets_with_hastags':
                self.avg_number_of_tweets_with_hastags(user_id),
            f'{user}_avg_number_of_retweets_with_hastags':
                self.avg_number_of_retweets_with_hastags(user_id),
            f'{user}_avg_number_of_retweets':
                self.avg_number_of_retweets(user_id),
            f'{user}_avg_number_of_tweets':
                self.avg_number_of_tweets(user_id),
            f'{user}_avg_number_of_mentions_not_including_retweets':
                self.avg_number_of_mentions_not_including_retweets(user_id),
            f'{user}_ratio_of_mentions_to_tweet':
                self.ratio_of_mentions_to_tweet(user_id),
            f'{user}_avg_url_per_retweet':
                self.avg_url_per_retweet(user_id),
            f'{user}_avg_url_per_tweet':
                self.avg_url_per_tweet(user_id),
            f'{user}_avg_number_of_media_in_retweets':
                self.avg_number_of_media_in_retweets(user_id),
            f'{user}_avg_number_of_media_in_tweets':
                self.avg_number_of_media_in_tweets(user_id),
            f'{user}_description':
                self.description(user_id),
            f'{user}_ratio_of_favorited_to_tweet':
                self.ratio_of_favorited_to_tweet(user_id),
            f'{user}_avg_positive_sentiment_of_tweets':
                self.avg_positive_sentiment_of_tweets(user_id),
            f'{user}_avg_negative_sentiment_of_tweets':
                self.avg_negative_sentiment_of_tweets(user_id),
            f'{user}_ratio_of_tweet_per_time_period_1':
                self.ratio_of_tweet_per_time_period(user_id)['1']
                if '1' in self.ratio_of_tweet_per_time_period(user_id) else 0,
            f'{user}_ratio_of_tweet_per_time_period_2':
                self.ratio_of_tweet_per_time_period(user_id)['2']
                if '2' in self.ratio_of_tweet_per_time_period(user_id)
                else 0,
            f'{user}_ratio_of_tweet_per_time_period_3':
                self.ratio_of_tweet_per_time_period(user_id)['3']
                if '3' in self.ratio_of_tweet_per_time_period(user_id)
                else 0,
            f'{user}_ratio_of_tweet_per_time_period_4':
                self.ratio_of_tweet_per_time_period(user_id)['4']
                if '4' in self.ratio_of_tweet_per_time_period(user_id)
                else 0,
            f'{user}_'
            'ratio_of_tweets_that_got_retweeted_per_time_period_1':
                self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)['1']
                if '1' in self.ratio_of_tweets_that_got_retweeted_per_time_period(user_id)
                else 0,
            f'{user}_'
            'ratio_of_tweets_that_got_retweeted_per_time_period_2':
                self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)['2']
                if '2' in self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)
                else 0,
            f'{user}_'
            'ratio_of_tweets_that_got_retweeted_per_time_period_3':
                self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)['3']
                if '3' in self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)
                else 0,
            f'{user}_'
            'ratio_of_tweets_that_got_retweeted_per_time_period_4':
                self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)['4']
                if '4' in self.ratio_of_tweets_that_got_retweeted_per_time_period(
                    user_id)
                else 0,
            f'{user}_ratio_of_retweet_per_time_period_1':
                self.ratio_of_retweet_per_time_period(user_id)['1']
            if '1' in self.ratio_of_retweet_per_time_period(user_id) else 0,
            f'{user}_ratio_of_retweet_per_time_period_2':
                self.ratio_of_retweet_per_time_period(user_id)['2']
                if '2' in self.ratio_of_retweet_per_time_period(user_id)
                else 0,
            f'{user}_ratio_of_retweet_per_time_period_3':
                self.ratio_of_retweet_per_time_period(user_id)['3']
                if '3' in self.ratio_of_retweet_per_time_period(user_id)
                else 0,
            f'{user}_ratio_of_retweet_per_time_period_4':
                self.ratio_of_retweet_per_time_period(user_id)['4']
                if '4' in self.ratio_of_retweet_per_time_period(user_id)
                else 0,
            f'{user}_avg_number_followers': self.avg_number_followers(user_id),
            f'{user}_avg_number_friends': self.avg_number_friends(user_id),
            f'{user}_ratio_of_follower_to_friends':
                self.ratio_of_follower_to_friends(user_id),
            }

    def to_dict(self):
        default_features = {
            'H': self.h(),
            'hM': self.hM(),
            'y': self.y(),
        }

        src_additional_features = self.additional_features(
            user_id=self.src_user, user='src')

        dest_additional_features = self.additional_features(
            user_id=self.dest_user, user='dest')

        return ChainMap(default_features, src_additional_features,
                        dest_additional_features)


def get_user_published_tweets(user_id, node_collection):
    """notation 6"""
    # all_tweets = {}

    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    # list of tweet ids
    tweets = attr['tweets']
    # all_tweets.update(tweets)

    retweeted_tweets = attr['retweeted_tweets']
    # all_tweets.update(retweeted_tweets)

    quoted_tweets = attr['quoted_tweets']
    # all_tweets.update(quoted_tweets)

    return tweets + retweeted_tweets + quoted_tweets


def users_ever_mentioned(user_id, node_collection):  # get_users_mentioned_in
    """notation 7"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return set(attr['users_mentioned_in_all_my_tweets'])


def number_of_tweets_with_user_mentions(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_tweets_with_user_mentions']


def tweets_mentioned_in(user_id, node_collection):
    """notation 9"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return set(attr['mentioned_in'])


def get_keywords_from_user_tweets(user_id, node_collection):
    """notation 12"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return set(attr['keywords_in_all_my_tweets'])


def calculate_network_diffusion(edges, keywords, node_collection,
                                tweet_collection, *, additional_attr=False,
                                do_not_add_sentiment=False, n_days=30):
    # todo: turn this into a generator and see if its contents will only be
    # consumed once. this will require removing counter and search for another
    # way of knowing the number of things calculated
    # changed results.append to yield

    widgets = ['Computing Diffusion, ',
               progressbar.Counter('Processed %(value)02d'),
               ' edges (', progressbar.Timer(), ')']
    bar = progressbar.ProgressBar(widgets=widgets)
    for src_user, dest_user in bar(edges):
        features = Features(src_user=src_user, dest_user=dest_user,
                            keywords=keywords, node_collection=node_collection)

        yield(features.to_dict())


def number_of_retweeted_tweets(user_id, node_collection):
    """---"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return len(attr['retweeted_tweets'])


def retweet_count(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['retweet_count']


def number_of_tweets_with_hashtags(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_tweets_with_hashtags']


def retweets_with_hashtags(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_retweeted_tweets_with_hashtags']


def get_user_number_of_tweet_days(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    tweet_max_date = attr['tweet_max_date']
    tweet_min_date = attr['tweet_min_date']
    diff = tweet_max_date - tweet_min_date

    return diff.days


def number_of_tweets_with_urls(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_tweets_with_urls']


def retweeted_tweets_with_urls(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_retweeted_tweets_with_urls']


def quoted_tweets_with_urls(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_quoted_tweets_with_urls']


def number_of_tweets_with_media(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_tweets_with_media']

# get_retweeted_tweets_with_media


def retweeted_tweets_with_media(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_retweeted_tweets_with_media']


def quoted_tweets_with_media(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['n_quoted_tweets_with_media']


def compute_ratio_of_tweet_per_time_period(user):
    periods = Counter()

    all_tweets_dates = user['tweets_dates'] + \
        user['retweeted_tweets_dates'] + user['quoted_tweets_dates']

    n_all_tweets_dates = len(all_tweets_dates)

    for tweet_date in all_tweets_dates:
        h = tweet_date.hour

        if h in range(0, 24):
            period = h // 6 + 1
            periods[str(period)] += 1

    for key, value in periods.items():
        periods[key] = value / n_all_tweets_dates

    user['ratio_of_tweet_per_time_period'] = periods


def compute_ratio_of_tweets_that_got_retweeted_per_time_period(user):
    periods = Counter()

    all_tweets_dates = user['tweets_dates'] + \
        user['retweeted_tweets_dates'] + user['quoted_tweets_dates']

    n_all_tweets_dates = len(all_tweets_dates)

    retweeted_tweets_dates = user['retweeted_tweets_dates']

    for tweet_date in retweeted_tweets_dates:
        h = tweet_date.hour

        if h in range(0, 24):
            period = h // 6 + 1
            periods[str(period)] += 1

    for key, value in periods.items():
        periods[key] = value / n_all_tweets_dates

    user['ratio_of_tweets_that_got_retweeted_per_time_period'] = periods


def compute_ratio_of_retweet_per_time_period(user):
    periods = Counter()
    retweeted_tweets_dates = user['retweeted_tweets_dates']
    n_retweeted_tweets_dates = len(retweeted_tweets_dates)

    for tweet_date in retweeted_tweets_dates:
        h = tweet_date.hour

        if h in range(0, 24):
            period = h // 6 + 1
            periods[str(period)] += 1

    for key, value in periods.items():
        if n_retweeted_tweets_dates:
            periods[key] = value / n_retweeted_tweets_dates
        else:
            periods[key] = 0

    user['ratio_of_retweet_per_time_period'] = periods


def compute_A(user):
    tweet_freq_table = {}
    all_tweets_dates = user['tweets_dates'] + \
        user['retweeted_tweets_dates'] + user['quoted_tweets_dates']

    n_all_tweets_dates = len(all_tweets_dates)

    for tweet_date in all_tweets_dates:
        tweet_date_and_time = tweet_date
        tweet_date = tweet_date_and_time.date()
        tweet_hour = tweet_date_and_time.hour
        hour_bin = tweet_hour // 4

        tweet_freq_table.setdefault(tweet_date, {0: 0,
                                                 1: 0,
                                                 2: 0,
                                                 3: 0,
                                                 4: 0,
                                                 5: 0})[hour_bin] += 1

    results = pd.DataFrame(list(tweet_freq_table.values()))
    results = results / n_all_tweets_dates
    results = results.values
    sum_ = np.sum(results, axis=0)

    user['A'] = sum_.tolist()
