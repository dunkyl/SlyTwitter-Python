'''
Twitter API v1.1 for uploading media
'''
import asyncio, base64, os
from io import BytesIO
from SlyAPI import *
from SlyAPI.oauth1 import OAuth1
from SlyAPI.webapi import JsonMap

import aiofiles

from .common import TwitterError, RE_FILE_URL

IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
VIDEO_EXTENSIONS = ['mp4', 'webm']

MEDIA_TYPES = {
    'mp4': 'video/mp4', 'webm': 'video/webm',
    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'
}

def get_upload_info(ext: str, is_dm: bool):
    prefix = "dm" if is_dm else "tweet"
    if ext == 'gif':
        max_size = 15_000_000
        category = prefix+'_gif'
    elif ext in IMAGE_EXTENSIONS:
        max_size = 5_000_000
        category = prefix+'_image'
    else: # video:
        # TODO: this is 512mb for ads, but I can't find the limit for tweet media
        # https://developer.twitter.com/en/docs/twitter-ads-api/creatives/overview/promoted-video-overview
        # ^ and this says only 500mb for ads...
        max_size = 15_000_000
        category = prefix+'_video'
    return max_size, category

class Media:
    id: int

    def __init__(self, source: int | JsonMap):
        match source:
            case int():
                self.id = source
            case {'media_id': int(id_)}:
                self.id = id_
            case _:
                raise TypeError(F"{source} is not a valid source for Media")


class TwitterUpload(WebAPI):
    base_url = 'https://upload.twitter.com/1.1/'

    def __init__(self, auth: OAuth1) -> None:
        super().__init__(auth)

    def get_full_url(self, path: str) -> str:
        return super().get_full_url(path) +'.json'

    async def add_alt_text(self, media: Media, text: str):
        if not text:
            raise ValueError("Alt text can't be empty.")
        elif len(text) > 1000:
            raise ValueError("Alt text can't be longer than 1000 characters.")

        await self.post_json_empty( 'media/metadata/create',
            json = {
                'media_id': str(media.id),
                'alt_text': {
                    'text': text
                }
            }
        )

    async def init_upload(self, type_: str, size: int, category: str):
        return Media(await self.post_form(
            'media/upload', data = {
                'command': 'INIT',
                'media_category': category,
                'media_type': type_,
                'total_bytes': str(size),
        }))

    async def append_upload(self, media: Media, index: int, chunk: bytes):
        return await self.post_form_empty(
            'media/upload', data = {
                'command': 'APPEND',
                'media_id': str(media.id),
                'segment_index': str(index),
                'media': base64.b64encode(chunk).decode('ascii')
            })

    async def finalize_upload(self, media: Media):
        return await self.post_form(
            'media/upload', data = {
                'command': 'FINALIZE',
                'media_id': str(media.id)
            })

    async def check_upload_status(self, media: Media):
        return await self.get_form(
            'media/upload', data = {
                'command': 'STATUS',
                'media_id': str(media.id)
            })

    async def upload(self, file_: str | tuple[bytes, str]) -> Media:
        # get the file:
        if hasattr(file_, 'url'):
            file_ = getattr(file_, 'url')

        match file_:
            case str() if m := RE_FILE_URL.match(file_):
                ext = m['ext']
            case str() if os.path.isfile(file_):
                ext = file_.split('.')[-1].lower()
            case (_, ext_):
                ext = ext_
            case _:
                raise TypeError(F"{file_} is not a valid bytes object, file path, or URL")
            
        maxsize, category = get_upload_info(ext, False)

        match file_:
            case str() if m := RE_FILE_URL.match(file_):
                async with self._client.get(file_) as resp:
                    if resp.content_length is None:
                        raise ValueError(F"File {file_} did not report its size. Aborting download.")
                    elif resp.content_length > maxsize:
                        raise ValueError(F"File is too large to upload ({resp.content_length} bytes)")
                    raw = await resp.read()
            case str() if os.path.isfile(file_):
                async with aiofiles.open(file_, 'rb') as f:
                    sz = os.path.getsize(file_)
                    if sz > maxsize:
                        raise ValueError(F"File is too large to upload ({sz} bytes)")
                    raw = await f.read()
            case (data, _):
                raw = data
            case _: raise AssertionError("impossible branch")

        size = len(raw)
        
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

        while True:
            match status:
                case { 'processing_info': { # pending
                        'check_after_secs': int(wait_secs)
                    } }:
                    await asyncio.sleep(wait_secs)
                    status = await self.check_upload_status(media)
                case { 'processing_info': {
                        'state': 'failed'
                    } }:
                    print('Upload failed:')
                    print(status)
                    raise TwitterError(status)
                case _: break # success

        return media