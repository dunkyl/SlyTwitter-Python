'''
Twitter API v1.1
'''
import re
from datetime import datetime
from typing import Any
from SlyAPI import *

from .twitter_upload import Media, TwitterUpload

RE_TWEET_LINK = re.compile(r'https://twitter\.com/(?P<user>[a-z0-9_]+)/status/(?P<tweet_id>\d+)', re.IGNORECASE)
RE_USER_LINK = re.compile(r'https://twitter\.com/(?P<user>[a-z0-9_]+)', re.IGNORECASE)

class User:
    '''Twitter user, can be hydrated from a variety of sources'''
    # TODO: consider garunteeing that these three are always hydrated
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

    def __init__(self, source: dict[str, Any]):
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
                raise TypeError(F'Invalid source type for tweet: {type(source)}')

    def __str__(self):
        return F'@{self.at}'

class Following:
    '''Following relationship between two users, four possible states'''
    a: User
    b: User
    mutual: bool
    a_follows_b: bool
    b_follows_a: bool

    def __init__(self, source: dict[str, Any]):
        self.a_follows_b = source['relationship']['source']['following']
        self.b_follows_a = source['relationship']['target']['following']
        self.mutual = self.a_follows_b and self.b_follows_a
        self.a = User(source['relationship']['source'])
        self.b = User(source['relationship']['target'])

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


class Tweet:
    id: int
    author_at: str # twitter user @
    body: str

    def __init__(self, source: int | str | dict[str, Any]):
        match source:
            case int():
                self.id = source
            case str():
                if not (m := RE_TWEET_LINK.match(source)):
                    raise ValueError('Cannot create Tweet without ID, link to tweet, or dict representation')
                self.author_at = m['user']
                self.id = int(m['tweet_id'])
            case { 'id': id_, 'extended_tweet': { 'full_text': text }, 'user': { 'screen_name': user } }:
                self.id = id_
                self.body = text
                self.author_at = user
            case { 'id': id_, 'text': text, 'user': { 'screen_name': user } }:
                self.id = id_
                self.body = text
                self.author_at = user
            case _:
                raise TypeError(F"{source} is not a valid source for Tweet")

    def link(self) -> str:
        return F"https://twitter.com/{self.author_at}/status/{self.id}"

    
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
    '''Twitter V1.1 API Client'''
    base_url = 'https://api.twitter.com/1.1'
    _upload_api: TwitterUpload
    
    def __init__(self, auth: OAuth1):

        super().__init__(auth)
        self._upload_api = TwitterUpload(auth)

    def get_full_url(self, path: str) -> str:
        return super().get_full_url(path) +'.json'

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
        return Tweet(await self.post_form( '/statuses/update',
            data = data
        ))

    async def check_follow(self, a: User | str, b: User | str):
        """ Get the relationship between two users. """
        if isinstance(a, User): a = a.at
        if isinstance(b, User): b = b.at
        return Following(await self.get_json( '/friendships/show', {
            'source_screen_name': a,
            'target_screen_name': b
        }))

    async def delete(self, tweet: Tweet | int | str):
        'Delete a tweet.'
        tweet_id = get_tweet_id(tweet)
        await self.post_json(F'/statuses/destroy/{tweet_id}')

    async def retweet(self, tweet: Tweet | int | str):
        'Retweet a tweet.'
        tweet_id = get_tweet_id(tweet)
        await self.post_json(F'/statuses/retweet/{tweet_id}')

    async def quote_tweet(self, body: str, quoting: Tweet | str, media: list[Media] | str | tuple[bytes, str] | None = None) -> Tweet:
        'Post a tweet quoting another tweet.'
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
    
    async def add_alt_text(self, media: Media, text: str):
        """ Add alt text to a media file. """
        await self._upload_api.add_alt_text(media, text)