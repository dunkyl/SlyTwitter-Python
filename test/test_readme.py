import json
from SlyTwitter import *


async def test_readme():

    app = json.load(open('test/app.json'))

    user = json.load(open('test/user.json'))

    twitter = await Twitter(app, user)

    # tweet = await twitter.tweet('Hello, world!')
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(follow)