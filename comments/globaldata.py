
# 256bits for secret key
TOKEN_BYTES = 32
# 128 bits for captcha ID
ID_BYTES = 16
# TODO: replace with secret loaded from disk
HMAC_SECRET = "testsecretpleaseignore".encode('utf-8')

TOKEN_HEADER = "X-Token"

# per captcha_id
MAX_ATTEMPTS = 3

# domain required for origin/referer check
expected_hostname = "localhost"
