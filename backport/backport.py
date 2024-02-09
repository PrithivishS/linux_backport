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
    print_log("@@menu_action_apply_next_patch", state)
    patch_list = state['patch_list']
    patch = patch_list[0]

    print_patch_dict("@@ cherry picking :", patch, state)
    git_cherry_pick(patch['sha1'])
    state['patch_list'] = patch_list[1:] #pop
    
    if git_repo_is_clean():
        menu_action_build(state)
    save_cp(state)

def menu_action_unapplied_patches(state):
    print_log("@@how_unapplied_patches", state)
    print_patch_list("", state)

def menu_action_pdb(state):
    print_log("@@menu_action_pdb", state)
    pdb.set_trace()

def menu_action_checkpoint(state):
    print_log("@@menu_action_checkpoint", state)
    save_cp(state)

def menu_action_push_unapplied(state):
    print_log("@@menu_action_push_unapplied", state)
    sha = input("enter SHA1 id or <enter> if none: ")
    if len(sha) == 0: return
    sha.strip()
    print(show_sha_info(sha))
    ok = input("enter 'y' if ok, else <enter>")
    if not ok: return

    state['patch_list'] = [make_patch_dict(sha)] + state['patch_list']
    menu_action_checkpoint(state)

def menu_action_pop_unapplied(state):
    print_log("@@menu_action_pop_unapplied", state)
    if len(state['patch_list']) > 1:
        state['patch_list'] = state['patch_list'][1:]
    else:
        state['patch_list'] = list() # not the worst choice
    menu_action_checkpoint(state)

def menu_action_pop_applied(state):
    print_log("@@do_pop_applied", state)
    os.system("git reset --hard HEAD^")
    menu_action_short_git_log(state)

def menu_action_short_git_log(state):
    print_log("@@how_short_git_log", state)
    git_short_log('%<(10) %h  %<(12) %an : %s', state)

def menu_action_bash(state):
    print_log("@@menu_action_bash", state)
    subprocess.run(['bash'])

def menu_action_log_note(state):
    print_log("@@menu_action_log_note", state)
    s = input("enter text to be appended to the log: ")
    print(s, file = state)

def menu_action_patch_info(state):
    print_log("@@menu_action_patch_info", state)
    prompted_show_sha_info(state)

def menu_action_build(state):
    print_log("@@menu_action_build", state)
    prompt_to_set_or_alter_state('build_cmd', state)
    if not state['build_cmd']:
        return

    # do it
    (ret_code, ret_text) = general_shell_cmd(state['build_cmd'])
    print_log(ret_text, state)
    print_log("\n** return code = %d **\n" % (ret_code), state)

def menu_action_backup_branch(state):
    print_log("@@menu_action_backup_branch", state)
    prompt_to_set_or_alter_state('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    (ret_code, ret_text) = general_shell_cmd(state['branch_backup_cmd'])
    print_log(ret_text, state)
    print_log("\n** return code = %d **\n" % (ret_code), state)

def move_top_applied_patch_to_unapplied():
    tap_sha = git_top_of_applied_stack_sha()
    # "push" tap_sha to unapplied patches
    state['patch_list'] = [make_patch_dict(tap_sha)] + state['patch_list']
    git_pop_applied_stack()
    
def menu_action_push_pre_req(state):
    print_log("@@menu_action_push_pre_req", state)

    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        return

    prq_sha = input("enter SHA1 id of prereq patch or <enter> if none: ")
    if not prq_sha: return
    
    move_top_applied_patch_to_unapplied()
    # "push" prq_sha to unapplied patches
    state['patch_list'] = [make_patch_dict(prq_sha)] + state['patch_list']
    menu_action_checkpoint(state)

def menu_action_push_pre_req_list(state):
    # get the name of the sha file
    print("enter the path of a file containing one sha per lineor <enter> if none")
    sha_file = input("sha_file: ")
    if not sha_file: return

    import_sha_list_file(sha_file, 'prepend', state)
    pdb.set_trace()
    pass

def menu_action_update_applied_patches(state):
    print_log("@@menu_action_update_applied_patches", state)
    state['applied_patch_list'] = git_applied_sha_list(state)
    save_cp(state)
    print_log(state['applied_patch_list'], state)

def menu_action_git_logG(state):
    print_log("@@menu_action_git_logG", state)
    print("""
    	     <search-type> : 'S' or 'G'
	     <pattern> : the text to search for
             <tag1>    : a known release tag(ex: v5.4_)
    	     <tag2>    : a known release tag subsequent to tag1""")
    tmp = input("\nenter <search_type> <pattern> <tag1> <tag2>: ")
    
    (S_or_G, pattern, tag1, tag2) = tmp.split()
    (ret, cmd, sha_list) = git_log_search(S_or_G, pattern, tag1, tag2)
    print_log("@@git_log: %s" % (cmd), state)
    for sha in sha_list:
        print_log(get_sha_info(sha, ''), state)
                                   
def menu_action_cherry_pick_continue(state):
    print_log("@@menu_actioncherry_pick_continue", state)
    git_cherry_pick__continue()
    
bp_menu_item_list = [
    #
    # main menu
    #
    {'prompt' : 'show git status', 'action': menu_action_git_status},
    {'prompt' : 'short_git_log', 'action': menu_action_short_git_log},
    {'prompt' : 'show unapplied patches',
     'action': menu_action_unapplied_patches},
    {'prompt' : 'apply next patch',
     'action':  menu_action_apply_next_patch},
    {'prompt' : 'cherry-pick --continue',
     'action': menu_action_cherry_pick_continue},
    {'prompt' : 'build', 'action' : menu_action_build},
    {'prompt' : 'backup branch', 'action' : menu_action_backup_branch},
    {'prompt' : 'find commits referring to pattern',
     'action' : menu_action_git_logG},
    {'prompt' : 'patch stack actions', 'sub-menu' : [
        {'prompt' : 'push one prereq by sha', 'action':  menu_action_push_pre_req},
        {'prompt' : 'push prereq list by sha',
         'action':  menu_action_push_pre_req_list},
        {'prompt' : 'push unapplied',
         'action' : menu_action_push_unapplied,},
        {'prompt' : 'pop unapplied',
         'action' : menu_action_pop_unapplied,},
        {'prompt': 'pop applied patch', 'action' : menu_action_pop_applied},
        ]
     },
    #
    # utility menu
    #
    {'prompt' : 'utility actions', 'sub-menu' : [
        {'prompt' : 'patch_info(sha)', 'action' : menu_action_patch_info},
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
    import_sha_list_file(state['args'].sha_list, 'set', state)
else:
    load_pickle_file(state)

backport_patches(state, bp_menu_item_list)

