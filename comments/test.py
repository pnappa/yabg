
import requests
import unittest
import subprocess

"""
    An automatic testing framework that ensures that the program is compliant with the protocol & generates content successfully.

    Refer to protocol/userflow.dia for the commenting protocol.
"""

def run_server():
    """
    Run the server as a debug mode.
    This mode ensures that all captchas are the same, and that there is a guaranteed number of blog entries (threads)
    """
    raise NotImplementedError("run server")

class TestCaptchaGen(unittest.TestCase):
    def test_thread_not_exists(self):
        self.assertFalse(True, msg="not implemented")

    def test_malformed_request(self):
        self.assertFalse(True, msg="not implemented")

    def test_wrong_methods(self):
        self.assertFalse(True, msg="not implemented")

    def test_thread_throttle(self):
        self.assertFalse(True, msg="not implemented")

class TestSolving(unittest.TestCase):
    def test_thread_not_exists(self):
        self.assertFalse(True, msg="not implemented")

    def test_invalid_answer(self):
        self.assertFalse(True, msg="not implemented")

    def test_invalid_captcha_id(self):
        self.assertFalse(True, msg="not implemented")

    def test_correct_answer(self):
        self.assertFalse(True, msg="not implemented")

    def test_incorrect_answer_few(self):
        self.assertFalse(True, msg="not implemented")

    def test_incorrect_answer_many(self):
        self.assertFalse(True, msg="not implemented")

    def test_wrong_methods(self):
        self.assertFalse(True, msg="not implemented")

class TestCommentPosting(unittest.TestCase):
    # solve a captcha so we can attempt to post a comment
    def get_valid_token(self):
        raise NotImplementedError("post comment")
        captcha_id, token, thread_id = None, None, None
        return captcha_id, token, thread_id

    def test_successful(self):
        self.assertFalse(True, msg="not implemented")
        
    def test_invalid_token(self):
        self.assertFalse(True, msg="not implemented")

    def test_expired_token(self):
        self.assertFalse(True, msg="not implemented")

    def test_missing_token(self):
        self.assertFalse(True, msg="not implemented")

    def test_missing_token(self):
        self.assertFalse(True, msg="not implemented")

    def test_mismatching_id_thread(self):
        self.assertFalse(True, msg="not implemented")

    def test_malformed_post(self):
        self.assertFalse(True, msg="not implemented")

def TestCommentRetrieval(unittest.TestCase):
    def test_invalid_thread(self):
        self.assertFalse(True, msg="not implemented")

    def test_invalid_since(self):
        self.assertFalse(True, msg="not implemented")

    def test_no_since(self):
        self.assertFalse(True, msg="not implemented")

    def test_since_exists(self):
        self.assertFalse(True, msg="not implemented")

if __name__ == "__main__":
    run_server()
    unittest.main()
