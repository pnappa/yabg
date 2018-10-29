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
            - hm, not sure if this is necessary now.
    TODO: replace print statements with logging statements, and add more in places.
            - some exceptions, like invalid token (non-stale) might be a good idea, to log fradulent attempts
    TODO: what about some functionality where I return a colour that's like a hash of the IP address, so that 
          when the user's name is displayed, it is in that colour.
            - why? to ensure that user's can't really copy-cat each other easily, but still reduce the entropy
              so that you can't infer someone's IP address via their username colour.
    TODO: replace email HMAC with argon2 hash
            - well, now i need to test this!
    TODO: add some revision functionality
            - what i mean by this is that users can view previous editions of each blog post. This seems nice and novel.
            - i suppose this wouldn't be part of this, but instead static file generation, and the front end would pull/display data from that based on the front-end UIs settings.

    Refer to protocol/userflow.png for the current protocol/userflow for captcha and comments.
        Although you should really look at userflow.dia, as I may have forgotten to render into a png.
"""

import sqlite3
from urllib.parse import urlparse
import tornado.web
import tornado.ioloop

import random
import db

# our libraries
import utils
import settings

SQL_CON = None

def check_csrf(func):
    """
    Check if the request to our endpoints is not unintentionally sent

    see:
        https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
    """
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

        # TODO: this might not be fully accurate! it doesn't seem to catch different ports - which are cross domain!!
        # origin or referer must match my site
        received_hostything = self.request.headers.get(
            'Origin') or self.request.headers.get('Referer')
        if received_hostything is None or urlparse(received_hostything).hostname != settings.EXPECTED_HOSTNAME:
            print(received_hostything)
            print(urlparse(received_hostything).hostname)
            print("Origin/Referer fail")
            return fail(self)

        return func(self, *args, **kwargs)

    return wrapper


class RequestCaptcha(tornado.web.RequestHandler):
    """
    Handling for /captcha/THREADID/

    Provides the client with a captcha challenge, if eligible
    """
    @check_csrf
    def post(self, thread_id):
        # TODO: check IP for throttling - can't have one guy requesting too many captchas

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.make_captcha(sql_cursor, thread_id, "text")
        sql_cursor.close()

        self.set_status(stat_code)
        self.write(ret_json)


class HandleCaptcha(tornado.web.RequestHandler):
    """
    Handling for /captcha/THREADID/solve/

    This endpoint processes the provided captcha answer, and awards token if its valid.
    """

    @check_csrf
    def post(self, thread_id):
        request_json = tornado.escape.json_decode(self.request.body)

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.validate_captcha(
            sql_cursor, thread_id, request_json)
        sql_cursor.close()

        self.set_status(stat_code)
        self.write(ret_json)


class MessageHandler(tornado.web.RequestHandler):
    """
    Handling for /comments/THREADID/

    Provides handling for posting and retrieving comments
    """

    # upload the message (provided they have a valid captcha key)
    @check_csrf
    def post(self, thread_id):
        request_json = tornado.escape.json_decode(self.request.body)
        captcha_token = None
        if settings.TOKEN_HEADER in self.request.headers:
            captcha_token = self.request.headers.get(settings.TOKEN_HEADER)

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
    """
    Handling for /comments/THREADID/requestdelete/COMMENTID/

    This will send a email to the user if the provided email matches the stored email for that comment.
    The email will contain a link to delete the post.
    """
    @check_csrf
    def post(self, thread_id, comment_id):
        # TODO: process whether they provided the right email.
        # I will do this after I change the email hash to use Argon2 instead of the hmac. Buuut, I really should pepper it too.
        #   probably a diff key to HMAC_SECRET_KEY though, just in case.
        request_json = tornado.escape.json_decode(self.request.body)

        sql_cursor = SQL_CON.cursor()
        stat_code, ret_json = utils.make_del_token(sql_cursor, thread_id, comment_id, request_json)
        sql_cursor.close()

        self.set_status(stat_code)
        self.write(ret_json)


class ProcessDeletion(tornado.web.RequestHandler):
    """
    Handling for /comments/THREADID/delete/COMMENTID/

    This is a GET request, as it will be a link sent to the user.
    I think I want it to provide an interstitial, which contains a form, upon which the user can click to complete it.
    Why? Because if its just a link, email spam filters will likely visit it to check the authenticity of the post, so
      if someone knows/guesses the other persons email, you can automatically delete their post without interaction! (:
    """
    @check_csrf
    def get(self, thread_id, comment_id):
        # TODO: process deltoken query parameter
        self.set_status(500)
        self.write({"error": "unimplemented"})
        self.finish()


class RandomRedirect(tornado.web.RequestHandler):
    """
    Getting this page will redirect the user to a random page
    """
    def get(self):
        sql_cursor = SQL_CON.cursor()
        chosen = random.choice(db.get_thread_postnames(sql_cursor))
        sql_cursor.close()

        self.redirect('/posts/{}/'.format(chosen))

def make_app():
    return tornado.web.Application([
        # it is mandatory that requests to these are made via JS queries

        # redirect to random blogpost
        (r"/random/", RandomRedirect),

        # retrieve, attempt captchas
        (r"/captcha/([^/]+)/", RequestCaptcha),
        (r"/captcha/([^/]+)/solve/", HandleCaptcha),

        # post/retrieve comments
        (r"/comments/([^/]+)/", MessageHandler),

        # request deletion token/complete deletion
        (r"/comments/(.+)/requestdelete/(.+)/", RequestDeleteToken),
        (r"/comments/(.+)/delete/(.+)/", ProcessDeletion),

        # (r"/comments/(.+)/(.+)/", AdminMessage planned to allow me to modify/delete messages


        # XXX: development fallback to serve the generated files
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': '../site-generator/generated/', "default_filename": "index.html"}),
    ])


if __name__ == "__main__":
    SQL_CON = sqlite3.connect("cooldb.db")

    # need to do this to enforce foreign keys
    SQL_CON.execute("PRAGMA foreign_keys = ON")

    # load settings
    settings.init()

    app = make_app()
    app.listen(10001, address="127.0.0.1")
    tornado.ioloop.IOLoop.current().start()
