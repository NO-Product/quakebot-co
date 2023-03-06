# NO-Product-alert-quakebot-co

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/NO-Product/alert-quakebot-co.git)

## Required environment variables:
```ini
TWITTER_API_TOKEN=[YOUR_API_TOKEN]
VERIFICATION_TOKEN=[SASMEX_VERIFICATION_TOKEN] # The token used to authorize SASMEX notifications
IFTTT_WEBHOOKS=[WEBOOK_URLS] # A list of URLs separated by commas ','
```

## Notification format:

Method: `POST`

Payload:
```js
{
    "code": "EQW",
    "date": "2023-03-04T16:46:56.548980",
    "twitter": true // present only if the notification source is twitter
}
```
