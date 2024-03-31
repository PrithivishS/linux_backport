#!/usr/bin/python3

import argparse
from bp_utils import *
import menu

parser = argparse.ArgumentParser()
parser.add_argument('--pickle-num', help='checkpoint to load')
parser.add_argument('--sha-list',
                    help='File declaring py array of sha(s)')
parser.add_argument('--log-file', default="~/tmp/backkport.log",
                    help='path to log file')
parser.add_argument('--pickle-file', default='backport.pickle',
                    help='pickle file to load')
parser.add_argument('--pickle-dir', default='~/tmp',
                    help='where to store checkpoints')
parser.add_argument('--first-commit', default = 'HEAD~20',
                    help='git log will be first-commit^..HEAD', required=True)
parser.add_argument('--no-auto-save', default = 'n',
                    help='for examining pickles')
# Parse the command line arguments
args = parser.parse_args()
state = state_init(args)

if args.sha_list:
    import_sha_list_file(state['args'].sha_list, 'set', state)

state = load_pickle_file(args, state)

backport_patches(state, bp_menu_item_list)

