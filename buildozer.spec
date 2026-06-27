[app]
title = Czytnik
package.name = czytnik
package.domain = org.iskra

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,pymupdf,ebooklib,beautifulsoup4,edge-tts,certifi,charset-normalizer,idna,urllib3,requests,aiohttp,aiosignal,frozenlist,multidict,yarl,lxml

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
