import re
from datetime import datetime
from typing import Any
from SlyAPI import *

from .twitter_upload import Media, TwitterUpload
from .common import make_with_self

RE_TWEET_LINK = re.compile(r'https://twitter\.com/(?P<user>[a-z0-9_]+)/status/(?P<tweet_id>\d+)', re.IGNORECASE)
RE_USER_LINK = re.compile(r'https://twitter\.com/(?P<user>[a-z0-9_]+)', re.IGNORECASE)


class User(APIObj['Twitter']):
    id: int
    at: str
    display_name: str

    # hydratable fields
    description: str|None = None
    location: str|None = None
    website: str|None = None
    is_verified: bool|None = None
    is_private: bool|None = None
    created_at: datetime|None = None
    profile_image: str|None = None

    def __init__(self, source: dict[str, Any], service: 'Twitter'):
        super().__init__(service)
        match source:
            case int():
                self.id = source
            case str() if m := RE_USER_LINK.match(source):
                self.at = m[1]
            case str(): # from screen name
                if source.startswith('@'):
                    self.at = source[1:]
                else:
                    self.at = source
            case { # from user response
                'id': int(id),
                'screen_name': str(at),
                'name': str(display_name),
                'location': str(location),
                'url': str(website),
                **extended
            }:
                self.id = id
                self.at = at
                self.display_name = display_name
                self.location = location
                self.website = website
                if extended:
                    self.description = extended['description']
                    self.is_verified = extended['verified']
                    self.is_private = extended['protected']
                    self.created_at = datetime.strptime(
                        extended['created_at'], '%a %b %d %H:%M:%S %z %Y')
                    self.profile_image = extended['profile_image_url_https']
            case { # from following response
                'followed_by': _,
                'id': int(id),
                'screen_name': str(at),
            }:
                self.id = id
                self.at = at
            case _:
                raise TypeError(f'Invalid source type for tweet: {type(source)}')

    def __str__(self):
        return F'@{self.at}'

class Following(APIObj['Twitter']):
    a: User
    b: User
    is_mutual: bool
    a_follows_b: bool
    b_follows_a: bool

    def __init__(self, source: dict[str, Any], service: 'Twitter'):
        super().__init__(service)
        self.a_follows_b = source['relationship']['source']['following']
        self.b_follows_a = source['relationship']['target']['following']
        self.mutual = self.a_follows_b and self.b_follows_a
        self.a = User(source['relationship']['source'], service)
        self.b = User(source['relationship']['target'], service)

    def __str__(self) -> str:
        if self.mutual:
            rel_str = 'mutually follows'
        elif self.a_follows_b:
            rel_str = 'follows'
        elif self.b_follows_a:
            rel_str = 'is followed by'
        else:
            rel_str = 'is not following or being followed by'
        return F"{self.a} {rel_str} {self.b}"


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
                if not (m := RE_TWEET_LINK.match(source)):
                    raise ValueError('Cannot create Tweet without ID, link to tweet, or dict representation')
                self.author_username = m['user']
                self.id = int(m['tweet_id'])
            case { 'id': id_, 'extended_tweet': { 'full_text': text }, 'user': { 'screen_name': user } }:
                self.id = id_
                self.body = text
                self.author_username = user
            case { 'id': id_, 'text': text, 'user': { 'screen_name': user } }:
                self.id = id_
                self.body = text
                self.author_username = user
            case _:
                raise TypeError(F"{source} is not a valid source for Tweet")

    def link(self) -> str:
        return F"https://twitter.com/{self.author_username}/status/{self.id}"

    async def delete(self):
        await self._service.delete(self)
    
def get_tweet_id(tweet: Tweet | int | str) -> int:
    match tweet:
        case Tweet():
            return tweet.id
        case int():
            return tweet
        case str() if m := RE_TWEET_LINK.match(tweet):
            return int(m['tweet_id'])
        case _:
            raise TypeError(F"{tweet} is not a valid tweet, ID, or URL")


class Twitter(WebAPI):
    base_url = 'https://api.twitter.com/1.1'
    _upload_api: TwitterUpload
    
    async def __init__(self, auth: str | OAuth1User):
        if isinstance(auth, str):
            auth = OAuth1User(auth)

        await super().__init__(auth)
        self._upload_api = await TwitterUpload(auth)

    def get_full_url(self, path: str) -> str:
        return super().get_full_url(path) +'.json'

    @make_with_self(Tweet)
    async def tweet(self, body: str, media: list[Media] | str | tuple[bytes, str] | None = None):
        """
            Post a tweet.
            Media can be:
              - a file path
              - a URL
              - some media already uploaded
              - a bytes-like obj a tupled with a file extension
        """
        data = { 'status': body }
        if media is not None and not isinstance(media, list):
            media = [await self._upload_api.upload(media)]
        if media:
            data |= { 'media_ids': ','.join(str(m.id) for m in media) }
        return await self.post_json( '/statuses/update',
            data = data
        )

    @make_with_self(Following)
    async def check_follow(self, a: User | str, b: User | str):
        """ Get the relationship between two users. """
        if isinstance(a, User): a = a.at
        if isinstance(b, User): b = b.at
        return await self.get_json( '/friendships/show', {
            'source_screen_name': a,
            'target_screen_name': b
        })

    async def delete(self, tweet: Tweet | int | str):
        id = get_tweet_id(tweet)
        await self.post_json(F'/statuses/destroy/{id}')

    async def retweet(self, tweet: Tweet | int | str):
        id = get_tweet_id(tweet)
        await self.post_json(F'/statuses/retweet/{id}')

    async def quote_tweet(self, body: str, quoting: Tweet | str, media: list[Media] | str | tuple[bytes, str] | None = None) -> Tweet:
        if isinstance(quoting, Tweet):
            quoting = quoting.link()
        if not RE_TWEET_LINK.match(quoting):
            raise ValueError(F"Not recognized as a valid tweet link for QRT: {quoting}")
        body += ' {quoting}'
        return await self.tweet(body, media)

    async def upload_media(self, file_: str | tuple[bytes, str]) -> Media:
        """ Upload a new media file to twitter for attaching to tweets.
            File can be:
              - a file path
              - a URL
              - a bytes-like obj a tupled with a file extension
        """
        return await self._upload_api.upload(file_)