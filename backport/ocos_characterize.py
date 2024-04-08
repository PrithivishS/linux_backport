#!/usr/bin/python3

import argparse
import pickle
import pdb

#our modules
import ocos_upstream_tags as oc_tags
import git_utils as git
import persist

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
parser.add_argument('--pickle-path', default='/home/evantass/tmp/sha_list_db.pickle',
                    help='where to store checkpoints')

# Parse the command line arguments
args = parser.parse_args()

pdb.set_trace()
tags = oc_tags.upstream_tags
upstream_sha_lists_by_tag = get_upstream_sha_lists_by_tag(args, tags)

with open(args.pickle_path, 'wb') as handle:
        pdb.set_trace()
        pickle.dump(upstream_sha_lists_by_tag, handle,
                    protocol=pickle.HIGHEST_PROTOCOL)
        pdb.set_trace()
        pass
