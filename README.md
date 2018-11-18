# Yet Another Blog Generator

Yes, it's yet another blog generator. 

## Features
 - [X] Comment/Captcha API
 - [X] Static site generation
 - [X] Customisable templates

Yeah, it's a real work in progress.

The above features work, but the ways of interacting with them aren't really well designed. I will work on the front end soon, currently comments can be posted for a post, but there's no way to delete them, or if the captcha goes wrong (user error or perhaps bad connection), things break... hard.

## Running it
You'll need Python 3.6 (I use `secrets`), and probably not Python 3.7 (some of `hmac` is deprecated then).

In the git directory:
```
~/.local/build/Python-3.6.7rc1/python -m venv venv --copies
source ./venv/bin/activate
pip install -r requirements.txt
```

To generate sites, change into the `site-generator` dir, and change some of the magic strings in main.py (provided argument to find\_posts, and the BASEURL global var). Then run.

To run the site in development mode you probably can fiddle some stuff in the .env file (the format is set in the README in `comments/`), to make sure everything works as-is. I think it shouuuuld would out of the box, but I don't hold up hope. Anyway, after running `server.py` from the comments directory. you should be able to view the page at localhost:10001/ provided you have generated the site (yep, you'll need to write a blogpost first, i'll probably ship some example posts with this one day).


## Why?
I designed this as an exercise in developing a light-weight, and secure blogging platform. I want to use it for my blog, which will probably live over at https://blog.pat.sh/


## Bug Bounty
> Are you telling me a hobby project has a bug bounty?

Sure, well, security bugs that is. I don't really have much money, but I do make shirts, so I'm happy to make one and send it to you. Email me if you find something relatively serious (I guess something thats within the OWASP Top 10?) - example, XSS, SQLi, CSRF, etc.

This link will eventually work: [you can find all my shirts here](https://pat.sh/shirts)
