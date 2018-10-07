
from dotenv import load_dotenv
import os

# 256bits for secret key
TOKEN_BYTES = 32
# 128 bits for captcha ID
ID_BYTES = 16
HMAC_SECRET = None

TOKEN_HEADER = "X-Token"

# per captcha_id
MAX_ATTEMPTS = 3

# domain required for origin/referer check
EXPECTED_HOSTNAME = None

def init():
    global HMAC_SECRET, EXPECTED_HOSTNAME
    load_dotenv(verbose=True)
    HMAC_SECRET = os.getenv("HMAC_SECRET_KEY").encode('utf-8')
    EXPECTED_HOSTNAME = os.getenv("EXPECTED_HOSTNAME")
