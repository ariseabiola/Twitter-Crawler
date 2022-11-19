# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
from pathlib import Path

import click
import networkx as nx
import pymongo
import requests
from dotenv import find_dotenv, load_dotenv

from indiff.twitter import auth, get_user_tweets_in_network


@click.command()
@click.argument('network_filepath', type=click.Path(exists=True))
def main(network_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    current_date_and_time = datetime.now()

    topic, _ = os.path.splitext(os.path.basename(network_filepath))

    # root directories
    root_dir = Path(__file__).resolve().parents[2]
    data_root_dir = os.path.join(root_dir, 'data')
    raw_data_root_dir = os.path.join(data_root_dir, 'raw')
    topic_raw_data_dir = os.path.join(raw_data_root_dir, topic)

    url = "http://example.com/"
    timeout = 5

    db_name = "info-diffusion"
    client = None

    try:
        # test internet conncetivity is active
        req = requests.get(url, timeout=timeout)
        req.raise_for_status()

        # prepare credentials for accessing twitter API
        consumer_key = os.environ.get('CONSUMER_KEY')
        consumer_secret = os.environ.get('CONSUMER_SECRET')
        access_token = os.environ.get('ACCESS_TOKEN')
        access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')

        api = auth(consumer_key=consumer_key,
                   consumer_secret=consumer_secret,
                   access_token=access_token,
                   access_token_secret=access_token_secret)

        client = pymongo.MongoClient(host='localhost', port=27017,
                                     appname=__file__)
        db = client[db_name]
        col = db[topic]

        # build initial graph from file
        social_network = nx.read_edgelist(network_filepath, delimiter=',',
                                          create_using=nx.DiGraph())
    except (ValueError, FileNotFoundError, FileExistsError, KeyError) as error:
        logger.error(error)
    except requests.HTTPError as e:
        logger.error("Checking internet connection failed, "
                     f"status code {e.response.status_code}")
    except requests.ConnectionError:
        logger.error("No internet connection available.")
    else:
        if not os.path.exists(topic_raw_data_dir):
            os.makedirs(topic_raw_data_dir)

        user_ids = social_network.nodes

        logger.info('downloading data set from raw data')
        error_ids = get_user_tweets_in_network(api=api, users=user_ids,
                                               collection=col, n_tweets=100000)

        logger.info('removing ids with error from graph')
        social_network.remove_nodes_from(error_ids)

        social_network.name = topic

        topic_raw_data_dir = Path(topic_raw_data_dir)

        # reports file path
        parts = list(topic_raw_data_dir.parts)
        if parts[-2] != 'raw':
            raise ValueError(f'Not an expected file path. Expected value: raw')
        _ = parts.pop(-2)
        parts[-2] = 'reports'
        topic_reports_dir = Path(*parts)

        graph_filename = os.path.join(topic_raw_data_dir, f'{topic}.adjlist')
        logger.info(f'writing graph to {graph_filename}')
        nx.write_adjlist(social_network, graph_filename, delimiter=',')

        tweet_count = col.count_documents({})
        graph_info_filename = os.path.join(topic_reports_dir,
                                           f'{topic}-crawl-stats.txt')
        logger.info(f'writing crawl reports to {graph_info_filename}')

        if not os.path.exists(topic_reports_dir):
            os.makedirs(topic_reports_dir)

        mode = 'a'
        if not os.path.exists(graph_info_filename):
            mode = 'w'

        with open(graph_info_filename, mode) as f:
            f.write(f'###* Info for {topic}, started at '
                    f'{current_date_and_time}.\n#\n#\n')
            f.write(nx.info(social_network))
            f.write(f'\nNumber of tweets: {tweet_count}')
    finally:
        if client is not None:
            logger.info('ending all server sessions')
            client.close()


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
