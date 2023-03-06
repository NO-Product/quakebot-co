from functools import partial
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Thread

import requests
from flask import Flask, abort, request

from twitter_monitor import monitor_tweets


def parse_bool(string: str):
    return string.lower() in ['true', '1', 'yes']


TEST_MODE = parse_bool(os.environ.get('TEST_MODE', 'False'))
VERIFICATION_TOKEN = os.environ.get('VERIFICATION_TOKEN')
ALERT_WEBHOOKS = os.environ.get('ALERT_WEBHOOKS', '')

ALERT_WEBHOOKS = [webhoook.strip() for webhoook in ALERT_WEBHOOKS.split(",")]


def create_app():
    app = Flask(__name__)
    threadPool = ThreadPoolExecutor(4)

    @app.route("/notify/sassla", methods=['POST'])
    def notify():
        authorization = request.headers.get('Authorization')
        if authorization != f'key={VERIFICATION_TOKEN}':
            abort(401)
        body: dict = request.get_json(silent=True)
        if body is None:
            return "bad body format.", 400

        try:
            code = body['message']['code']
        except (KeyError, TypeError):
            app.logger.error(f"received a message with an invalid body format. request body: {request.get_data(as_text=True)}")
            return "invalid body format.", 400

        if code == "RWT":
            if TEST_MODE:
                on_eqw_signal(test=True)
            return "OK", 200
        elif code == "EQW":
            on_eqw_signal()
            return "OK", 200
        else:
            return "invalid signal code.", 400

    last_eqw_singal_date = None

    def on_eqw_signal(test=False, twitter=False):
        nonlocal last_eqw_singal_date
        print(f"Recived EQW signal! from twitter: {twitter} - is test: {test}")
        # ignore subsequent EQW signals for 15 seconds
        # to avoid sending multiple webhooks for a single signal
        now = datetime.now()
        if last_eqw_singal_date and now - last_eqw_singal_date < timedelta(seconds=15):
            print(f"Signal ignored: within 15 seconds of previous signal.")
            return
        last_eqw_singal_date = now

        payload = {
            "code": "EQW",
            "date": datetime.now().isoformat()
        }
        if test:
            payload['test'] = True
        if twitter:
            payload['twitter'] = True

        def send_webhook(webhook):
            with requests.post(webhook, json=payload) as response:
                print(f"Notification sent to '{webhook}' with status code: {response.status_code}")

        results = threadPool.map(send_webhook, ALERT_WEBHOOKS)


    twitter_monitor_thread = Thread(
        target=monitor_tweets,
        kwargs={'on_eqw_tweet': partial(on_eqw_signal, twitter=True)},
        daemon=True
    )
    twitter_monitor_thread.start()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run("0.0.0.0", 5000)
