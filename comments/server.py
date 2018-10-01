#!/usr/bin/python3

"""
    A simple web server to handle user submitted comments. 
    This includes a custom-made captcha, based off image recognition.
    I wish to write this stuff in Go, C++ or whatever in the future.

    We require unique identifying codes for each blog-post, which dictates 
        how the comment will be stored in the db

    Ensure that the user's IP is validly logged (i.e. set X-Real-IP in nginx)

    Flow is (U=user, S=server):
        U->S: user requests captcha
        S->U: server sends UUID, and captcha data (if they've tried too often recently, tell them to back-off)
        U->S: UUID, captcha guess
        S->U: status, one-time usable captcha secret  - 
                status: either ok, or not ok, or timed out
                    it won't be ok if stale (i.e. give them 30secs?)
                captcha secret: a random string that allows a comment to be posted (expires after use)
                    tied to the user's requested IP address, and will expire in 5 mins
                    also tied to the thread commenting in

        if ok:
            U: probably requests comment data (AJAX request?) to stay up to date
            S: server deletes data for that query
        if not ok and only a couple of tries:
            S->U: new captcha data, UUID, && increments counter for failed tries for client
        if not ok and too many tries:
            S: blacklist the IP temporarily
            S->U: send the client a "you suck" msg, ask them to try in a min
"""

import sqlite3
# import img2ansi
import tornado.web
from urllib.parse import urlparse
import tornado.ioloop
import json


# token gen & presentation
import base64
from Crypto import Random

# domain required for origin/referer check
expected_hostname = "localhost"

sql_con = sqlite3.connect("cooldb.db")

# check if the request to our endpoints is not malicious, basically:
# https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
def check_csrf(func):
    def wrapper(self, *args, **kwargs):
        global expected_site_name

        def fail(self):
            self.set_status(400)
            self.write({"error": "csrf, please ensure Origin/Referer headers are set correctly & you are making a request with XMLHTTPRequest"})
            self.finish()
            return None

        # ensure request was made with JS
        auth_header = self.request.headers.get('X-Requested-With')
        if auth_header is None or auth_header != "XMLHTTPRequest":
            print("auth headerfail")
            return fail(self)

        # origin or referer must match my site
        received_hostything = self.request.headers.get('Origin') or self.request.headers.get('Referer')
        if received_hostything is None or urlparse(received_hostything).hostname != expected_hostname:
            print(received_hostything)
            print(urlparse(received_hostything).hostname)
            print("Origin/Referer fail")
            return fail(self)

        return func(self, *args, **kwargs)

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
        return {"hint_type": "text", "display_data": "what is the value of 5+two?"}, { "answers": ["7", "seven"] }

def store_captcha_id(captcha_id, thread_id):
    with sql_con:
        sql_con.execute("INSERT INTO tokenmapping(captcha_id, thread_id) VALUES(?, ?)", (captcha_id, thread_id))

def store_challenge(captcha_id, hint, answers):
    hint_str = json.dumps(hint)
    answers_str = json.dumps(answers)

    with sql_con:
        sql_con.execute("INSERT INTO challenges(captcha_id, answer, hint) VALUES(?, ?, ?)", (captcha_id, answers_str, hint_str))

class RequestCaptcha(tornado.web.RequestHandler):
    @check_csrf
    # return a UUID, and captcha data, to allow posting for <thread> comments
    def post(self, thread_id):
        print(self.request.headers)
        # TODO: check IP for throttling
        # TODO: check thread id exists (no need to? store_captcha_id will throw if it doesn't exist?)
        # ^ i mean, that feels a bit hacky

        # id to uniquely identify captcha request
        captcha_id = Random.get_random_bytes(32)
        # the thread this captcha token will apply to
        thread_id = int(thread_id)
        try:
            store_captcha_id(captcha_id, thread_id)
        except sqlite3.IntegrityError as e:
            print(e)
            self.set_status(400)
            self.write({"error": "invalid thread id"})
            self.finish()
            return
        
        # get captcha challenge and store it
        hint, answers = get_challenge('text')
        store_challenge(captcha_id, hint, answers)
        
        # serialise id into transportable str
        b64_str = base64.b64encode(captcha_id).decode('utf-8')
        self.set_header("X-Captcha-ID", b64_str)

        self.write(hint)
        self.finish()

class HandleCaptcha(tornado.web.RequestHandler):
    # check stuff, and return crypographic captcha token if valid
    @check_csrf
    def post(self, threadid, captchaid):
        # XXX: captchaid should be part of header?
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()

class MessageHandler(tornado.web.RequestHandler):
    # upload the message (provided they have a valid captcha key)
    @check_csrf
    def post(self, threadid):
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()

    # return a trove of all the comments that are available for that thread
    @check_csrf
    def get(self, threadid):
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()
        # TODO: i should also implement some kind of since parameter, so we reduce how many comments to return when updating

def make_app():
    return tornado.web.Application([
        # it is mandatory that requests to these are made via JS queries
        (r"/captcha/(.+)/", RequestCaptcha),
        (r"/captcha/(.+)/(.+)/attempt/", HandleCaptcha),
        (r"/comments/(.+)/", MessageHandler)

        # (r"/comments/(.+)/(.+)/", AdminMessage planned to allow me to modify/delete messages
        ])

if __name__ == "__main__":
    # need to do this to enforce foreign keys
    sql_con.execute("PRAGMA foreign_keys = ON")

    app = make_app()
    app.listen(10001, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()

