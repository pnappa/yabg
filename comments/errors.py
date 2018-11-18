
class CommentException(Exception):
    def __init__(self, errno, status_code, err_msg):
        self.errno = errno
        self.status_code = status_code
        self.message = err_msg
        super().__init__()

    def get_json_error(self):
        """
            Convert the internal error state to one that can emit a useful json error output
        """
        return {"errno": self.errno, "error": self.message}

    def get_status_code(self):
        return self.status_code


class NonExistentThreadError(CommentException):
    def __init__(self, thread_id):
        super().__init__(errno=1, status_code=404,
                         err_msg="invalid thread id {0}".format(thread_id))


class NonExistentCaptchaError(CommentException):
    def __init__(self, captcha_id):
        super().__init__(errno=7, status_code=400,
                         err_msg="invalid captcha id {0}".format(captcha_id))

class NonExistentCommentError(CommentException):
    def __init__(self, comment_id, thread_id):
        super().__init__(errno=6, status_code=400,
                         err_msg="invalid comment id {0} for thread {1}".format(comment_id, thread_id))

class NonExistentAnswerError(CommentException):
    def __init__(self):
        super().__init__(errno=10, status_code=400,
                         err_msg="invalid answer - potentially missing")


class MissingTokenError(CommentException):
    def __init__(self):
        super().__init__(errno=8, status_code=400, err_msg="missing token")


class InvalidTokenError(CommentException):
    def __init__(self):
        super().__init__(errno=3, status_code=403, err_msg="invalid/expired token")


class InvalidPostError(CommentException):
    def __init__(self, post_json):
        super().__init__(errno=9, status_code=400,
                err_msg="missing/malformed post - are you missing mandatory fields? received: {}".format(post_json))


class InvalidEmailError(CommentException):
    """
    Thrown when provided a malformed email, not when the email is not matching the valid one.
    We don't raise when non-matching, so as to protect the email of the user
    We instead provide a message (on success and when it doesn't match):
        "Please check the provided email for a delete link"
    """
    def __init__(self):
        super().__init__(errno=4, status_code=403,
                err_msg="invalid/missing email")

