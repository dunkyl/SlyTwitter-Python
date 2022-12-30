import pytest
from SlyTwitter.twitter_v2 import TwitterV2 as Twitter

@pytest.mark.skip(reason="v2")
async def test_readme_v2():

    twitter = await Twitter('test/twauth2.json', 'test/user22.json')

    me = await twitter.user()

    assert me == await twitter.user('dunkyl_')

    print(me)

    followed = await twitter.all_followed_by(me)

    follows_TechConnectify = False

    async for user in followed:
        if user.at == 'TechConnectify':
            follows_TechConnectify = True
            break

    assert follows_TechConnectify