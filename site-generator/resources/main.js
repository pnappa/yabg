// hm, this javascript doesn't feel very good. So, here's some stuff I can do to make it better/
// TODO:
//      - abstract the ajax into its own fn
//      - test abnormal paths - imagine failed responses from the server.. etc.
//      - is there a better way to do globals? do I use classes? do I just use polyfills to do this stuff?
//          - this feels a bit heavy weight.. I really wanna keep the site's size tiny!
//      - the ajax error code, i don't know it - i have to research what the error codes and stuff mean.

window.captchaID = null;
window.captchaToken = null;

function openComment() {
    console.log("opening comment box..");
    document.getElementById("startpostcomment").style.display = "block";
    loadCaptcha();
}

// get the thread id
function getThreadID() {
    return document.head.querySelector("[name~=postid][content]").content;
}

function sendJSON(method, endpoint, data, callback, extraHeaders) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = callback;
    xhttp.open(method, endpoint, true);
    xhttp.setRequestHeader("X-Requested-With", "XMLHTTPRequest");
    xhttp.setRequestHeader("Content-Type", "application/json");
    if (extraHeaders) {
        for (let head of extraHeaders) {
            xhttp.setRequestHeader(head[0], head[1]);
        }
    }
    if (data) {
        xhttp.send(data);
    } else {
        xhttp.send();
    }
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

function loadCaptcha() {
    console.log("loading captcha");

    sendJSON("POST", "/captcha/" + getThreadID() + "/", null, function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log("received ajax response");
            onCaptchaLoad(JSON.parse(this.responseText));
        }
    });
}

// build the ajax request to send the captcha data back (id, and answer)
function checkCaptcha(callback) {

    // TODO: somehow build error?
    
    var data = JSON.stringify({"id": window.captchaID, "answer": document.getElementsByName("captchaanswer")[0].value});
    sendJSON("POST", "/captcha/" + getThreadID() + "/solve/", data, function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log("received ajax response");
            callback(JSON.parse(this.responseText));
        } else {
            console.log("error checking captcha?");
            console.log(this.responseText);
            // probably load new image depending on err msg number
        }
    });
}

function submitComment() {
    // TODO: return false if this fails, so it doesn't submit! (or preventDefault, i can't remember...)
    checkCaptcha((captchaResult) => {
        // build the ajax request to submit the comment
        // should involve the ID, captcha token, and form contents
        console.log(captchaResult);

        window.captchaToken = captchaResult["key"]["token"];
        let spc = document.getElementById("startpostcomment");

        let commentJson = {};
        commentJson["title"] = spc.children["title"].value;
        commentJson["name"] =  spc.children["name"].value;
        commentJson["body"] = spc.children["body"].value;
        // if the user has put in an email
        if (spc.children["email"].value != "") {
            commentJson["email"] = spc.children["email"].value;
        }
        var data = JSON.stringify({"captcha_id": window.captchaID, "post": commentJson});
        let finishFn = function() {
            if (this.readyState == 4 && this.status == 200) {
                console.log("received ajax response");
                console.log(JSON.parse(this.responseText));
                // TODO: fetch new comments and display commenting success? clear fields (potentially hide..?), etc?
            } else {
                console.log("error checking captcha?");
                console.log(this.responseText);
                //TODO: error handling
            }
        };
        sendJSON("POST", "/comments/" + getThreadID() + "/", data, finishFn, [["X-Token", window.captchaToken]]); 
    });

    return false;
}

function styleComment(name, title, body, posted) {
    let div = document.createElement("article");

    let titleEl = document.createElement("span");
    titleEl.innerText = title;

    let nameEl = document.createElement("span");
    nameEl.innerText = name;

    let dateEl = document.createElement("time");
    dateEl.innerText = posted;

    let bodyEl = document.createElement("p");
    bodyEl.innerText = body;

    div.appendChild(titleEl);
    div.appendChild(nameEl);
    div.appendChild(dateEl);
    div.appendChild(bodyEl);

    return div;
}


function loadAllComments() {
    // TODO
    sendJSON("GET", "/comments/" + getThreadID() + "/", null, function() {
        if (this.readyState == 4 && this.status == 200) {
            console.log(JSON.parse(this.responseText));
            let comments = JSON.parse(this.responseText)["comments"];
            for (let com of comments) {
                let commento = styleComment(com["name"], com["title"], com["body"], com["posted"]);
                document.getElementById("commentbox").appendChild(commento);
            }
        } 
    });
}

window.onload = loadAllComments;

document.getElementById("composecomment").onclick = () => { openComment(); };

document.getElementById('startpostcomment').addEventListener('submit', function(evt){
    evt.preventDefault();
    submitComment();
})
