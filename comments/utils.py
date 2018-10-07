"""
    General utility functions.
"""

# requires python >3.6
import secrets

import db
import globaldata

class CommentException(Exception):
    def __init__(self, errno, status_code, err_msg):
        self.errno = errno
        self.status_code = status_code
        self.message = err_msg

    def get_json_error(self):
        """
            Convert the internal error state to one that can emit a useful json error output
        """
        return {"errno": self.errno, "error": self.message}

    def get_status_code(self):
        return self.status_code

class NonExistentThreadError(CommentException):
    def __init__(self, thread_id):
        super().__init__(errno=1, status_code=404, err_msg="invalid thread id %".format(thread_id))

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


def make_captcha(sql_cursor, thread_id, challenge_type):
    """
    @param thread_id: threads.id that the captcha is associated with
    @param challenge_type: either text/....
        determines what kind of challenge will be returned

    @return status code, json output tuple

    This function generates a captcha, and returns the json to send back to the requesting user.
    This captcha challenge is stored in the db for later comparison.
    """

    try:
        sql_cursor.execute("begin")

        if not db.thread_exists(sql_cursor, thread_id):
            raise NonExistentThreadError(thread_id)

        # generate unique ID for each captcha 
        captcha_id = secrets.token_urlsafe(globaldata.ID_BYTES)
        
        hint, answers = get_challenge(challenge_type)
        db.store_challenge(sql_cursor, captcha_id, thread_id, hint, answers)

        ret_json = {"id": captcha_id, "captcha": hint}

        sql_cursor.execute("commit")
        sql_cursor.close()

        return 200, ret_json

    # one of our "expected errors"
    except CommentException as ce:
        sql_cursor.execute("rollback")
        return ce.get_status_code(), ce.get_json_error()
    # unknown error? still rollback, but propagate the exception
    except Exception as e:
        sql_cursor.execute("rollback")
        raise e
