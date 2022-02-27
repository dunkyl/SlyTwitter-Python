# ![sly logo](https://raw.githubusercontent.com/dunkyl/SlyMeta/main/sly%20logo.svg) Sly Twitter for Python

> 🚧 **This library is an early work in progress! Breaking changes may be frequent.**

> 🐍 For Python 3.10+

## No-boilerplate, _async_ and _typed_ Twitter access. 😋

```shell
pip install slytwitter
```

This library does not have full coverage.
Version 2 and premium version 1.1 are not supported.
Currently, the following topics are supported:

* Posting and managing tweets, with media
* Reading followers

You can directly grant user tokens using the command line, covering the whole OAuth 1.0 grant process.

---

Example usage:

```python
import asyncio
from SlyTwitter import *

async def main():

    twitter = await Twitter('test/app.json', 'test/user.json')

    follow = await twitter.check_follow('dunkyl_', 'TechConnectify')

    print(follow) # @dunkyl_ follows @TechConnectify
    
asyncio.run(main())
```
