from enum import Enum
from typing import Any
from SlyAPI import *

class Scope:
    USERS_READ = 'users.read'
    TWEETS_READ = 'tweets.read'
    FOLLOWS_READ = 'follows.read'

class TweetField(Enum):
    ATTACHMENTS = 'attachments'
    AUTHOR_ID = 'author_id'
    CONTEXT_ANNOTATIONS = 'context_annotations'
    CONVERSATION_ID = 'conversation_id'
    CREATED_AT = 'created_at'
    ENTITIES = 'entities'
    GEO = 'geo'
    ID = 'id'
    
    IN_REPLY_TO_USER_ID = 'in_reply_to_user_id'
    LANG = 'lang'
    NON_PUBLIC_METRICS = 'non_public_metrics'
    ORGANIC_METRICS = 'organic_metrics'
    PROMOTED_METRICS = 'promoted_metrics'
    PUBLIC_METRICS = 'public_metrics'
    PULICATIONS = 'publications'
    REFERENCED_TWEETS = 'referenced_tweets'
    REPLY_SETTINGS = 'reply_settings'
    SOURCE = 'source'
    TEXT = 'text'
    WITHHELD = 'withheld'

class UserField(Enum):
    CREATED_AT = 'created_at'
    DESCRIPTION = 'description'
    ENTITIES = 'entities'
    ID = 'id'
    LOCATION = 'location'
    NAME = 'name'
    PINNED_TWEET_ID = 'pinned_tweet_id'
    PROFILE_IMAGE_URL = 'profile_image_url'
    PROTECTED = 'protected'
    PUBLIC_METRICS = 'public_metrics'
    URL = 'url'
    USERNAME = 'username'
    VERIFIED = 'verified'
    WITHHELD = 'withheld'

class User:
    id: int # NOTE: represented as a string in the API
    at: str
    display_name: str

    def __init__(self, source: Any):
        match source:
            # v2 with default fields
            case { 'id': str(id_), 'username': str(at), 'name': str(display_name) }:
                self.id = int(id_)
                self.at = at
                self.display_name = display_name
            case _:
                raise ValueError(F'Unknown source for User: {source}')

    def __str__(self):
        return F'@{self.at}'


class TwitterV2(WebAPI):
    base_url = 'https://api.twitter.com/2/'
    
    def __init__(self, auth: OAuth2):
        super().__init__(auth)

    @requires_scopes('users.read')
    async def me(self) -> User:
        '''The currently authenticated user.'''
        return User((await self.get_json('users/me'))['data'])

    @requires_scopes('users.read')
    async def user(self, at: str|None=None) -> User:
        '''Get a user by their @username.'''
        if at is None:
            return await self.me()
        return User((await self.get_json(F'users/by/username/{at}'))['data'])

    @requires_scopes('users.read', 'tweet.read', 'follows.read')
    async def all_followers_of(self, user: User) -> AsyncTrans[User]:
        """ Get the list of users following a user."""
        return self.paginated(F'users/{user.id}/followers', {}, None).map(User)

    @requires_scopes('users.read', 'tweet.read', 'follows.read')
    async def all_followed_by(self, user: User) -> AsyncTrans[User]:
        """ Get the list of followed users by a user."""
        return self.paginated(F'users/{user.id}/following', {}, None).map(User)