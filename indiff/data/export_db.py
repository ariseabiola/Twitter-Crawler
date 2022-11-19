# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path

import click
import progressbar
import pymongo
from dotenv import find_dotenv, load_dotenv
from pymongo.errors import DuplicateKeyError
from sqlitedict import SqliteDict


@click.command()
@click.argument('topic')
def main(topic):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)

    # root directories
    root_dir = Path(__file__).resolve().parents[2]
    datastore_root_dir = os.path.join(root_dir, 'data', 'raw')
    dataset_dir = os.path.join(datastore_root_dir, topic)

    try:
        if not os.path.exists(dataset_dir):
            raise FileNotFoundError(f'{dataset_dir} does not exist.')
        myclient = pymongo.MongoClient("localhost", 27017)
    except (ValueError, FileNotFoundError, FileExistsError, KeyError) as error:
        logger.error(error)
    else:
        network_filepath = Path(dataset_dir)
        if not network_filepath.is_absolute():
            raise ValueError('Expected an absolute path.')
        if not network_filepath.is_dir():
            raise ValueError('network_filepath path is not a directory.')

        database_filepath = list(network_filepath.glob('*.sqlite'))[0]

        mydb = myclient["info-diffusion"]
        mycol = mydb[topic]

        # get tweet ids that fulfil the date range of interest
        logger.info("Export tweets from sqlite to mongodb")
        with SqliteDict(filename=database_filepath.as_posix(),
                        tablename='tweet-objects') as tweets:
            # iterate over the tweets dataset to fetch desired result for nodes
            bar = progressbar.ProgressBar(maxval=len(tweets),
                                          prefix='Exporting Tweets: ')
            for tweet_id in bar(tweets):
                # export to mongodb
                tweet_ = tweets[tweet_id]._json
                id_ = {"_id": tweet_id}
                new_document = {**id_, **tweet_}

                try:
                    _ = mycol.insert_one(new_document)
                except DuplicateKeyError:
                    logging.info(f"found duplicate key: {tweet_id}")
                    continue


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
