import os
from datetime import datetime, timedelta
from time import sleep, time
import re

import requests
import retry


POLL_INTERVAL = 1
POLL_USER_ID = '921836240563032066' # the user id for @SafeLiveAlerter
TWITTER_API_TOKEN = os.environ.get("TWITTER_API_TOKEN")


@retry.retry()
def monitor_tweets(on_eqw_tweet):
    session = requests.Session()
    endpoint = f'https://api.twitter.com/2/users/{POLL_USER_ID}/tweets'
    params = {
        'tweet.fields': 'text,created_at'
    }
    headers = {
        "Authorization": f"Bearer {TWITTER_API_TOKEN}",
        "User-Agent": "v2TweetLookupPython"
    }

    while True:
        begin = time()

        with session.get(endpoint, params=params, headers=headers) as r:
            response = r.json()

        tweets = response['data']

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

        time_delta = time() - begin
        sleep(max(0, POLL_INTERVAL - time_delta))


# for testing
def get_tweet(tweet_id):
    endpoint = f"https://api.twitter.com/2/tweets/{tweet_id}"
    headers = {
        "Authorization": f"Bearer {TWITTER_API_TOKEN}",
        "User-Agent": "v2TweetLookupPython"
    }
    with requests.get(endpoint, headers=headers) as response:
        return response.json()['data']
