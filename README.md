# Yet Another Blog Generator

Yes, it's yet another blog generator. 

## Features
 - [X] Comment/Captcha API
 - [ ] Static site generation
 - [ ] Customisable templates

Yeah, it's a real work in progress.

## Running it
You'll need Python 3.6 (I use `secrets`), and probably not Python 3.7 (some of `hmac` is deprecated then).

In the git directory:
```
~/.local/build/Python-3.6.7rc1/python -m venv venv --copies
source ./venv/bin/activate
pip install -r requirements.txt
```

## Why?
I designed this as an exercise in developing a light-weight, and secure blogging platform. I want to use it for my blog, which will probably live over at https://blog.pat.sh/


## Bug Bounty
> Are you telling me a hobby project has a bug bounty?

Sure, well, security bugs that is. I don't really have much money, but I do make shirts, so I'm happy to make one and send it to you. Email me if you find something relatively serious (I guess something thats within the OWASP Top 10?) - example, XSS, SQLi, CSRF, etc.

This link will eventually work: [you can find all my shirts here](https://pat.sh/shirts)
