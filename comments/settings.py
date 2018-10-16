
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

# Argon parameters, tuned (refer to .env for details)
ARGON_PARAMS = {
        "rounds": None, "memory": None, "threads": None, "expected_time": None, "fuzzing_time": None
        }

def init():
    global HMAC_SECRET, EXPECTED_HOSTNAME
    load_dotenv(verbose=True)
    HMAC_SECRET = os.getenv("HMAC_SECRET_KEY").encode('utf-8')
    EXPECTED_HOSTNAME = os.getenv("EXPECTED_HOSTNAME")

    # load the argon2 parameters one by one (refer to .env for details)
    ARGON_PARAMS["rounds"] =            int(os.getenv("ARGON_ROUNDS"))
    ARGON_PARAMS["memory"] =            int(os.getenv("ARGON_MEMORY"))
    ARGON_PARAMS["threads"] =           int(os.getenv("ARGON_THREADS"))
    ARGON_PARAMS["expected_time"] =     int(os.getenv("ARGON_EXPECTED_TIME"))
    ARGON_PARAMS["fuzzing_time"] =      int(os.getenv("ARGON_FUZZING_TIME"))
