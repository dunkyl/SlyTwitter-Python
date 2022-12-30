import pytest
import asyncio

import aiohttp
from SlyTwitter import *

async def test_readme():

    twitter = await Twitter('test/user.json')

    # tweet = await twitter.tweet('Hello, world!')
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(follow)
    assert str(follow) == '@dunkyl_ follows @TechConnectify'

@pytest.mark.skip(reason="effectual")
async def test_upload_tweet_delete():

    twitter = await Twitter('test/user.json')

    # post a tweet with an image

    media = await twitter.upload_media('test/test.jpg')
    await media.add_alt_text('A test image.')
    tweet = await twitter.tweet('Hello, world!', [media])

    print(tweet)

    await asyncio.sleep(10)

    # delete it and make sure its gone

    await tweet.delete()

    await asyncio.sleep(10)

    async with aiohttp.ClientSession() as session:
        async with session.get(tweet.link()) as resp:
            assert(resp.status == 404)