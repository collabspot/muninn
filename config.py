TWITTER_CLIENT_KEY = ""
TWITTER_SECRET_KEY = ""

GOOGLE_CLIENT_KEY = ""
GOOGLE_SECRET_KEY = ""

GITHUB_CLIENT_KEY = ""
GITHUB_SECRET_KEY = ""

try:
    from config_local import *
except ImportError:
    pass
