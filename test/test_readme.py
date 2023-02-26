import sys, asyncio

import aiohttp, pytest

from SlyTwitter import *
from SlyTwitter.twitter import OAuth1, OAuth1App, OAuth1User

app = OAuth1App.from_json_file('test/sly_test_app.json')
user = OAuth1User.from_json_file('test/user.json')
auth = OAuth1(app, user)

# Preconditions:
# - test was not recenty run (several hours?)
@pytest.mark.skipif(sys.gettrace() is None, reason="Fails repeats due to spam protection")
async def test_readme():

    twitter = Twitter(auth)

    tweet = await twitter.tweet('Hello, world!')
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(tweet)
    print(follow)

async def test_follow():

    twitter = Twitter(auth)
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    assert str(follow) == '@dunkyl_ follows @TechConnectify'

# Preconditions:
# - test was not recenty run (several hours?)
@pytest.mark.skipif(sys.gettrace() is None, reason="Fails repeats due to spam protection")
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

    # TODO: tweet.link() doesn't give a 404 even when it's deleted.
    # await asyncio.sleep(10)

    # async with aiohttp.ClientSession() as session:
    #     async with session.get(tweet.link()) as resp:
    #         assert(resp.status == 404)