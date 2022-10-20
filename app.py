import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import requests
from flask import Flask, abort, request


def parse_bool(string: str):
    return string.lower() in ['true', '1', 'yes']


TEST_MODE = parse_bool(os.environ.get('TEST_MODE', 'False'))
PASSWORD = os.environ.get('PASSWORD')
IFTTT_WEBHOOKS = os.environ.get('IFTTT_WEBHOOKS', '')

IFTTT_WEBHOOKS = [webhoook.strip() for webhoook in IFTTT_WEBHOOKS.split(",")]


def create_app():
    app = Flask(__name__)
    threadPool = ThreadPoolExecutor(4)
    last_eqw_singal_date = None

    @app.route("/notify", methods=['POST'])
    @app.route("/notify/", methods=['POST'])
    def notify():
        authorization = request.headers.get('Authorization')
        if authorization != f'key={PASSWORD}':
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


    def on_eqw_signal(test=False):
        nonlocal last_eqw_singal_date
        # ignore subsequent EQW signals for 15 seconds
        # to avoid sending multiple webhooks for a single signal
        now = datetime.now()
        if last_eqw_singal_date and last_eqw_singal_date - now < timedelta(seconds=15):
            return
        last_eqw_singal_date = now
        
        payload = {
            "code": "EQW",
            "date": datetime.now().isoformat()
        }
        if test:
            payload['test'] = True

        def send_webhook(webhook):
            with requests.post(webhook, json=payload) as response:
                return response.status_code

        results = threadPool.map(send_webhook, IFTTT_WEBHOOKS)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run("0.0.0.0", 5000)
