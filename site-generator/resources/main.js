// hm, this javascript doesn't feel very good. So, here's some stuff I can do to make it better/
// TODO:
//      - abstract the ajax into its own fn
//      - test abnormal paths - imagine failed responses from the server.. etc.
//      - is there a better way to do globals? do I use classes? do I just use polyfills to do this stuff?
//          - this feels a bit heavy weight.. I really wanna keep the site's size tiny!

window.captchaID = null;
window.captchaToken = null;

function opencomment() {
    console.log("opening comment box..");
    document.getElementById("startpostcomment").style.display = "block";
    loadcaptcha();
}

// get the thread id
function getThreadID() {
    return document.head.querySelector("[name~=postid][content]").content;
}

// for when we get the captcha challenge from the server
function onCaptchaLoad(data) {
    // we should have checks based on what kind of captcha it is:
    // if data["captcha"]["type"] == "text" blah blah
    // but for now, lets be lazy
    document.getElementById("question").innerText = data["captcha"]["display_data"];
    window.captchaID = data["id"];
    // TODO: store captchaID expiry (so that at submit we can check client side, before sending, just to avoid messy request handling less often)

    // hide the spinner
    document.getElementById("captchaspinner").style.display = "none";
    // make them able to answer!
    document.getElementById("captchaloaded").style.display = "block";
}

function loadcaptcha() {
    console.log("loading captcha");

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log("received ajax response");
            onCaptchaLoad(JSON.parse(this.responseText));
        }
    };
    xhttp.open("POST", "/captcha/" + getThreadID() + "/", true);
    xhttp.setRequestHeader("X-Requested-With", "XMLHTTPRequest");
    xhttp.send();
}

function checkCaptcha(callback) {
    // TODO: build the ajax request to send the captcha data back (id, and answer)
    // TODO: somehow build error?

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log("received ajax response");
            callback(JSON.parse(this.responseText));
        } else {
            console.log("error checking captcha?");
            console.log(this.responseText);
            // probably load new image depending on err msg number
        }
    };
    xhttp.open("POST", "/captcha/" + getThreadID() + "/solve/", true);
    xhttp.setRequestHeader("X-Requested-With", "XMLHTTPRequest");
    xhttp.setRequestHeader("Content-Type", "application/json");
    var data = JSON.stringify({"id": window.captchaID, "answer": document.getElementsByName("captchaanswer")[0].value});
    xhttp.send(data);
}

function submitComment() {
    checkCaptcha((captchaResult) => {
        // TODO: this error check doesn't work i think - should build a functional one lol
        //if (err) {
        //    console.log("failed to submit captcha?");
        //    console.log(err);
        //}

        // TODO: build the ajax request to submit the comment
        // should involve the ID, captcha token, and form contents
        console.log(captchaResult);

        window.captchaToken = captchaResult["key"]["token"];
        let spc = document.getElementById("startpostcomment");
        let postTitle = spc.children["title"].value;
        let postName = spc.children["name"].value;
        let postEmail = spc.children["email"].value;
        let postBody = spc.children["body"].value;


        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                console.log("received ajax response");
                console.log(JSON.parse(this.responseText));
            } else {
                console.log("error checking captcha?");
                console.log(this.responseText);
                //TODO: error handling
            }
        };
        xhttp.open("POST", "/comments/" + getThreadID() + "/", true);
        xhttp.setRequestHeader("X-Requested-With", "XMLHTTPRequest");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.setRequestHeader("X-Token", window.captchaToken);
        let commentJson = {};
        commentJson["title"] = postTitle;
        commentJson["name"] =  postName;
        commentJson["body"] = postBody;
        if (postEmail) {
            commentJson["email"] = postEmail;
        }

        console.log("captchaID:" + window.captchaID + " token:" + window.captchaToken);
        var data = JSON.stringify({"captcha_id": window.captchaID, "post": commentJson});
        xhttp.send(data);

    });
}


function loadComments() {
    // TODO
    console.log("TODO: load the comments in");
}

window.onload = loadComments;
