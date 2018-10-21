"""
    General utility functions.
"""

# hashing the captcha tokens
# requires python >3.6
import secrets
import hmac

# hashing the email with a time-throttled KDF
from passlib.hash import argon2
import time

# for our request_wrapper decorator
from functools import wraps

import db
import settings
from errors import *

def request_wrapper(func):
    """
    Decorator to refactor down that try except custom cruft that we use to simplify the requests,
    and ensure consistent error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # XXX: fix this, this requires the assumption that sql_con is ALWAYS the first argument.
        # I guess i can duck type it, but that's shoddy
        sql_cursor = args[0]

        try:
            sql_cursor.execute('begin')
            res = func(*args, **kwargs)
            sql_cursor.execute('commit')
            return res
        # one of our "expected errors"
        except CommentException as comment_except:
            sql_cursor.execute("rollback")
            return comment_except.get_status_code(), comment_except.get_json_error()
        # unknown error? still rollback, but propagate the exception
        except Exception as exception:
            sql_cursor.execute("rollback")
            raise exception

    return wrapper

# TODO: replace with something hard
def get_challenge(challenge_type):
    """
    @param: challenge_type
        one of text, ansi
    @return: hint,answers tuple
        hint should contain the type, and what the client should display

        hint= {
            "hint_type": "text",
            "display_data": "what is the value of 5+two?"
        }
    """
    if challenge_type == "text":
        return {"hint_type": "text", "display_data": "what is the value of 5+two?"}, \
               {"answers": ["7", "seven"]}

    raise NotImplementedError("unknown challenge type")

def generate_captcha_token(sql_cursor, captcha_id):
    # gen crypto token
    captcha_token = secrets.token_urlsafe(settings.TOKEN_BYTES)
    # make hmac, store token and captcha_id tuple
    captcha_token_hash = hmac.new(settings.HMAC_SECRET,\
                                  captcha_token.encode('utf-8'), 'sha256').digest()
    expiry = db.store_token(sql_cursor, captcha_id, captcha_token_hash)
    # remove the captcha request from challenges
    db.remove_challenge(sql_cursor, captcha_id)

    # get the expiry of newly created token
    # return it and non hashed token
    return expiry, captcha_token

def is_post_valid(post_json):
    if post_json is None:
        return False

    # enforce mandatory fields
    if "title" not in post_json or "body" not in post_json or "name" not in post_json:
        return False

    # of course they have to be strings
    if not isinstance(post_json["title"], str) or not isinstance(post_json["body"], str)\
            or not isinstance(post_json["name"], str):
        return False

    return True

def is_token_valid(sql_cursor, captcha_id, captcha_token):
    if captcha_token is None:
        return False

    token_hash = db.get_token_hash(sql_cursor, captcha_id)
    # hmac our token to see if it matches up with the DB token
    computed_hash = hmac.new(settings.HMAC_SECRET,
                             captcha_token.encode('utf-8'), 'sha256').digest()

    if token_hash is None:
        raise InvalidTokenError()
    return hmac.compare_digest(token_hash, computed_hash)

def hash_email(email):
    # hash using a strong KDF
    res_hash = argon2.using(rounds=settings.ARGON_PARAMS["rounds"],
                            memory_cost=settings.ARGON_PARAMS["memory"],
                            parallelism=settings.ARGON_PARAMS["threads"]).hash(email)

    # fuzz some time, so some side channel data isn't leaked
    time.sleep(secrets.randbelow(settings.ARGON_PARAMS["fuzzing_time"])/1000)

    return res_hash

def compare_email(email, stored_hash):
    # TODO: compare the two emails, but if email is none, or stored_hash is none, hash some dummy value
    #       return the comparison of the two, after sleeping a fuzzed amount
    raise NotImplementedError("lol")

@request_wrapper
def make_captcha(sql_cursor, thread_id, challenge_type):
    """
    @param thread_id: threads.id that the captcha is associated with
    @param challenge_type: either text/....
        determines what kind of challenge will be returned

    @return status code, json output tuple

    This function generates a captcha, and returns the json
        to send back to the requesting user.
    This captcha challenge is stored in the db for later comparison.
    """

    if not db.thread_exists(sql_cursor, thread_id):
        raise NonExistentThreadError(thread_id)

    # generate unique ID for each captcha
    captcha_id = secrets.token_urlsafe(settings.ID_BYTES)

    hint, answers = get_challenge(challenge_type)
    db.store_challenge(sql_cursor, captcha_id, thread_id, hint, answers)

    ret_json = {"id": captcha_id, "captcha": hint}

    return 200, ret_json

@request_wrapper
def validate_captcha(sql_cursor, thread_id, request_json):
    """
    Given a user provided attempt, check whether we grant them a token or not
    """

    provided_attempt = request_json["answer"] if "answer" in request_json else None
    captcha_id = request_json["id"] if "id" in request_json else None

    if provided_attempt is None:
        raise NonExistentAnswerError()

    # exists and not stale
    if not db.is_valid_captcha(sql_cursor, captcha_id) or\
       not db.is_challenge_available(sql_cursor, captcha_id):
        raise NonExistentCaptchaError(captcha_id)

    if not db.thread_exists(sql_cursor, thread_id):
        raise NonExistentThreadError(thread_id)

    attempt_number = db.get_attempt_count(sql_cursor, captcha_id) + 1

    # sanity check that we're not in a state where we didn't clean up captcha_id
    #   after too many attempts
    if attempt_number > settings.MAX_ATTEMPTS:
        raise RuntimeError("captcha_id ({}) not removed after too many attempts".format(captcha_id))

    # check if valid answer and increment number of attempts
    is_valid = db.crossvalidate_answer(sql_cursor, captcha_id, provided_attempt)
    if is_valid:
        expiry, captcha_token = generate_captcha_token(sql_cursor, captcha_id)
        ret_json = {"id": captcha_id, "status": "ok",
                    "key": {"token": captcha_token, "expiry": expiry}}
        return 200, ret_json

    # failed on the last try?
    if attempt_number == settings.MAX_ATTEMPTS:
        # delete all data relating to this captcha_id
        db.remove_captcha(sql_cursor, captcha_id)
        # tell them they need to start from another captcha
        return 200, {"id": captcha_id, "status": "restart"}

    return 200, {"id": captcha_id, "status": "try again"}


@request_wrapper
def post_comment(sql_cursor, thread_id, request_json, captcha_token):

    captcha_id = request_json["captcha_id"] if "captcha_id" in request_json else None
    post_json = request_json["post"] if "post" in request_json else None

    if captcha_token is None:
        raise MissingTokenError()

    # exists and not stale
    if not db.is_valid_captcha(sql_cursor, captcha_id):
        raise NonExistentCaptchaError(captcha_id)

    if not db.thread_exists(sql_cursor, thread_id):
        raise NonExistentThreadError(thread_id)

    if not is_token_valid(sql_cursor, captcha_id, captcha_token):
        raise InvalidTokenError()

    if not is_post_valid(post_json):
        raise InvalidPostError(post_json)

    title, comment_body, author_name = post_json["title"], post_json["body"], post_json["name"]
    # optional email field, argon2 hash it
    email = post_json["email"] if "email" in post_json else None
    email_hash = hash_email(email) if email is not None else None

    # TODO: get ip address to store

    # consume captcha token, plus post the comment to the database
    comment_id = db.submit_post(sql_cursor, thread_id, captcha_id, title,
                                author_name, comment_body, email_hash)

    return 200, {"captcha_id": captcha_id, "comment_id": comment_id}

@request_wrapper
def get_comments(sql_cursor, thread_id, since_comment_id):

    if not db.thread_exists(sql_cursor, thread_id):
        raise NonExistentThreadError(thread_id)

    # XXX: do we need to check if since_comment_id is valid..?
    return 200, {"comments": db.comments_since(sql_cursor, thread_id, since_comment_id)}
