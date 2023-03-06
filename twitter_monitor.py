import logging
import os
import re
import threading
from datetime import datetime, timedelta
from time import sleep, time

import requests
import retry

POLL_INTERVAL = 1
TWITTER_MONITOR_USERS = os.environ["TWITTER_MONITOR_USERS"]
TWITTER_API_TOKEN = os.environ["TWITTER_API_TOKEN"]
USER_AGENT = "v2TweetLookupPython"

logger = logging.getLogger(__name__)

twitter_api_tokens_lock = threading.Lock()
twitter_api_token_index = -1
twitter_api_tokens = list(map(lambda x: x.strip(), TWITTER_API_TOKEN.split(",")))


def get_api_token():
    global twitter_api_token_index
    with twitter_api_tokens_lock:
        twitter_api_token_index += 1
        if twitter_api_token_index >= len(twitter_api_tokens):
            twitter_api_token_index = 0
        return twitter_api_tokens[twitter_api_token_index]


def monitor_tweets(on_eqw_tweet):
    twitter_users = list(map(lambda x: x.strip(), TWITTER_MONITOR_USERS.split(',')))
    endpoint = f'https://api.twitter.com/2/users/by'
    params = {
        'usernames': ','.join(twitter_users),
    }
    headers = {
        "Authorization": f"Bearer {TWITTER_API_TOKEN}",
        "User-Agent": USER_AGENT
    }
    with requests.get(endpoint, params=params, headers=headers) as response:
        status = response.status_code
        result: dict = response.json()

    if status == 401:
        print(f"Error: Unauthorized. Please check your API tokens. API response: {result}")
        return

    users = result.pop('data', None)
    errors = result.pop('errors', None)
    if errors and users:
        print(f"Error: Failed to fetch user id for one or more users. API response: {errors}")
    elif not users:
        print(f"Error: Failed to fetch users ids. API response: {errors or result}")
        return

    for user in users:
        thread = threading.Thread(target=_monitor_tweets, args=(user['id'], on_eqw_tweet))
        thread.daemon = True
        thread.start()


@retry.retry(delay=1, logger=logger)
def _monitor_tweets(twitter_user_id, on_eqw_tweet):
    session = requests.Session()
    endpoint = f'https://api.twitter.com/2/users/{twitter_user_id}/tweets'
    params = {
        'tweet.fields': 'text,created_at'
    }

    begin = None
    def wait_interval():
        time_delta = time() - begin
        sleep(max(0, POLL_INTERVAL - time_delta))

    while True:
        begin = time()

        api_token = get_api_token()
        headers = {
            "Authorization": f"Bearer {api_token}",
            "User-Agent": USER_AGENT
        }
        with session.get(endpoint, params=params, headers=headers) as response:
            status = response.status_code
            result = response.json()

        if status == 429:
            logger.warning(f"Warning: Too Many Requests on token: {api_token}")
            wait_interval()
            continue

        tweets = result['data']

        now = datetime.now()
        def is_recent_tweet(tweet):
            created_at = datetime.fromisoformat(tweet['created_at'].strip('Z'))
            return now - created_at < timedelta(seconds=15)

        tweets = list(filter(is_recent_tweet, tweets))

        # for testing
        # test_tweet = get_tweet("1572832210000183296")
        # test_tweet = get_tweet("1571911780938678273")
        # test_tweet = get_tweet("1572832213510545410")
        # test_tweet = get_tweet("1571923482862043137")
        # tweets = [test_tweet]

        def is_eqw_tweet(tweet):
            text = tweet['text']
            return (
                (
                    ("CDMX: 🟡 MODERADO" in text or "CDMX: 🔴 FUERTE" in text)
                    or re.search("CDMX: (?:🟡|🔴) \d+ seg.", text)
                )
                and (
                    "#Sismo en progreso" in text or "#SASSLA" in text
                )
            )

        eqw_tweets = list(filter(is_eqw_tweet, tweets))

        if len(eqw_tweets):
            on_eqw_tweet()

        wait_interval()


# for testing
def get_tweet(tweet_id):
    endpoint = f"https://api.twitter.com/2/tweets/{tweet_id}"
    headers = {
        "Authorization": f"Bearer {TWITTER_API_TOKEN}",
        "User-Agent": "v2TweetLookupPython"
    }
    with requests.get(endpoint, headers=headers) as response:
        return response.json()['data']
