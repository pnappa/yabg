import os
# parsing the md files for metadata
import re

import functools
# generating rfc3339 strings
import datetime
import pytz

import logging

import shutil

# generating html from md
import markdown 
# generating the final html
from jinja2 import Environment, FileSystemLoader
JINJAENV = Environment(loader=FileSystemLoader('templates'))

def warn(msg):
    logger = logging.getLogger()
    logger.warning(msg)

def err(msg):
    try:
        logger = logging.getLogger()
        raise Exception(msg)
    except:
        logger.exception('exception triggered')

def info(msg):
    logger = logging.getLogger()
    logger.info(msg)

def parse_file(filename, postname):
    # parse the supplied pat-markdown file, and extract out the tagged metadata.

    info('parsing {}'.format(filename))
    
    mandatory_fields = ("title", "author") 
    # optional fields and their defaults if non-existent (none typically implies they may be generated for you.
    optional_fields = {"postdate": None, "publish": 'false', "id": None}

    def mini_parse(line):
        # skip empty lines
        if line.strip() == '':
            return None

        try:
            # line is of the format: [meta_type] # (meta_data)
            # this is just how i can write markdown comments that aren't rendered into html
            meta_type = re.search(r'(?<=\[)[^\]]+(?=\])', line).group(0)
            meta_data = re.search(r'(?<=# \()[^\)]+(?=\))', line).group(0)
        except:
            raise StopIteration('no more metadata..?')

        if meta_type not in mandatory_fields and meta_type not in optional_fields:
            err("unexpected post metadata in file {0} : {1}".format(filename, meta_type))

        return {meta_type:meta_data}

    built_metadata = {}
    with open(filename, 'r') as postmd:
        for line in postmd:
            try:
                data = mini_parse(line)
                # skip empty liens
                if data is None:
                    continue

                built_metadata.update(data)

            # break at the first line failed (should be body content)
            except StopIteration as e:
                break

        # check data is clean
        if any(a not in built_metadata for a in mandatory_fields):
            err("missing fields in post: {}".format(filename))
    
    # set default field data
    for meta_type, default in optional_fields.items():
        if meta_type not in built_metadata:
            built_metadata.update({meta_type: default})
            # churn some warnings out
            warn("Missing optional metadata field {}".format(meta_type))


    # add the url name (simply the dir it writes in, but this is provided to the fn tho)
    built_metadata.update({"postname": postname})
    
    built_metadata.update({"filename": filename})

    return built_metadata


# https://stackoverflow.com/a/234329
def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

def write_thread_id(post, idnum):
    # write the idnum into the metadata of the post's markdown file (prepend it)
    with open(post['filename'], 'r') as original: data = original.read()
    with open(post['filename'], 'w') as modified: modified.write("[id]: # ({})\n".format(idnum) + data)

def write_thread_date(post, date_str):
    # write the idnum into the metadata of the post's markdown file (prepend it)
    with open(post['filename'], 'r') as original: data = original.read()
    with open(post['filename'], 'w') as modified: modified.write("[postdate]: # ({})\n".format(date_str) + data)

# https://stackoverflow.com/a/8556555
def get_rfc3339_now():
    d = datetime.datetime.utcnow()
    d_with_timezone = d.replace(tzinfo=pytz.UTC)
    return d_with_timezone.isoformat()


def find_posts(directory):
    # walk through, parse the markdown fields (probably the main one will be called main.md)
    post_metadata = []
    for root, _, files in walklevel(directory, level=1):
        # ignore hidden files or the top level
        if root[root.rfind(os.path.sep)+1] == '.' or root == directory:
            continue

        if "main.md" not in files:
            err("missing markdown main.md file for post: {}".format(root))

        post_metadata.append(parse_file(os.path.join(root, "main.md"), postname=root[root.rfind(os.path.sep)+1:]))

    # extract all the thread ids explicitly set
    thread_ids = functools.reduce(lambda x,y: x + [y["id"]] if y["id"] is not None else x, post_metadata, ['0'])

    # are there any duplicates? (also includes non-published ones!!!)
    if len(thread_ids) != len(set(thread_ids)):
        err("duplicate thread ids specified")

    sorted_ids = sorted(map(int, thread_ids))

    # only parse those if it is valid (flag is set inside saying its complete)
    post_metadata = [datum for datum in post_metadata if datum["publish"] == "true"]

    # enumerate the thread IDs - to provide the ability to suggest a post number
    for datum in post_metadata:
        idnum = datum["id"]
        if idnum is None:
            suggested = sorted_ids[-1]+1
            print("Alert! The following post does not have an ID set - {}".format(datum["postname"]))
            print("Would you like to assign it post #{}? y/n (no will skip)".format(suggested))
            choice = input().strip()
            if choice == 'y':
                datum["id"] = str(suggested)

                # set the thread id for this post within the source file
                write_thread_id(datum, suggested)
            elif choice == 'n':
                err("User requested termination")
            else:
                err("invalid input, terminating")
                
            sorted_ids.append(suggested)
    

    # TODO handle includes
    # hopefully later down the track i support file includes
    # a change i'd have to do would be to parse the entire file for md comments, instead of stopping early.

    for datum in post_metadata:
        if datum["postdate"] is None:
            # TODO: ask user?
            datum["postdate"] = get_rfc3339_now()
            write_thread_date(datum, datum["postdate"])

    return post_metadata

def dump_html(html, outfile):
    # remove empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    # TODO: minify

    # create the nested folder if it doesn't exist already
    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    # save in directory (filename)
    with open(outfile, 'w') as of:
        of.write(html)

def generate_post_html(post, outfile):
    info("generating post html for {}".format(post))

    # generate the blog post body
    md = markdown.Markdown()
    with open(post["filename"], 'r') as mdIn:
        postbody = md.convert("".join(mdIn.readlines()))

    # chuck the post data into the template post.html
    template = JINJAENV.get_template("post.html")
    output = template.render(title=post["title"], postauthor=post["author"], 
                             postid=post["id"], postcontent=postbody,
                             postdate=post["postdate"]) 

    dump_html(output, outfile)

def date_sorted(posts):
    return sorted(posts, key=lambda x: x["postdate"], reverse=True)

def generate_post_list(posts, outfile):
    # generate the html page that lists all the posts in rev chronological order
    info('generating list of posts') 

    sorted_posts = date_sorted(posts)

    template = JINJAENV.get_template('list.html')
    output = template.render(posts=sorted_posts)

    dump_html(output, outfile)

def generate_front_page(posts, outfile):
    # generate the landing page with the provided posts

    sorted_posts = date_sorted(posts)

if __name__ == "__main__":
    # TODO, configuration


    logging.basicConfig(level=logging.INFO)

    # remove previously generated files to a backup
    os.makedirs('./backups', exist_ok=True)
    shutil.move('./generated', './backups/' + get_rfc3339_now())

    # XXX: this can't contain a trailing slash/pathseparator - i prob should auto filter this in the function..
    posts = find_posts('/home/pnappa/github.com/pnappa/blog-entries')

    # TODO: generate the post entry in the SQL DB for the comments (they use it as a foreign key)

    for post in posts:
        generate_post_html(post, './generated/posts/'+post['postname']+'/index.html')

    generate_post_list(posts, './generated/posts/index.html')

    generate_front_page(posts, './generated/index.html')

    # copy static files to the generated dir
    resource_dir = os.path.join(os.getcwd(),'resources/')
    src_files = os.listdir(resource_dir)
    print(src_files)
    for filename in src_files:
        fullfilename = os.path.join(resource_dir, filename)
        if os.path.isfile(fullfilename):
            info("copying resource file {}".format(fullfilename))
            shutil.copy(fullfilename, './generated')

    # TODO: deploy script

    
