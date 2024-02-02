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
from datetime import datetime

def buildit(fobj):
    print_log("\n", fobj)
    print_log("Check that the applied comit:", fobj)
    print_log("\t1) has no conflicts", fobj)
    print_log("\t2) builds", fobj)
    print_log('\n and then enter "git cherry-pick --continue"', fobj)
    print_log("\nDON'T CONTINUE FROM A NON BUILDING COMMIT\n", fobj)
    do_bash(fobj)
    input("<enter> to continue, else <control-c>")

def resolve_conflicts(state):
        # resolve conflicts
    print_log("\n====  CONFLICT RESOLUTION REQUIRED ====\n",
              state['log_fobj'])
    do_git_status(state)

def apply_next_patch(state):
    print_log("@@apply_next_patch", (state['log_fobj']))
    patch_list = state['patch_list']
    patch = patch_list[0]

    print_patch_dict("@@ cherry picking :", patch, state['log_fobj'])
    if git_cherry_pick(patch['sha1']) !=0:
        resolve_conflicts(state)
    buildit(state['log_fobj'])

    state['patch_list'] = patch_list[1:] #pop
    save_cp(state)

def show_unapplied_patches(state):
    print_log("@@how_unapplied_patches", (state['log_fobj']))
    print_patch_list("", state['patch_list'], state['log_fobj'])

def do_pdb(state):
    print_log("@@do_pdb", (state['log_fobj']))
    pdb.set_trace()

def do_checkpoint(state):
    print_log("@@do_checkpoint", (state['log_fobj']))
    save_cp(state)

def do_push_unapplied(state):
    print_log("@@do_push_unapplied", (state['log_fobj']))
    sha_string = input("enter SHA1 id or <enter> if none: ")
    if len(sha_string) == 0: return
    sha_string.strip()
    print(show_sha_info(sha_string))
    ok = input("enter 'y' if ok, else <enter>")
    if not ok: return
    push_unapplied_patch(sha_string)
    do_checkpoint(state)

def do_pop_unapplied(state):
    print_log("@@do_pop_unapplied", (state['log_fobj']))
    if len(state['patch_list']) > 1:
        state['patch_list'] = state['patch_list'][1:]
    else:
        state['patch_list'] = list() # not the worst choice
    do_checkpoint(state)

def pop_applied_patch(state):
    print_log("@@do_pop_applied", (state['log_fobj']))
    os.system("git reset --hard HEAD^")
    show_short_git_log(state)

def show_short_git_log(state):
    print_log("@@how_short_git_log", (state['log_fobj']))
    git_short_log(state, '%<(10) %h  %<(12) %an : %s')

def _do_bash(state):
    do_bash(state['log_fobj'])

def do_log_note(state):
    s = input("enter text to be appended to the log: ")
    print(s, file = state['log_fobj'])

def do_patch_info(state):
    prompted_show_sha_info(state['log_fobj'])

def do_build(state):
    prompt_to_set_or_alter_state('build_cmd', state)
    if not state['build_cmd']:
        return

    # do it
    (ret_code, ret_text) = general_shell_cmd(state['build_cmd'])
    print_log(ret_text, state['log_fobj'])
    print_log("\n** return code = %d **\n" % (ret_code), state['log_fobj'])

def do_backup_branch(state):
    prompt_to_set_or_alter_state('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    (ret_code, ret_text) = general_shell_cmd(state['branch_backup_cmd'])
    print_log(ret_text, state['log_fobj'])
    print_log("\n** return code = %d **\n" % (ret_code), state['log_fobj'])

def do_push_pre_req(state):
    # "tap" => "top applied patch"
    (ret,tap_sha) = general_shell_cmd("git rev-parse --short HEAD")
    tap_info = show_sha_info(tap_sha)
    prq_sha = input("enter SHA1 id of prereq patch or <enter> if none: ")
    prq_info = show_sha_info(prq_sha)
    print_log("""\n\nThe prequisite you've identified is:
              \t%s
    	      \nThe top applied patch on the current branch(tap) is:
    	      %s
    	      \nif you proceed, this will happen:
    	      \ttop applied patch will be pushed to the unapplied patch list
    	      \tprereq will be pushed to the unapplied patch list
    	      \ttop applied patch will be 'popped' from the current branch
	      """ % (tap_info, prq_info)
              ,
              state['log_fobj'])
    (ret, tmp) = general_shell_cmd("git status --porcelain")
    if not tmp:
        pdb.set_trace()
        # "push" tap_sha to unapplied patches
        state['patch_list'] = [make_patch_dict(tap_sha)] + state['patch_list']
        # "push" prq_sha to unapplied patches
        state['patch_list'] = [make_patch_dict(prq_sha)] + state['patch_list']
        # pop applied patch
        general_shell_cmd('git reset --hard HEAD^')
        do_checkpoint(state)
    else:
        print_log("git status not clean. no changes made",
                  state['log_fobj'])
    
bp_menu_list = [
    #
    # more important
    #
    {'prompt' : 'show git status', 'action': do_git_status},
    {'prompt' : 'short_git_log', 'action': show_short_git_log},
    {'prompt' : 'show unapplied patches',
     'action': show_unapplied_patches},
    {'prompt' : 'apply next patch', 'action':  apply_next_patch},
    {'prompt' : 'push pre req by sha', 'action':  do_push_pre_req},
    {'prompt' : 'build', 'action' : do_build},
    {'prompt' : 'backup branch', 'action' : do_backup_branch},
    #
    # less important
    #
    {'prompt' : 'patch_info(sha)', 'action' : do_patch_info},
    {'prompt' : 'push unapplied (changes next)',
     'action' : do_push_unapplied,},
    {'prompt' : 'pop unapplied (changes next)',
     'action' : do_pop_unapplied,},
    {'prompt': 'pop applied patch', 'action' : pop_applied_patch},
    {'prompt' : 'launch pdb', 'action' : do_pdb},
    {'prompt' : 'launch bash', 'action' : _do_bash},
    {'prompt' : 'increment git branch', 'action' :
     get_next_branch},
    {'prompt' : 'save checkpoint', 'action' : do_checkpoint},
    {'prompt' : 'note to log file', 'action' : do_log_note}
]

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
parser.add_argument('--log-depth', default='10',
                    help='# of commits to show on git log menu item')
parser.add_argument('--first-commit', default = 'HEAD~20',
                    help='git log will be first-commit^..HEAD')
# Parse the command line arguments
args = parser.parse_args()
state = state_init(args)

if args.sha_list:
    sha_file_to_pickled_state(state)
else:
    load_pickle_file(state)
backport_patches(state)

