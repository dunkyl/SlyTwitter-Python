import asyncio
import json

import aiohttp
from SlyTwitter import *


async def test_readme():

    app = json.load(open('test/app.json'))

    user = json.load(open('test/user.json'))

    twitter = await Twitter(app, user)

    # tweet = await twitter.tweet('Hello, world!')
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(follow)

async def test_upload_tweet_delete():

    app = json.load(open('test/app.json'))

    user = json.load(open('test/user2.json'))

    twitter = await Twitter(app, user)

    # post a tweet with an image

    media = await twitter.upload_media('test/test.jpg')
    await media.add_alt_text('A test image.')
    tweet = await twitter.tweet('Hello, world!', [media])

    print(tweet)

    await asyncio.sleep(1)

    # delete it and make sure its gone

    await tweet.delete()

    await asyncio.sleep(1)

    async with aiohttp.ClientSession() as session:
        async with session.get(tweet.link()) as resp:
            assert(resp.status == 404)