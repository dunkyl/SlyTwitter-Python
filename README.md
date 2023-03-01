# ![sly logo](https://raw.githubusercontent.com/dunkyl/SlyMeta/main/sly%20logo.svg) Sly Twitter for Python

<!-- elevator begin -->

> 🚧 **This library is an early work in progress! Breaking changes may be frequent.**

> 🐍 For Python 3.10+

## No-boilerplate, *async* and *typed* Twitter access. 😋

```shell
pip install slytwitter
```

This library does not have full coverage.
Premium version 1.1 is not supported.
Currently, the following topics are supported:

* Posting and managing tweets, with media
* Reading followers

V2 may or may not work, due to changes in access policy to Twitter's API. If it is, the following topics are supported:

* Reading followers and following
* Getting users

You can directly grant user tokens using the command line, covering the whole OAuth 1.0 grant process.

<!-- elevator end -->

---

Example usage:

```python
import asyncio
from SlyTwitter import *

async def main():

    auth = OAuth1('test/app.json', 'test/user.json')
    twitter = Twitter(auth)

    tweet = await twitter.tweet('Hello, world!')
    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(tweet)
    print(follow) # @dunkyl_ follows @TechConnectify
    
asyncio.run(main())
```

---

Example CLI usage for getting authorized:

```sh
py -m SlyTwitter v1 scaffold
# ...
py -m SlyTwitter v1 grant
```

Granting credentials requires a Twitter developer account and credentials from their website. Visit [Twitter developers](https://developer.twitter.com/en/portal/dashboard) to get started.
