#!/usr/bin/python3

"""
    A simple web server to handle user submitted comments.
    This includes a custom-made captcha, based off image recognition.
    I wish to write this stuff in Go, C++ or whatever in the future.
        Why? Well, to make it extremely low profile.
        It would also require switching DB to a KV store - which is entirely doable, and should provide some speedup.

    We require unique identifying codes for each blog-post, which dictates
        how the comment will be stored in the db

    TODO: Ensure that the user's IP is validly logged (i.e. set X-Real-IP in nginx)
    TODO: Change all SQL into stored procedures.
    TODO: careful of TOCTOU bugs. I should coagulate databse interactions more, methinks.

    Refer to protocol/userflow.png for the current protocol/userflow for captcha and comments.
        Although you should really look at userflow.dia, as I may have forgotten to render into a png.

"""

import sqlite3
from urllib.parse import urlparse
import tornado.web
import tornado.ioloop

# our libraries
import utils
import globaldata

SQL_CON = None

# check if the request to our endpoints is not malicious, basically:
# https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
def check_csrf(func):
    def wrapper(self, *args, **kwargs):
        def fail(self):
            self.set_status(400)
            self.write(
                {"error": "csrf, please ensure Origin/Referer headers are set correctly & you are making a request with XMLHTTPRequest"})
            self.finish()

        # ensure request was made with JS
        auth_header = self.request.headers.get('X-Requested-With')
        if auth_header is None or auth_header != "XMLHTTPRequest":
            print("auth headerfail")
            return fail(self)

        # origin or referer must match my site
        received_hostything = self.request.headers.get(
            'Origin') or self.request.headers.get('Referer')
        if received_hostything is None or urlparse(received_hostything).hostname != globaldata.expected_hostname:
            print(received_hostything)
            print(urlparse(received_hostything).hostname)
            print("Origin/Referer fail")
            return fail(self)

        return func(self, *args, **kwargs)

    return wrapper

# /captcha/THREADID/


class RequestCaptcha(tornado.web.RequestHandler):
    @check_csrf
    def post(self, thread_id):
        # TODO: check IP for throttling - can't have one guy requesting too many captchas

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.make_captcha(sql_cursor, thread_id, "text")
        sql_cursor.close()

        self.set_status(stat_code)
        self.write(ret_json)

# /captcha/THREADID/solve/


class HandleCaptcha(tornado.web.RequestHandler):
    # check stuff, and return cryptographic captcha token if valid
    @check_csrf
    def post(self, thread_id):
        request_json = tornado.escape.json_decode(self.request.body)

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.validate_captcha(
            sql_cursor, thread_id, request_json)
        sql_cursor.close()

        self.set_status(stat_code)
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

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.post_comment(
            sql_cursor, thread_id, request_json, captcha_token)
        sql_cursor.close()

        self.set_status(stat_code)
        self.write(ret_json)

    # return a trove of all the comments that are available for that thread
    # this takes a query argument, since, which filters to results to those after that comment_id
    @check_csrf
    def get(self, thread_id):
        # as comment ids are positive, comments since id>-1 will return all
        since_comment_id = self.get_argument("since", default=-1)

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.get_comments(sql_cursor, thread_id, since_comment_id)
        sql_cursor.close()

        self.set_status(stat_code)
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
    SQL_CON = sqlite3.connect("cooldb.db")

    # need to do this to enforce foreign keys
    SQL_CON.execute("PRAGMA foreign_keys = ON")

    app = make_app()
    app.listen(10001, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()
