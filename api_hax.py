#!/usr/bin/python3

import pdb
import argparse
import requests
from github import Github
from github import Auth
import inspect


def add_commit_comment(args, commit_sha, comment):
    print("not ready for prime time")
    return
    session = get_session(args)
    url = "https://github.com/AMDEPYC/backport_tools/commit/" + commit_sha
    print(f"url: {url}")
    headers = {
        "Authorization": f"token {args.github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment}

    res = session.get('https://login.live.com')
    cookies = dict(res.cookies)
    response = session.post('https://login.live.com',
                        auth=('Email', 'Password'),
                        verify=False,
                        cookies=cookies)
    if response.ok: print("slap my head and call me tater")

    #response = session.post(url, headers=headers, data=data)
    
    if response.status_code == 201:
        print("Comment added successfully")
    else:
        #print(f"Error: {response.status_code}, {response.text}")
        print(f"Error: {response.status_code}")

# handle args
parser = argparse.ArgumentParser(description="diff review tool")
parser.add_argument("-ghu", "--github_user", type=str, help="your github user id")
parser.add_argument("-ght", "--github_token", type=str, help="your github access token")

args = parser.parse_args()

if not args.github_user or not args.github_token:    
    print("automatic access to github not possible. Run rvw_diff.py --help and look for -ghu, -ght")

token_display = "present" if args.github_token != "" else "absent"
print(f"user: {args.github_user}, token: {token_display}")

def demo1(args):
    # one of the repos is, in fact, "Linux_Backport"
    auth = Auth.Token(args.github_token)
    g = Github(auth=auth)
    pdb.set_trace()
    for repo in g.get_user().get_repos():
        print(repo.name)
        print("=========")
        if repo.name == "Linux_Backport":
            pdb.set_trace()
        #print(dir(repo))
    pdb.set_trace()
    g.close()
    pass

def demo2(args):
    # one of the repos is, in fact, "Linux_Backport"
    auth = Auth.Token(args.github_token)
    g = Github(auth=auth)
    r = g.get_repo("AMDEPYC/backport_tools")

    sha = "69403a22744f5761d1b864babc12bda0b22403b6"
    c = r.get_commit(sha)
    for cmnt in c.get_comments():
        pdb.set_trace()
        print("hey")
    pdb.set_trace()
    return (g, r)
    pass

def demo3(args, sha):
    # one of the repos is, in fact, "Linux_Backport"
    auth = Auth.Token(args.github_token)
    g = Github(auth=auth)
    r = g.get_repo("AMDEPYC/backport_tools")
    c = r.get_commit(sha)
    #print top comment
    c.create_comment("Hello Walter")
    for cmnt in c.get_comments():
        print(cmnt.body)
        print("\t== hey ==")
    return (g, r, c, cmnt)

def add_comment(args, sha, comment):
    # one of the repos is, in fact, "Linux_Backport"
    auth = Auth.Token(args.github_token)
    g = Github(auth=auth)
    r = g.get_repo("AMDEPYC/backport_tools")
    c = r.get_commit(sha)
    c.create_comment(comment)
    return (g)
    pass

def main(args):
    #g = demo1(args)
    #(g,r) = demo2(args); g.close()
    #(g, r, c, cmnt) = demo3(args, "69403a22744f5761d1b864babc12bda0b22403b6");g.close()
    g = add_comment(args, "69403a22744f5761d1b864babc12bda0b22403b6", "That'll do pig. That'll do.");g.close()
    print("boy howdy")

main(args)
