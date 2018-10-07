"""
    Handling all the database interactions.
"""

import sqlite3
import json

def thread_exists(sql_cursor, thread_id):
    sql_cursor.execute("SELECT EXISTS(SELECT 1 FROM threads where id = ?);", (thread_id,))
    return sql_cursor.fetchone()[0] == 1

# store the captcha challenge for that id persistently
def store_challenge(sql_cursor, captcha_id, thread_id, hint, answers):
    hint_str = json.dumps(hint)
    answers_str = json.dumps(answers)
    
    sql_cursor.execute("INSERT INTO tokenmapping(captcha_id, thread_id) VALUES(?,?)", (captcha_id, thread_id))
    sql_cursor.execute("INSERT INTO challenges(captcha_id, answer, hint) VALUES(?, ?, ?)", (captcha_id, answers_str, hint_str))
