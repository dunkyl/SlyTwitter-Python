import sys, asyncio, inspect

from SlyTwitter.twitter_v2 import Scope
from SlyAPI.flow import *

async def main(args: list[str]):

    match args:
        case ['v1', 'grant']:
            await grant_wizard(Scope, kind='OAuth1')
        case ['v1', 'scaffold']:
            scaffold_wizard(kind='OAuth1', override={
                "request_uri": "https://api.twitter.com/oauth/request_token",
                "authorize_uri": "https://api.twitter.com/oauth/authorize",
                "access_uri": "https://api.twitter.com/oauth/access_token"
            })
            
        case ['v2', 'grant']:
            await grant_wizard(Scope, kind='OAuth2')
        case ['v2', 'scaffold']:
            scaffold_wizard(kind='OAuth2', override={
                "token_uri": "https://api.twitter.com/2/oauth2/token",
                "auth_uri": "https://twitter.com/i/oauth2/authorize"
            })
        case _: # help
            print(inspect.cleandoc("""
            SlyTwitter command line: tool for Twitter OAuth1/2.
            Usage:
                SlyTwitter [v1|v2] [scaffold|grant]
                Same as SlyAPI, but scopes are listed in a menu.
            """))

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))