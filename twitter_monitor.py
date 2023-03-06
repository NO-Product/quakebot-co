import json
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
TWITTER_TOKEN_RATE_LIMIT = int(os.environ["TWITTER_TOKEN_RATE_LIMIT"])
TWITTER_TEXT_QUERY = json.loads(os.environ.get('TWITTER_TEXT_QUERY', r"""
{
    "AND": [
        {
            "OR": [
                "CDMX: 🟡 MODERADO",
                "CDMX: 🔴 FUERTE",
                {"REGEX": "CDMX: (🟡|🔴) \\d+ seg."}
            ]
        },
        {
            "OR": [
                "#Sismo en progreso",
                "#SASSLA"
            ]
        }
    ]
}
"""))
USER_AGENT = "v2TweetLookupPython"

logger = logging.getLogger(__name__)

twitter_api_tokens_lock = threading.Lock()
twitter_api_token_index = -1
twitter_api_tokens = list(map(lambda x: x.strip(), TWITTER_API_TOKEN.split(",")))
twitter_api_calls_since = None
twitter_api_calls = None


def query_tweet_text_for_alert(tweet_text, query: dict):
    key, value = next(iter(query.items()))
    if key.upper() == "OR":
        for item in value:
            if isinstance(item, dict):
                if query_tweet_text_for_alert(tweet_text=tweet_text, query=item):
                    return True
            else:
                if item in tweet_text:
                    return True
        return False
    elif key.upper() == "AND":
        for item in value:
            if isinstance(item, dict):
                if not query_tweet_text_for_alert(tweet_text=tweet_text, query=item):
                    return False
            else:
                if item not in tweet_text:
                    return False
        return True
    elif key.upper() == "REGEX":
        return re.search(value, tweet_text)


def get_api_token():
    global twitter_api_token_index
    global twitter_api_calls_since
    global twitter_api_calls

    with twitter_api_tokens_lock:
        if twitter_api_calls_since is None or time() - twitter_api_calls_since > 3600:
            twitter_api_calls_since = time()
            twitter_api_calls = 0
        if twitter_api_calls + 1 > TWITTER_TOKEN_RATE_LIMIT:
            wait_time = max(0, 3600 - (time() - twitter_api_calls_since))
            logger.warning(f"Warning: Hit rate limit of {TWITTER_TOKEN_RATE_LIMIT} requests/hr. waiting: {round(wait_time)} seconds")
            sleep(wait_time)
            twitter_api_calls_since = time()
            twitter_api_calls = 0
        twitter_api_calls += 1

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
            return query_tweet_text_for_alert(tweet['text'], TWITTER_TEXT_QUERY)

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
