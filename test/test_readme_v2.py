import pytest

from SlyTwitter.twitter_v2 import TwitterV2 as Twitter
from SlyTwitter.twitter_v2 import OAuth2, OAuth2App, OAuth2User

@pytest.mark.skip(reason="Twitter API changes")
async def test_readme_v2():

    app = OAuth2App.from_json_file('test/twauth2.json')
    user = OAuth2User.from_json_file('test/user22.json')
    auth = OAuth2(app, user)

    twitter = Twitter(auth)

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