[app]
title = Atlas Analyzer
package.name = atlasanalyzer
package.domain = ir.atlas
source.dir = .
source.include_exts = py,ttf,png,jpg,json
version = 1.0

requirements = python3,kivy==2.3.0,requests,urllib3,chardet,idna,certifi,arabic-reshaper,python-bidi

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
