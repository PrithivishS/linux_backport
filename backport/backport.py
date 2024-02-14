#!/usr/bin/python3

import pdb
import subprocess
import re
import fileinput
import sys
import importlib
import argparse
import pickle
from git_utils import *
from bp_utils import *

def apply_next_patch(state):
    print_log("@@apply_next_patch", state)
    patch_list = state['patch_list']
    patch = patch_list[0]

    print_patch_dict("@@ cherry picking :", patch, state)
    git_cherry_pick(patch['sha1'])
    state['patch_list'] = patch_list[1:] #pop
    
    if git_repo_is_clean():
        build(state)
    save_cp(state)

def unapplied_patches(state):
    print_log("@@how_unapplied_patches", state)
    print_patch_list("", state)

def do_pdb(state):
    print_log("@@pdb", state)
    pdb.set_trace()

def checkpoint(state):
    print_log("@@checkpoint", state)
    save_cp(state)

def pop_unapplied(state):
    print_log("@@pop_unapplied", state)
    if len(state['patch_list']) > 1:
        state['patch_list'] = state['patch_list'][1:]
    else:
        state['patch_list'] = list() # not the worst choice
    checkpoint(state)

def pop_applied(state):
    print_log("@@do_pop_applied", state)
    os.system("git reset --hard HEAD^")
    short_git_log(state)

def short_git_log(state):
    print_log("@@how_short_git_log", state)
    git_short_log('%<(10) %h  %<(12) %an : %s', state)

def bash(state):
    print_log("@@bash", state)
    subprocess.run(['bash'])

def log_note(state):
    print_log("@@log_note", state)
    s = input("enter text to be appended to the log: ")
    print(s, file = state)

def patch_info(state):
    print_log("@@patch_info", state)
    prompted_show_sha_info(state)

def build(state):
    print_log("@@build", state)
    line_fn = lambda line, state: print_log(line, state)
    prompt_to_set_or_alter_state('build_cmd', state)
    if not state['build_cmd']:
        return

    # do it, ignore ret text(for now @ least)
    # assume build_cmd is of the form: <cmd> <arg string>
    L = state['build_cmd'].split(' ')
    shell_args = ' '.join(L[1:])
    poll_shell_cmd(L[0], shell_args, line_fn, state)

def backup_branch(state):
    print_log("@@backup_branch", state)
    line_fn = lambda line, state: print_log(line, state)
    prompt_to_set_or_alter_state('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    cmd_args = ' '.join(state['branch_backup_cmd'].split(' ')[1:])
    out = poll_shell_cmd('git', cmd_args, line_fn, state)

def move_top_applied_patch_to_unapplied(state):
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
    if not confirm("Are you sure? Enter 'y' if ok, else <enter>: ", ['y']):
    	return
    
    tap_sha = git_top_of_applied_stack_sha()
    # "push" tap_sha to unapplied patches
    state['patch_list'] = [make_patch_dict(tap_sha)] + state['patch_list']
    git_pop_applied_stack()

def move_n_pick(state):
    cp_sha = input("enter SHA1 id of  patch or <enter> if none: ")
    if not cp_sha: return
    move_top_applied_patch_to_unapplied(state)
    git_cherry_pick(cp_sha)
    
def push_one_sha(state):
    print_log("@@push_one_sha", state)

    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        return
    if not confirm("Are you sure you don't need to pop top applied patch? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

    prq_sha = input("enter SHA1 id of  patch or <enter> if none: ")
    if not prq_sha: return
    
    print(show_sha_info(prq_sha))
    if not confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    # "push" prq_sha to unapplied patches
    state['patch_list'] = [make_patch_dict(prq_sha)] + state['patch_list']
    checkpoint(state)

def push_sha_list(state):
    print_log("@@push_sha_list", state)
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        return
    if not confirm("Are you sure you don't need to pop top applied patch? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

     # get the name of the sha file
    print("enter the path of a file containing one sha per line <enter> if none")
    sha_file = input("sha_file: ")
    if not sha_file: return

    import_sha_list_file(sha_file, 'prepend', state)

def update_applied_patches(state):
    print_log("@@update_applied_patches", state)
    state['applied_patch_list'] = git_applied_sha_list(state)
    save_cp(state)
    print_log(state['applied_patch_list'], state)

def git_logG(state):
    print_log("@@git_logG", state)
    line_fn = lambda line, state: print_log(get_sha_info(line, ''), state)
    print("""
    	     <search-type> : 'S' or 'G'
	     <pattern> : the text to search for
             <tag1>    : a known release tag(ex: v5.4_)
    	     <tag2>    : a known release tag subsequent to tag1""")
    tmp = input("\nenter <search_type> <pattern> <tag1> <tag2>: ")
    
    (S_or_G, pattern, tag1, tag2) = tmp.split()
    git_log_search(S_or_G, pattern, tag1, tag2, line_fn, state)
                                   
def cherry_pick_continue(state):
    if git_repo_is_clean():
        print_log("repo is clean. can't cherry-pick --continue")
        return
    print_log("@@cherry_pick_continue", state)
    git_cherry_pick_continue()

def cherry_pick_abort(state):
    print_log("@@cherry_pick_abort", state)
    if git_repo_is_clean():
        print_log("repo is clean. can't cherry-pick --abort")
        return
    git_cherry_pick_abort()

def cherry_pick_by_sha(state):
    print_log("@@cherry_pick_by_sha", state)
    if not git_repo_is_clean():
        print_log("repo is unclean. can't cherry-pick by_sha")
        return

    cp_sha = input("enter SHA1 id of  patch or <enter> if none: ")
    if not cp_sha: return
    
    print(show_sha_info(cp_sha))
    if not confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    git_cherry_pick_by_sha(cp_sha)

def show_top_unapp(state):
    show_top_unapplied_patch(state)

def show_patch_by_sha(state):
    sha = input("enter sha of patch to be shown: ")
    (ret, output) = shell_cmd("git show " + sha)
    print_log(output, state)

bp_menu_item_list = [
    #
    # main menu
    #
    {'prompt' : 'show git status', 'action': git_status},
    {'prompt' : 'short_git_log', 'action': short_git_log},
    {'prompt' : 'show unapplied patches','action': unapplied_patches},
    {'prompt' : 'apply next patch', 'action':  apply_next_patch},
    {'prompt' : 'build', 'action' : build},
    {'prompt' : 'find commits referring to pattern', 'action' : git_logG},
    {'prompt' : 'compare patch to upstream',
     'action' : compare_patch_to_upstream},
    {'prompt' : 'cherry pick actions', 'sub-menu' : [
        {'prompt' : 'show git status', 'action': git_status},
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'cherry-pick --continue',
         'action': cherry_pick_continue},
        {'prompt' : 'cherry-pick -abort',
         'action': cherry_pick_abort},
        {'prompt' : 'cherry-pick by sha',
         'action': cherry_pick_by_sha},
    ]},
    {'prompt' : 'patch stack actions', 'sub-menu' : [
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'show unapplied patches','action': unapplied_patches},
        {'prompt' : 'move top applied -> unapplied, cherry-pick by sha',
         'action':  move_n_pick},
        {'prompt' : 'move top applied commit -> unapplied',
         'action':  move_top_applied_patch_to_unapplied},
        {'prompt' : 'push one sha -> unapplied', 'action':  push_one_sha},
        {'prompt' : 'push sha list -> unapplied', 'action':  push_sha_list},
        {'prompt' : 'pop unapplied', 'action' : pop_unapplied,},
        {'prompt': 'pop applied patch', 'action' : pop_applied},
        {'prompt' : 'show top unapplied patch','action': show_top_unapp},
        ]
     },
    #
    # utility menu
    #
    {'prompt' : 'utility actions', 'sub-menu' : [
        {'prompt' : 'patch_info(sha)', 'action' : patch_info},
        {'prompt' : 'launch pdb', 'action' : do_pdb},
        {'prompt' : 'launch bash', 'action' : bash},
        {'prompt' : 'increment git branch', 'action' : next_branch},
        {'prompt' : 'backup branch', 'action' : backup_branch},
        {'prompt' : 'update applied patch_list',
         'action' : update_applied_patches},
        {'prompt' : 'save checkpoint', 'action' : checkpoint},
        {'prompt' : 'note to log file', 'action' : log_note},
        {'prompt': 'show_patch_by_sha', 'action' : show_patch_by_sha}
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

