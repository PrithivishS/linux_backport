#!/usr/bin/python3

import pdb
import subprocess
import re
import fileinput
import os #FIXME: just to save typing if we land in pdb
import sys
import importlib
import argparse
import pickle
from git_utils import *
from bp_utils import *

def buildit():
    print("\n")
    print("Check that the applied comit:")
    print("\t1) has no conflicts")
    print("\t2) builds")
    print('\n and then enter "git cherry-pick --continue"')
    print("\nDON'T CONTINUE FROM A NON BUILDING COMMIT\n")
    do_bash()
    input("<enter> to continue, else <control-c>")

def resolve_conflicts():
        # resolve conflicts
    print("\n====  CONFLICT RESOLUTION REQUIRED ====\n")
    do_git_status()

def apply_next_patch(state):
    patch_list = state['patch_list']
    patch = patch_list[0]

    print_patch_dict("@@ cherry picking :", patch)
    if git_cherry_pick(patch['sha1']) !=0:
        resolve_conflicts()
    buildit()

    state['patch_list'] = patch_list[1:] #pop
    save_cp(state)

def _do_menu_1():
    print("_do_menu1")
    
def show_unapplied_patches(state):
    print_patch_list("", state['patch_list'])

def do_pdb(state):
    pdb.set_trace()

def do_checkpoint(state):
    save_cp(state)

def do_push_unapplied(state):
    sha_string = input("enter SHA1 id or <enter> if none: ")
    if len(sha_string) == 0: return
    sha_string.strip()
    d = make_patch_dict(sha_string)
    print_patch_dict("", d)
    ok = input("enter 'y' if ok, else <enter>")
    if not ok: return
    state['patch_list'] = [d] + state['patch_list']

def do_pop_unapplied(state):
    if len(state['patch_list']) > 1:
        state['patch_list'] = state['patch_list'][1:]
    else:
        state['patch_list'] = list() # not the worst choice

def pop_applied_patch():
    os.system("git reset --hard HEAD^")

def show_short_git_log(state):
    git_short_log(state['log_depth'], '%<(10) %h  %<(12) %an : %s')

bp_menu_list = [
    {'prompt' : 'apply next patch', 'action':  apply_next_patch,
     'use_state' : True},
    {'prompt' : 'show git status', 'action': do_git_status, 'use_state' : False},
    {'prompt' : 'short_git_log', 'action': show_short_git_log,
     'use_state' : True},
    {'prompt' : 'show unapplied patches', 'action': show_unapplied_patches, 'use_state' : True},
    {'prompt' : 'push unapplied (changes next)',
     'action' : do_push_unapplied, 'use_state': True},
    {'prompt' : 'pop unapplied (changes next)',
     'action' : do_pop_unapplied, 'use_state': True},
    {'prompt': 'pop applied patch', 'action' : pop_applied_patch,
     'use_state' : False},
    {'prompt' : 'increment git branch', 'action' :
     get_next_branch, 'use_state': False},
    {'prompt' : 'launch pdb', 'action' : do_pdb, 'use_state': True},
    {'prompt' : 'launch bash', 'action' : do_bash, 'use_state': False},
    {'prompt' : 'save checkpoint', 'action' : do_checkpoint,
     'use_state': True},
]

def backport_patches(args):
    state = load_pickle_file(args)
    state['cp_num'] = next_cp_num(args)
    state['pickle_dir'] = args.pickle_dir
    state['pickle_file'] = args.pickle_file
    state['log_depth'] = args.log_depth

    while True:
        do_menu_choice(bp_menu_list, state)
        
parser = argparse.ArgumentParser()
add_common_args(parser)
parser.add_argument('--pickle-num', help='checkpoint to load')
parser.add_argument('--sha-list',
                    help='File declaring py array of sha(s)')

# Parse the command line arguments
args = parser.parse_args()

if args.sha_list:
    sha_file_to_pickled_state(args)
else:
    load_pickle_file(args)
backport_patches(args)

