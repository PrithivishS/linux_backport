#!/usr/bin/python3

import argparse
import pdb

#our modules
import git_utils as git

def get_upstream_sha_lists_by_tag(args, tags):
    # this code asssumes one tag per line with a comma at eol
    sha_lists = dict()
    tags = [tag.rstrip(",") for tag in tags.split("\n") if tag]
    get_sha_list = git.get_short_sha_list_by_key # name too long
    print("getting sha_lists(this will take some time")
    for tag in tags:
        print("\t" + tag)
        sha_lists[tag] = get_sha_list(tag, args.upstream_tree_path)
    return sha_lists

# FIXME: save giant has to disk

parser = argparse.ArgumentParser()

parser.add_argument('--upstream_tree_path', help='path to upstream_git_tree')
parser.add_argument('--vendor_tree_path', help='path to vendor_git_tree')
parser.add_argument('--vendor_branch', help='vendor branch')

# Parse the command line arguments
args = parser.parse_args()

pdb.set_trace()
vendor_sha_list = git.log_sync(args.vendor_tree_path, args.vendor_branch)
