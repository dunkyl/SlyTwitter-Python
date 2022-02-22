import re
from typing import Any
from SlyAPI import *
from SlyAPI.oauth1 import OAuth1App, OAuth1User, OAuth1

RE_TWEET_LINK = re.compile(r'https://twitter\.com/([a-z0-9_]+)/status/(\d+)', re.IGNORECASE)

class Media(APIObj['Twitter']):
    id: int

    def __init__(self, source: int | dict[str, Any], service: 'Twitter'):
        super().__init__(service)
        match source:
            case int():
                self.id = source
            case {'media_id': id_}:
                self.id = id_
            case _:
                raise TypeError(F"{source} is not a valid source for Media")

    # async def addAltText(self, text: str):
    #     await self._service.addAltText(self, text)

class Tweet(APIObj['Twitter']):
    id: int
    author_username: str # twitter user @
    body: str

    def __init__(self, source: int | str | dict[str, Any], service: 'Twitter'):
        super().__init__(service)
        match source:
            case int():
                self.id = source
            case str():
                if not (match := RE_TWEET_LINK.match(source)):
                    raise ValueError('Cannot create Tweet without ID, link to tweet, or dict representation')
                self.author_username = match.group(1)
                self.id = int(match.group(2))
            case { 'id': id_, 'extended_tweet': { 'full_text': text } }:
                self.id = id_
                self.body = text
            case { 'id': id_, 'text': text }:
                self.id = id_
                self.body = text
            case _:
                raise TypeError(F"{source} is not a valid source for Tweet")

    def link(self) -> str:
        return F"https://twitter.com/{self.author_username}/status/{self.id}"

    # async def delete(self):
    #     await self._service.delete(self)

class Twitter(WebAPI):

    base_url = 'https://api.twitter.com/1.1'
    media_url = 'https://upload.twitter.com/1.1'
    
    def __init__(self, app: OAuth1App, user: OAuth1User):
        auth = OAuth1(app, user)
        super().__init__(auth)

    async def tweet(self, body: str, media: list[Media] | None = None) -> Tweet:
        """ Post a tweet. """
        data = { 'status': body }
        if media:
            data |= { 'media_ids': [m.id for m in media] }
        return Tweet( await self.req_form_oauth1(
                'POST', '/statuses/update.json',
                data
            ), self )