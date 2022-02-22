import json
from SlyTwitter import *
from SlyAPI import OAuth1App, OAuth1User


async def test_tweet():

    app = json.load(open('test/app.json'))

    user = json.load(open('test/user.json'))

    twitter = await Twitter(app, user)

    tweet = await twitter.tweet('Hello, world!')

    print(tweet)