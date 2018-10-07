#!/usr/bin/python3

"""
    A simple web server to handle user submitted comments. 
    This includes a custom-made captcha, based off image recognition.
    I wish to write this stuff in Go, C++ or whatever in the future.

    We require unique identifying codes for each blog-post, which dictates 
        how the comment will be stored in the db

    TODO: Ensure that the user's IP is validly logged (i.e. set X-Real-IP in nginx)
    TODO: Change all SQL into stored procedures.
    TODO: careful of TOCTOU bugs. I should coagulate databse interactions more, methinks.

    Refer to protocol/userflow.png for the current protocol/userflow for captcha and comments.

    
"""

import sqlite3
import tornado.web
from urllib.parse import urlparse
import tornado.ioloop
import json

# token gen & presentation
import secrets
# storing the captcha token/email address securely
import hmac

# our libraries
import utils
import db
import globaldata


sql_con = None

# check if the request to our endpoints is not malicious, basically:
# https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
def check_csrf(func):
    def wrapper(self, *args, **kwargs):

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
        if received_hostything is None or urlparse(received_hostything).hostname != globaldata.expected_hostname:
            print(received_hostything)
            print(urlparse(received_hostything).hostname)
            print("Origin/Referer fail")
            return fail(self)

        return func(self, *args, **kwargs)

    return wrapper

def does_thread_exist(thread_id):
    c = sql_con.cursor()
    c.execute("SELECT EXISTS(SELECT 1 FROM threads where id = ?);", (thread_id,))
    does_exist = c.fetchone()[0] == 1
    c.close()

    return does_exist

def nonexistent_thread_error(request_handler, thread_id):
    request_handler.set_status(404)
    request_handler.write({"errno": 1, "error": "invalid thread id %".format(thread_id)})
    request_handler.finish()

def captcha_answer_valid(provided, correct_answers):
    # if provided is one of the correct_answers
    return provided in correct_answers

def generate_captcha_token(captcha_id):
    c = sql_con.cursor()
    captcha_token = secrets.token_urlsafe(globaldata.TOKEN_BYTES)
    # ^ err, maybe not urlsafe? I need bytes for the hmac, but I guess i can just convert the str to bytes? Doesn't really matter, except maybe for some extreme edge case 
    
    captcha_token_hash = hmac.new(globaldata.HMAC_SECRET, captcha_token.encode('utf-8'), 'sha256').digest()
    print("tokenhashtype", type(captcha_token_hash))
    c.execute("INSERT INTO tokens(captcha_id, token) VALUES(?,?);", (captcha_id, captcha_token_hash))

    c.execute("SELECT expiry FROM tokens WHERE captcha_id=?;", (captcha_id,))
    expiry = c.fetchone()[0]

    sql_con.commit()

    c.close()

    return expiry,captcha_token

def captcha_id_nonexistent_error(request_handler):
    request_handler.set_status(400)
    request_handler.write({"errno": 7, "error": "invalid captcha id, or captcha has been reset"})
    request_handler.finish()

# check whether a captcha id exists & pertains to a particular thread
def is_captcha_id_valid(captcha_id, thread_id):
    c = sql_con.cursor()
    c.execute("SELECT EXISTS(SELECT 1 FROM tokenmapping WHERE thread_id=? AND captcha_id=?);", (thread_id, captcha_id))
    isvalid = c.fetchone()[0] == 1
    sql_con.commit()
    c.close()
    return isvalid

# check whether the captcha_token is valid
def is_token_valid(captcha_id, captcha_token):
    token_hash = hmac.new(globaldata.HMAC_SECRET, captcha_token.encode("utf-8"), 'sha256').digest()
    c = sql_con.cursor()
    c.execute("SELECT token FROM tokens WHERE captcha_id=?;", (captcha_id,))
    row = c.fetchone()
    # there isn't a token?
    if row is None:
        raise Exception("checked captcha token that didn't exist... logic error?")
    # timing safe comparison
    res = hmac.compare_digest(row[0], token_hash)
    sql_con.commit()
    c.close()
    return res

def make_post(thread_id, captcha_id, title, author_name, body, email_hash, ipaddr=None):
    # perform a sanity check that the thread_id and captcha id exist
    if not is_captcha_id_valid(captcha_id, thread_id):
        raise Exception("shit dog, somehow we made a post with a captcha_id that doesn't exist")

    c = sql_con.cursor()
    # invalidate captcha token (this will cascade into the rest)
    c.execute("DELETE FROM tokenmapping WHERE captcha_id=?;", (captcha_id,))

    # sanity check that the token doesn't exist anymore
    c.execute("SELECT EXISTS(SELECT 1 from tokens WHERE captcha_id=?);", (captcha_id,))
    sql_con.commit()
    # oh shit, it still exists, our cascade wasn't set up correctly.
    if c.fetchone()[0] == 1:
        raise Exception("token invalidation routine not functioning...")

    # store comment
    c.execute("INSERT INTO comments(thread_id, title, author_name, commentbody, emailhash, ipaddr) VALUES(?,?,?,?,?,?);", (thread_id, title, author_name, body, email_hash, ipaddr))
    comment_id = c.lastrowid
    sql_con.commit()
    c.close()

    return comment_id
            

def remove_challenge(captcha_id):
    c = sql_con.cursor()
    c.execute("DELETE FROM challenges WHERE captcha_id=?", (captcha_id,))
    sql_con.commit()
    c.close()

# /captcha/THREADID/
class RequestCaptcha(tornado.web.RequestHandler):
    @check_csrf
    def post(self, thread_id): 
        # TODO: check IP for throttling - can't have one guy requesting too many captchas
        
        sql_cursor = sql_con.cursor()
        sc, ret_json = utils.make_captcha(sql_cursor, thread_id, "text")
        sql_cursor.close()

        self.status_code = sc
        self.write(ret_json)

# /captcha/THREADID/solve/
class HandleCaptcha(tornado.web.RequestHandler):
    # check stuff, and return cryptographic captcha token if valid
    @check_csrf
    def post(self, thread_id):
        request_json = tornado.escape.json_decode(self.request.body)

        sql_cursor = sql_con.cursor()
        sc, ret_json = utils.validate_captcha(sql_cursor, thread_id, request_json)
        sql_cursor.close() 
        
        self.status_code = sc
        self.write(ret_json)

# posting a comment, and retrieving comments
# /comments/THREADID/
class MessageHandler(tornado.web.RequestHandler):
    # upload the message (provided they have a valid captcha key)
    @check_csrf
    def post(self, thread_id):
        request_json = tornado.escape.json_decode(self.request.body)
        captcha_token = None
        if globaldata.TOKEN_HEADER in self.request.headers:
            captcha_token = self.request.headers.get(globaldata.TOKEN_HEADER)

        sql_cursor = sql_con.cursor()
        sc, ret_json = utils.post_comment(sql_cursor, thread_id, request_json, captcha_token)
        sql_cursor.close()

        self.status_code = sc
        self.write(ret_json)

    # return a trove of all the comments that are available for that thread
    # this takes a query argument, since, which filters to results to those after that comment_id
    @check_csrf
    def get(self, thread_id):
        # as comment ids are positive, comments since id>-1 will return all
        since_comment_id = self.get_argument("since", default=-1)

        sql_cursor = sql_con.cursor()
        sc, ret_json = utils.get_comments(thread_id)
        sql_cursor.close()

        self.status_code = sc
        self.write(ret_json)
        
class RequestDeleteToken(tornado.web.RequestHandler):
    # ...
    @check_csrf
    def post(self, thread_id, comment_id):
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()

class ProcessDeletion(tornado.web.RequestHandler):
    @check_csrf
    def get(self, thread_id, comment_id):
        # TODO: process deltoken query parameter
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()

def make_app():
    return tornado.web.Application([
        # it is mandatory that requests to these are made via JS queries

        # retrieve, attempt captchas
        (r"/captcha/([^/]+)/", RequestCaptcha),
        (r"/captcha/([^/]+)/solve/", HandleCaptcha),

        # post/retrieve comments
        (r"/comments/([^/]+)/", MessageHandler),

        # request deletion token/complete deletion
        (r"/comments/(.+)/requestdelete/(.+)/", RequestDeleteToken),
        (r"/comments/(.+)/delete/(.+)/", ProcessDeletion),

        # (r"/comments/(.+)/(.+)/", AdminMessage planned to allow me to modify/delete messages
        ])

if __name__ == "__main__":
    sql_con = sqlite3.connect("cooldb.db")

    # need to do this to enforce foreign keys
    sql_con.execute("PRAGMA foreign_keys = ON")

    app = make_app()
    app.listen(10001, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()

