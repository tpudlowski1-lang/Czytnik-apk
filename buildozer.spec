[app]
title = Czytnik
package.name = czytnik
package.domain = pl.czytnik

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,pymupdf,ebooklib,beautifulsoup4,edge-tts,certifi,charset-normalizer,idna,urllib3,requests,aiohttp,aiosignal,frozenlist,multidict,yarl,lxml

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk_path = /usr/local/lib/android/sdk/ndk/27.3.13750724
android.sdk_path = /usr/local/lib/android/sdk
android.build_tools_version = 34.0.0
android.archs = arm64-v8a
android.accept_sdk_license = True
android.skip_update = True

[buildozer]
log_level = 2
