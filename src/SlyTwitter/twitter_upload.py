import asyncio, base64, os
from io import BytesIO
from typing import Any
from SlyAPI import *
from SlyAPI.oauth1 import OAuth1

import aiofiles

from .common import make_with_self, RE_FILE_URL

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
VIDEO_EXTENSIONS = ['mp4', 'webm']

MEDIA_TYPES = {
    'mp4': 'video/mp4', 'webm': 'video/webm',
    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif'
}
#TODO: webp?

def get_media_category(ext: str, is_DM: bool):
    if ext not in MEDIA_TYPES:
        raise ValueError(F'Extension {ext} is not a valid media type')
    cat2 = MEDIA_TYPES[ext].split('/')[0] if not ext == 'gif' else 'gif'
    if is_DM:
        return F"Dm{cat2[0].upper()}{cat2[1:]}"
    else:
        return F"Tweet{cat2[0].upper()}{cat2[1:]}"

class Media(APIObj['TwitterUpload']):
    id: int

    def __init__(self, source: int | dict[str, Any], service: 'TwitterUpload'):
        super().__init__(service)
        match source:
            case int():
                self.id = source
            case {'media_id': id_}:
                self.id = id_
            case _:
                raise TypeError(F"{source} is not a valid source for Media")

    async def add_alt_text(self, text: str):
        await self._service.add_alt_text(self, text)


class TwitterUpload(WebAPI):
    base_url = 'https://upload.twitter.com/1.1/'

    def __init__(self, auth: OAuth1):
        super().__init__(auth)

    def get_full_url(self, path: str) -> str:
        return super().get_full_url(path) +'.json'

    async def add_alt_text(self, media: Media, text: str):
        if not text:
            raise ValueError("Alt text can't be empty.")
        elif len(text) > 1000:
            raise ValueError("Alt text can't be longer than 1000 characters.")

        return await self.post_json( 'media/metadata/create',
            json = {
                'media_id': str(media.id),
                'alt_text': {
                    'text': text
                }
            }
        )

    @make_with_self(Media)
    async def init_upload(self, type_: str, size: int, category: str):
        return await self.post_json(
            '/media/upload', data = {
                'command': 'INIT',
                'media_category': category,
                'media_type': type_,
                'total_bytes': str(size),
        })

    async def append_upload(self, media: Media, index: int, chunk: bytes):
        return await self.post_json(
            '/media/upload', data = {
                'command': 'APPEND',
                'media_id': str(media.id),
                'segment_index': str(index),
                'media': base64.b64encode(chunk).decode('ascii')
            })

    async def finalize_upload(self, media: Media):
        return await self.post_json(
            '/media/upload', data = {
                'command': 'FINALIZE',
                'media_id': str(media.id)
            })

    async def check_upload_status(self, media: Media):
        return await self.get_json(
            '/media/upload', data = {
                'command': 'STATUS',
                'media_id': str(media.id)
            })

    async def upload(self, file_: str | tuple[bytes, str]) -> Media:

        maxsize = 15_000_000 # bytes 

        # get the file:
        if hasattr(file_, 'url'):
            file_ = getattr(file_, 'url')
        match file_:
            
            case str() if m := RE_FILE_URL.match(file_):
                async with self.session.get(file_) as resp:
                    if resp.content_length is None:
                        raise ValueError(F"File {file_} did not report its size. Aborting download.")
                    elif resp.content_length > maxsize:
                        raise ValueError(F"File is too large to upload ({resp.content_length} bytes)")
                    raw = await resp.read()
                ext = m['ext']
            case str() if os.path.isfile(file_):
                async with aiofiles.open(file_, 'rb') as f:
                    sz = os.path.getsize(file_)
                    if sz > maxsize:
                        raise ValueError(F"File is too large to upload ({sz} bytes)")
                    raw = await f.read()
                ext = file_.split('.')[-1].lower()
            case (data, ext_):
                raw = data
                ext = ext_
            case _:
                raise TypeError(F"{file_} is not a valid bytes object, file path, or URL")

        size = len(raw)
        category = get_media_category(ext, False)

        
        if category in ('DmImage', 'TweetImage'):
            maxsize = 5_000_000 # bytes

        if size > maxsize:
            raise ValueError(F"File {file_} is too large to upload ({size/1_000_000} mb > {maxsize/1_000_000} mb).")

        # start upload:
        media = await self.init_upload(MEDIA_TYPES[ext], size, category)
        sent = 0
        index = 0
        stream = BytesIO(raw)

        # send chunks
        while sent < size:
            _append_result = await self.append_upload(
                media, index,
                stream.read(4*1024*1024) )
            # print(_append_result)
            sent = stream.tell()
            index += 1
        
        # finalize upload and wait for twitter to confirm
        status = await self.finalize_upload(media)

        if 'expires_after_secs' in status:
            pass
        else:

            while status['state'] not in ['succeeded', 'failed']:
                await asyncio.sleep(status['check_after_secs'])

                status = await self.check_upload_status(media)

        if status['state'] == 'failed':
            raise Exception(F"Upload failed: {status['processing_info']['state']}")

        return media