import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


if __name__ == '__main__':
    client = MongoClient()
    try:
        client.admin.command('ismaster')
    except ConnectionFailure:
        print(">>> Server not available. Please install or start MongoDB.")
        sys.exit(1)
    else:
        print(">>> Passed server availability test!")
