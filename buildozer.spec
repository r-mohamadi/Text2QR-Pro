[app]
title = Text2QR Pro
package.name = text2qrpro
package.domain = org.rmoha
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,md
version = 1.0.0
requirements = python3,kivy,qrcode,pillow
orientation = portrait
android.enable_androidx = True
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
