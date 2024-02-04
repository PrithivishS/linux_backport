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

def menu_action_apply_next_patch(state):
    print_log("@@menu_action_apply_next_patch", (state['log_fobj']))
    patch_list = state['patch_list']
    patch = patch_list[0]

    print_patch_dict("@@ cherry picking :", patch, state['log_fobj'])
    git_cherry_pick(patch['sha1'])

    (ret, tmp) = general_shell_cmd("git status --porcelain")
    if not tmp:
        git_cherry_pick__continue()
        state['patch_list'] = patch_list[1:] #pop
    menu_action_build(state)

    save_cp(state)

def menu_action_unapplied_patches(state):
    print_log("@@how_unapplied_patches", (state['log_fobj']))
    print_patch_list("", state['patch_list'], state['log_fobj'])

def menu_action_pdb(state):
    print_log("@@menu_action_pdb", (state['log_fobj']))
    pdb.set_trace()

def menu_action_checkpoint(state):
    print_log("@@menu_action_checkpoint", (state['log_fobj']))
    save_cp(state)

def menu_action_push_unapplied(state):
    print_log("@@menu_action_push_unapplied", (state['log_fobj']))
    sha_string = input("enter SHA1 id or <enter> if none: ")
    if len(sha_string) == 0: return
    sha_string.strip()
    print(show_sha_info(sha_string))
    ok = input("enter 'y' if ok, else <enter>")
    if not ok: return
    push_unapplied_patch(sha_string)
    menu_action_checkpoint(state)

def menu_action_pop_unapplied(state):
    print_log("@@menu_action_pop_unapplied", (state['log_fobj']))
    if len(state['patch_list']) > 1:
        state['patch_list'] = state['patch_list'][1:]
    else:
        state['patch_list'] = list() # not the worst choice
    menu_action_checkpoint(state)

def menu_action_pop_applied(state):
    print_log("@@do_pop_applied", (state['log_fobj']))
    os.system("git reset --hard HEAD^")
    menu_action_short_git_log(state)

def menu_action_short_git_log(state):
    print_log("@@how_short_git_log", (state['log_fobj']))
    git_short_log(state, '%<(10) %h  %<(12) %an : %s')

def menu_action_bash(state):
    print_log("@@menu_action_bash", (state['log_fobj']))
    subprocess.run(['bash'])

def menu_action_log_note(state):
    print_log("@@menu_action_log_note", (state['log_fobj']))
    s = input("enter text to be appended to the log: ")
    print(s, file = state['log_fobj'])

def menu_action_patch_info(state):
    print_log("@@menu_action_patch_info", (state['log_fobj']))
    prompted_show_sha_info(state['log_fobj'])

def menu_action_build(state):
    print_log("@@menu_action_build", (state['log_fobj']))
    prompt_to_set_or_alter_state('build_cmd', state)
    if not state['build_cmd']:
        return

    # do it
    (ret_code, ret_text) = general_shell_cmd(state['build_cmd'])
    print_log(ret_text, state['log_fobj'])
    print_log("\n** return code = %d **\n" % (ret_code), state['log_fobj'])

def menu_action_backup_branch(state):
    print_log("@@menu_action_backup_branch", (state['log_fobj']))
    prompt_to_set_or_alter_state('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    (ret_code, ret_text) = general_shell_cmd(state['branch_backup_cmd'])
    print_log(ret_text, state['log_fobj'])
    print_log("\n** return code = %d **\n" % (ret_code), state['log_fobj'])

def menu_action_push_pre_req(state):
    print_log("@@menu_action_push_pre_req", (state['log_fobj']))
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
        # "push" tap_sha to unapplied patches
        state['patch_list'] = [make_patch_dict(tap_sha)] + state['patch_list']
        # "push" prq_sha to unapplied patches
        state['patch_list'] = [make_patch_dict(prq_sha)] + state['patch_list']
        # pop applied patch
        general_shell_cmd('git reset --hard HEAD^')
        menu_action_checkpoint(state)
    else:
        print_log("git status not clean. no changes made",
                  state['log_fobj'])
def menu_action_update_applied_patches(state):
    print_log("@@menu_action_update_applied_patches", (state['log_fobj']))
    state['applied_patch_list'] = git_applied_sha_list(state)
    save_cp(state)
    print_log(state['applied_patch_list'], state['log_fobj'])

def menu_action_git_logG(state):
    print_log("@@menu_action_git_logG", (state['log_fobj']))
    print("""<pattern> : the text to search for
             <tag1>    : a known release tag(ex: v5.4_)
    	     <tag2>    : a known release tag subsequent to tag1""")
    tmp = input("\nenter  <pattern> <tag1> <tag2>: ")
    
    (pattern, tag1, tag2) = tmp.split()
    (ret, tmp) = general_shell_cmd("git log --oneline -G%s %s...%s"
                                   % (pattern, tag1, tag2))
    print_log(tmp, state['log_fobj'])
                                   
def menu_action_cherry_pick_continue(state):
    print_log("@@menu_actioncherry_pick_continue", (state['log_fobj']))
    git_cherry_pick__continue()
    
bp_menu_item_list = [
    #
    # more important
    #
    {'prompt' : 'show git status', 'action': menu_action_git_status},
    {'prompt' : 'short_git_log', 'action': menu_action_short_git_log},
    {'prompt' : 'show unapplied patches',
     'action': menu_action_unapplied_patches},
    {'prompt' : 'apply next patch',
     'action':  menu_action_apply_next_patch},
    {'prompt' : 'push prereq by sha', 'action':  menu_action_push_pre_req},
    {'prompt' : 'cherry-pick --continue',
     'action': menu_action_cherry_pick_continue},
    {'prompt' : 'build', 'action' : menu_action_build},
    {'prompt' : 'backup branch', 'action' : menu_action_backup_branch},
    {'prompt' : 'find commits referring to pattern',
     'action' : menu_action_git_logG},
    #
    # less important
    #
    {'prompt' : 'utility actions', 'sub-menu' : [
        {'prompt' : 'patch_info(sha)', 'action' : menu_action_patch_info},
        {'prompt' : 'push unapplied (changes next)',
         'action' : menu_action_push_unapplied,},
        {'prompt' : 'pop unapplied (changes next)',
         'action' : menu_action_pop_unapplied,},
        {'prompt': 'pop applied patch', 'action' : menu_action_pop_applied},
        {'prompt' : 'launch pdb', 'action' : menu_action_pdb},
        {'prompt' : 'launch bash', 'action' : menu_action_bash},
        {'prompt' : 'increment git branch', 'action' :
         menu_action_next_branch},
        {'prompt' : 'update applied patch_list'
         , 'action' : menu_action_update_applied_patches},
        {'prompt' : 'save checkpoint', 'action' : menu_action_checkpoint},
        {'prompt' : 'note to log file', 'action' : menu_action_log_note}
        ]
     }
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
parser.add_argument('--first-commit', default = 'HEAD~20',
                    help='git log will be first-commit^..HEAD', required=True)
# Parse the command line arguments
args = parser.parse_args()
state = state_init(args)

if args.sha_list:
    sha_file_to_pickled_state(state)
else:
    load_pickle_file(state)
backport_patches(state, bp_menu_item_list)

