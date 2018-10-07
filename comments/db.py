"""
    Handling all the database interactions.
"""

import json


def thread_exists(sql_cursor, thread_id):
    sql_cursor.execute(
        "SELECT EXISTS(SELECT 1 FROM threads where id = ?);", (thread_id,))
    return sql_cursor.fetchone()[0] == 1

# store the captcha challenge for that id persistently


def store_challenge(sql_cursor, captcha_id, thread_id, hint, answers):
    hint_str = json.dumps(hint)
    answers_str = json.dumps(answers)

    sql_cursor.execute(
        "INSERT INTO tokenmapping(captcha_id, thread_id) VALUES(?,?)", (captcha_id, thread_id))
    sql_cursor.execute("INSERT INTO challenges(captcha_id, answer, hint) VALUES(?, ?, ?)",
                       (captcha_id, answers_str, hint_str))


def is_valid_captcha(sql_cursor, captcha_id):
    if captcha_id is None:
        return False

    # captcha id exists & isn't stale
    sql_cursor.execute(
        "SELECT EXISTS(SELECT 1 FROM tokenmapping where captcha_id=? AND DATETIME('now') < expiry);", (captcha_id,))
    exists = sql_cursor.fetchone()[0] == 1
    # if stale, remove it from the table (this is a no-op if it didn't exist)
    if not exists:
        sql_cursor.execute(
            "DELETE FROM tokenmapping WHERE captcha_id=?", (captcha_id,))
    return exists


def is_challenge_available(sql_cursor, captcha_id):
    # return whether we can solve for this captcha_id
    sql_cursor.execute(
        "SELECT EXISTS(SELECT 1 from challenges WHERE captcha_id=?)", (captcha_id,))
    return sql_cursor.fetchone()[0] == 1


def get_attempt_count(sql_cursor, captcha_id):
    sql_cursor.execute(
        "SELECT attempts FROM challenges WHERE captcha_id=?", (captcha_id,))
    return sql_cursor.fetchone()[0]


def crossvalidate_answer(sql_cursor, captcha_id, provided_attempt):

    # increment attempt count
    sql_cursor.execute(
        "UPDATE challenges SET attempts = attempts + 1 WHERE captcha_id=?", (captcha_id,))
    # check whether answer is correct
    sql_cursor.execute(
        "SELECT answer FROM challenges WHERE captcha_id=?", (captcha_id,))
    answers = json.loads(sql_cursor.fetchone()[0])["answers"]

    # current correctness is determined by whether the verbatim answer is present in the answer list
    is_valid = provided_attempt in answers
    return is_valid


def remove_captcha(sql_cursor, captcha_id):
    # delete everything about captcha_id from db
    # do this by removing from tokenmapping - all others cascade
    sql_cursor.execute(
        "DELETE FROM tokenmapping WHERE captcha_id=?", (captcha_id,))


def get_token_hash(sql_cursor, captcha_id):
    sql_cursor.execute(
        "SELECT token FROM tokens WHERE captcha_id=? AND DATETIME('now') < expiry", (captcha_id,))
    row = sql_cursor.fetchone()
    if row is None:
        # delete the token because its expired (no-op if token doesn't exist)
        sql_cursor.execute(
            "DELETE FROM tokens WHERE captcha_id=?", (captcha_id,))
        return None
    return row[0]


def comments_since(sql_cursor, thread_id, since_comment_id):
    ret_comments = []
    sql_cursor.execute(
        "SELECT id, title, commentbody, author_name FROM comments WHERE thread_id=? AND id > ?;", (thread_id, since_comment_id))
    for row in sql_cursor.fetchall():
        ret_comments.append(
            {"comment_id": row[0], "title": row[1], "body": row[2], "name": row[3]})

    return ret_comments


def store_token(sql_cursor, captcha_id, captcha_token_hash):
    sql_cursor.execute(
        "INSERT INTO tokens(captcha_id, token) VALUES(?,?)", (captcha_id, captcha_token_hash))
    sql_cursor.execute(
        "SELECT expiry FROM tokens WHERE captcha_id=?", (captcha_id,))
    return sql_cursor.fetchone()[0]


def remove_challenge(sql_cursor, captcha_id):
    sql_cursor.execute(
        "DELETE FROM challenges WHERE captcha_id=?", (captcha_id,))


def submit_post(sql_cursor, thread_id, captcha_id, title, author_name, comment_body, email_hash, ip_addr=None):
    # submit post
    sql_cursor.execute("INSERT INTO comments(thread_id, title, author_name, commentbody, emailhash, ipaddr) VALUES(?,?,?,?,?,?);",
                       (thread_id, title, author_name, comment_body, email_hash, ip_addr))
    comment_id = sql_cursor.lastrowid

    # consume captcha token (this cascades and will hit the token table)
    sql_cursor.execute(
        "DELETE FROM tokenmapping WHERE captcha_id=?", (captcha_id,))
    # sanity check that it doesn't exist
    sql_cursor.execute(
        "SELECT EXISTS(SELECT 1 from tokens WHERE captcha_id=?);", (captcha_id,))
    # oh shit, it still exists, our cascade wasn't set up correctly.
    if sql_cursor.fetchone()[0] == 1:
        raise Exception("token invalidation routine not functioning...")

    return comment_id
