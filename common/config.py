""" Variables should be defined at OS environment on deployment stage """
import os

# Client-side generated token, should be set to the webhook configuration at facebook application settings
FB_VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN")

#  Page Access Token can be get from facebook application settings
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PASSWD = os.environ.get("REDIS_PASSWD")
