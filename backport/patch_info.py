#!/usr/bin/python3

#
# givenf a commit subject, find the sha1 of the commit and the tag that contains it
#

import pdb
import subprocess
import re
import argparse
import sys
from git_utils import *
from bp_utils import *
from meta_git import *

EG_ver="v6.6"
EG_pretty_fmt=" --pretty=tformat:'%<(10) %h  %<(12) %an : %s: %cd' "

#FIXME: this may be obsolete
def show_tag_info(tag):
    cmd = "git  log -1 " + tag + EG_pretty_fmt
    ret = subprocess.check_output(cmd, shell=True)
    text = ret.decode('latin-1')
    duh = text.strip()
    print("\t" + tag)
    print("\t\t" +duh)
    return duh.split(" ")[0]

def show_sha_info(sha, subj):
    tmp = get_sha_info(sha, subj)
    print(tmp)
    
def main(args):
    if args.subject and args.sha:
        sys.exit("provide only one of --sha, --subject")
    if args.subject:
        sha1_list = find_sha1_list_by_subject(subject, None, EG_ver)
        for sha in sha1_list:
            show_sha_info(sha, args.subject)
    else:
        sha1 = args.sha
        show_sha_info(sha1, args.subject)

    
parser = argparse.ArgumentParser()
parser.add_argument('--subject', default='')
parser.add_argument('--sha', default='')

# Parse the command line arguments
args = parser.parse_args()

# Access the value of the parameter
#print(args.--subject)
subject = re.escape(args.subject)
main(args)
