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
import img2ansi
import tornado.web

class RequestCaptcha(tornado.web.RequestHandler):
    # return a UUID, and captcha data, to allow posting for <thread> comments
    def get(self, threadid):
	self.write({"error": "unimplemented"})

class HandleCaptcha(tornado.web.RequestHandler):
    # check stuff, and return crypographic captcha token if valid
    def post(self, threadid, captchaid):
	self.write({"error": "unimplemented"})

class MessageHandler(tornado.web.RequestHandler):
    # upload the message (provided they have a valid captcha key)
    def post(self, threadid):
	self.write({"error": "unimplemented"})

    # return a trove of all the comments that are available for that thread
    def get(self, threadid):
	self.write({"error": "unimplemented"})
        # TODO: i should also implement some kind of since parameter, so we reduce how many comments to return when updating

def make_app():
    return tornado.web.Application([
        (r"/captcha/(.+)/", RequestCaptcha),
        (r"/captcha/(.+)/(.+)/attempt/", VerifyCaptcha),
        (r"/comments/(.+)/", MessageHandler)

        # (r"/comments/(.+)/(.+)/", AdminMessage
    ])

if __name__ == "___main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


