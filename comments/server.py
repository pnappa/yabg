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

# domain required for origin/referer check
expected_hostname = "localhost"

# check if the request to our endpoints is not malicious, basically:
# https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
def check_csrf(func):
    def wrapper(self, *args, **kwargs):
        global expected_site_name

        def fail(self):
            self.set_status(400)
            self.write({"error": "csrf"})
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

class RequestCaptcha(tornado.web.RequestHandler):
    @check_csrf
    # return a UUID, and captcha data, to allow posting for <thread> comments
    def get(self, threadid):
        print(self.request.headers)
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()

class HandleCaptcha(tornado.web.RequestHandler):
    # check stuff, and return crypographic captcha token if valid
    @check_csrf
    def post(self, threadid, captchaid):
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
        (r"/captcha/(.+)/", RequestCaptcha),
        (r"/captcha/(.+)/(.+)/attempt/", HandleCaptcha),
        (r"/comments/(.+)/", MessageHandler)

        # (r"/comments/(.+)/(.+)/", AdminMessage planned to allow me to modify/delete messages
        ])

if __name__ == "__main__":
    app = make_app()
    app.listen(10001, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()

