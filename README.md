# QuakeBot | Distribute earthquake alerts to IFTTT, Zapier and others.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/NO-Product/alert-quakebot-co.git)

<a name="introduction"/>

## Introduction
QuakeBot instantly notify automation tools such as IFTTT and Zapier when an earthquake notification is received, making it easy to integrate local earthquake alerts with your smart home and other devices. You can easily configure the app to process inbound alerts from official earthquake monitoring services such as SASSLA, or to monitor specific Twitter accounts for public alerts. 

Each deployment of QuakeBot can be configured to process earthquake alerts for a specified location or region and once an alert has been received, to then notify one or more webhook URLs connected to individuals, companies or services within that alert area. 


## Table of Contents  
- [Introduction](#introduction)  
- [Deploy to Heroku](#deploy-to-heroku)
- [Integrations : Earthquake Warning Systems](#integrations)
  - [SASSLA](#integrations-sassla)
  - [Twitter API](#integrations-twitter)
- [Additional Information](#additional-information)
  - [Real-world Deployment](#additional-information-example-use-case) 


------------------------------------------------------------------------------------------


<a name="deploy-to-heroku"/>

## Deploy to Heroku
It's easy to deploy your own instance of QuakeBot to Heroku in just a few clicks. First click 'Deploy to Heroku' and choose a name for your Heroku app. Then configure your QuakeBot instance by setting the environment variables (also known as CONFIG VAR in Heroku).

⚠️ **Important:** Ensure your Heroku dyno is 'always on' by upgrading it to use Hobby tier, else it will be slow to respond to alerts.

### Environment variables: 
```ini
TWITTER_API_TOKEN=[YOUR_API_TOKEN]
VERIFICATION_TOKEN=[SASMEX_VERIFICATION_TOKEN] # The token used to authorize SASMEX notifications
IFTTT_WEBHOOKS=[WEBOOK_URLS] # A list of URLs separated by commas ','

ALERT_WEBHOOKS=[LIST_OF_WEBHOOK_URLS] # Set 1 or more (comma separated) webhook URLs that should be notified when an earthquake alert is received
VERIFICATION_TOKEN=[INBOUND_NOTIFICATION_TOKEN] # To secure requests made to `/notify/*` each request must contain the token you set here
TWITTER_API_TOKEN=[TWITTER_API_TOKENS] # Set 1 or more (comma separated) Twitter API keys. If multiple are provided, they will be continually rotated to increase your rate limit
TWITTER_MONITOR_USERS=[LIST_OF_TWITTER_USERS] # Set 1 or more Twitter usernames (comma separated) who's Tweets should be monitored for new alerts
TWITTER_TEXT_QUERY=[AND_NOT_OR_MATCH_STRING] # Criteria used to determine if any Tweet received should trigger a new QuakeBot alert
TWITTER_TOKEN_RATE_LIMIT=[HOURLY_REQUEST_LIMIT] # Total number of requests that should be made hourly (per token) to Twitter API. (Default value = 684)
```

### Webhook payload:
Here's an example of the payload sent with each webhook notification QuakeBot sends, when a new earthquake alert has been received. This is what would therefore be received by any webhook URL defined in the `ALERT_WEBHOOKS` environment variable.

**Method:** `POST`

**Payload:**
```js
{
    "code": "EQW", // Set using the value provided by SASSLA notification where `RWT` is a test signal and `EQW` is a real alert
    "date": "2023-03-04T16:46:56.548980",
    "twitter": true // Present only if the earthqauke notification source is twitter
}
```


------------------------------------------------------------------------------------------


<a name="integrations"/>

## Integrations : Earthquake Warning Systems


<a name="integrations-sassla"/>

### SASSLA | Region: Mexico
For anyone living in Mexico it's easy to configure QuakeBot to receive inbound webhook alerts from [SASSLA](https://www.sassla.mx/), which can then be instantly processed and redistributed to your list of webhook URLs. Once you've deployed your instance of QuakeBot, contact the SASSLA Developer team via email (app@sassla.mx) and ask them to add your app's URL to their earthquake notification list.

#### Email template (translate to Spanish before sending):
```
Hello SASSLA team,

I have just deployed my own instance of QuakeBot and I would like to start receiving your earthquake alerts. Here's the information you require:

Location: [CITY]
Verification token: [VERIFICATION_TOKEN]
Notification URL: APP_URL/notify/sassla/

Thank you,
```




<a name="integrations-twitter"/>

### Twitter API | Region: Global
Understanding that each country around the world will have a varying level of technical maturity in providing localised, citizen-level alerts, we have added Twitter as one of the earthquake alert sources. This enables you to configure each deployment of QuakeBot to monitor 1 or more Twitter accounts for new Tweets and to then determine whether any of the Tweets match a specific text pattern. 

In the two examples below, you can see the @SafeLiveAlerter account operated by [SASSLA](https://www.sassla.mx/) instantly posts a Tweet each time an earthquake has been detected for any part of Mexico. QuakeBot was then configured to monitor this Twitter account and to instantly notify it's list of webhook alert URLs whenever a Tweet from this account matched a specific text pattern.

#### Sample Twitter match:
```
(("CDMX: 🟡 MODERADO" OR "CDMX: 🔴 FUERTE") OR "CDMX: (?:🟡|🔴) \d+ seg.")) AND ( "#Sismo en progreso" OR "#SASSLA"))
```

#### Sample Tweets:
|Tweet 1|Tweet 2|
|:-:|:-:|
|![First Image](https://user-images.githubusercontent.com/16068761/222926394-71ba3106-00de-4a36-82ad-5397a638f718.png)|![Second Image](https://user-images.githubusercontent.com/16068761/222926418-19b659e0-f8ca-49f6-a2df-bee3dd9793d9.png)|



------------------------------------------------------------------------------------------


<a name="additional-information"/>

## Additional Information

<a name="additional-information-example-use-case"/>

### Example Use Case
QuakeBot was first developed to act as an extension of Mexico City's earthquake early warning system. As a resident of Mexico City, the user missed the public alert system on two occasions where a medium / strong earthquake had been detected. On the first occassion the public sirens were activated in the middle of the day but the user did not hear them as they had headphones in. On the second occassion, the public sirens were activated at 3am so the user did not hear them because the building's sound insulation significantly reduced the volume of the sirens so much that it didn't wake them up.

On both occassions, the user would have benefitted from an alert mechanism that intentionally interrupted their current activity, causing them to understand 'something' was happening, which would have then made other alerting systems (public sirens, alert apps etc) effective. 

QuakeBot was then developed to achieve this. In its initial deployment the app was configured to receive webhook alerts from SASMEX for the Mexico City region, in addition to monitoring the SASMEX Twitter account for Tweets that matched a specific pattern used by their system for localised alerts. Once a notification was received by QuakeBot, it would then instantly notify multiple IFTTT webhooks which triggered personalised alert mechanisms. User alerts included immediately pausing their Spotify music to ensure they can hear external noises, creating a visual alert by triggering an entire Philips Hue lighting system to flash and also automatically calling themselves from a phone number that was favourited on the user's device to bypass any 'Do Not Disturb' mode.
