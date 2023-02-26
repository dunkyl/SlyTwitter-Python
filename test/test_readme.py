import pytest
import asyncio

import aiohttp
from SlyTwitter import *
from SlyTwitter.twitter import OAuth1, OAuth1App, OAuth1User

app = OAuth1App.from_json_file('test/sly_test_app.json')
user = OAuth1User.from_json_file('test/user.json')
auth = OAuth1(app, user)

async def test_readme():

    twitter = Twitter(auth)

    # tweet = await twitter.tweet('Hello, world!')
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(follow)
    assert str(follow) == '@dunkyl_ follows @TechConnectify'

@pytest.mark.skip(reason="effectual")
async def test_upload_tweet_delete():

    twitter = Twitter(auth)

    # post a tweet with an image

    media = await twitter.upload_media('test/test.jpg')
    await twitter.add_alt_text(media, 'A test image.')
    tweet = await twitter.tweet('Hello, world!', [media])

    print(tweet)

    await asyncio.sleep(10)

    # delete it and make sure its gone

    await twitter.delete(tweet)

    await asyncio.sleep(10)

    async with aiohttp.ClientSession() as session:
        async with session.get(tweet.link()) as resp:
            assert(resp.status == 404)