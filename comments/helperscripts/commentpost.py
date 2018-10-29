"""
Basic script to post a valid comment
Assumes static captcha answer of 7
"""


import requests

headers = {"X-Requested-With": "XMLHTTPRequest", "Origin": "http://localhost:10001/"}

captcha_answer = "7"
threadid = "1"

title = "Post title"
email = "me@pat.sh"
name = "Pat"
postbody = "hello world"


# get the captcha challenge
r = requests.post("http://localhost:10001/captcha/{}/".format(threadid), headers=headers).json()
captcha_id = r["id"]

# answer the challenge, get the token
r = requests.post("http://localhost:10001/captcha/{}/solve/".format(threadid), headers=headers, json={"id": captcha_id, "answer": captcha_answer}).json()
token = r["key"]["token"]

# post the thread with the token
r = requests.post("http://localhost:10001/comments/{}/".format(threadid), headers={**headers, 'X-Token': token}, json={"captcha_id": captcha_id, "post": {"title": title, "name": name, "email": email, "body": postbody}})
print(r)
print(r.json())
comment_id = str(r.json()["comment_id"])


# request the delete token for comment for the hello world post where i just posted (for the moment, this is hardcoded)
r = requests.post("http://localhost:10001/comments/" + threadid + "/requestdelete/" + comment_id +"/", headers=headers, json={"email": email})
print(r)
print(r.json())

