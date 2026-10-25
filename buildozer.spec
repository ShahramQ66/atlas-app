[app]
title = Atlas Analyzer
package.name = atlasanalyzer
package.domain = ir.atlas
source.dir = .
source.include_exts = py,html,json,png,jpg
version = 1.0

requirements = python3,kivy==2.2.1,cython==0.29.36

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
