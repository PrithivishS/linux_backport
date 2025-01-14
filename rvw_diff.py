#!/usr/bin/python3

import pdb
import tempfile
import os
import subprocess
import re
import difflib

def tempfile_notes():    
    (bp_fd, bp_path) = tempfile.mkstemp() # "bp" -> backported
    (us_fd, us_path) = tempfile.mkstemp() # "us" -> upstream
    print(bp_path + "," + us_path)
    # get output, do stuff
    # clean up tmp files
    os.close(bp_fd); os.close(us_fd)
    os.unlink(bp_path); os.unlink(us_path)

# return upstream sha if found and True for explanations if found
def parse_header(hdr):
    pattern = rf"\b{re.escape('commit')}\s+(\w+)\s+{re.escape('upstream')}\b"
    backport_changes = False #no explained changes
    upstrm_sha = 0

    for line in hdr:
        match = re.search(pattern, line)
        if match:
            upstrm_sha = match.group(1)

        if line.upper().lstrip().startswith("[BACKPORT CHANGES]"):
            backport_changes = True

    return (upstrm_sha, backport_changes) # will fault if sha not found

def parse_diff_body(lines):
    for ix, line in enumerate(lines):
        if line.startswith("diff --git a/"):
            prefix = lines[:ix]
            diff_body = lines[ix:]
            return (prefix, diff_body)

def sanitize_diff_body(db):
    ret = []
    pattern = r'^@@ .+? @@ (.*)$'

    for line in db:
        if line.startswith("index "):
            continue
        else:
            match = re.match(pattern, line)
            if match:
                line = match.group(1)
        ret.append(line)
    return ret

def diff_list(L1, L2):
    buf = "===========\n"
    tmp = list(difflib.unified_diff(L1, L2))
    if not len(tmp):
        print("no diff **")
    else:
        count = 0
        for line in tmp:
            sw = line.startswith
            if sw("--- \n") or sw("+++ \n"):
                continue
            if sw("++") or sw("+-") or sw("--") or sw("-+"):
                buf += line + '\n'
                count += 1
        if count == 0 :
            print("no non context diff**")
        else:
            pdb.set_trace()
            print(buf)

def get_commit_parts(sha):
    result = subprocess.run(['git', 'show', sha], capture_output=True, text=True)

    # Split the output into lines and strip whitespace
    lines = [line for line in result.stdout.splitlines()]
    hdr, diff_body = parse_diff_body(lines)
    diff_body = sanitize_diff_body(diff_body)
    upstrm_sha, deviation_explntn = parse_header(hdr)
    return hdr, diff_body, upstrm_sha, deviation_explntn

def check_backported_patch(bpsha):
    bp_hdr, bp_body, bp_upstrm_sha, bp_deviation = get_commit_parts(bpsha)
    if bp_upstrm_sha == 0:
        raise Exception("no upstream patch citation")
    us_hdr, us_body, us_upstrm_sha, us_deviation = get_commit_parts(bp_upstrm_sha)
    print("backported sha: %s, \n\tupstream sha: %s, \n\tdeviation explanation:%s" % (bpsha, bp_upstrm_sha, bp_deviation))
    diff_list(bp_body, us_body)
    print("==========")

# main
while True:
    bpsha = input("enter the SHA for the backported patch<or ctrl-c>: ")
    try:
        check_backported_patch(bpsha)
    except Exception as e:
        print("something went wrong, maybe missing commit")
        print("may also be short sha is not long enough")

