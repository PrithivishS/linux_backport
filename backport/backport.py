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
    if not top_cites_upstream_or_confirmed_dont_care(state):
        print_log("no upstream citation or confirmation of indifference",
                  state)
        return
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        
    patch_list = state['unapplied_patches']
    patch = patch_list[0]

    print_patch_dict("@@ cherry picking :", patch, state)
    git_cherry_pick(patch['sha1'])
    state['unapplied_patches'] = patch_list[1:] #pop
    
    if git_repo_is_clean():
        build(state)
    save_cp(state)

def unapplied_patches(state):
    print_log("@@how_unapplied_patches", state)
    print_patch_list("", state['unapplied_patches'], state)

def do_pdb(state):
    print_log("@@pdb", state)
    pdb.set_trace()

def checkpoint(state):
    print_log("@@checkpoint", state)
    save_cp(state)

def pop_unapplied(state):
    print_log("@@pop_unapplied", state)
    if len(state['unapplied_patches']) > 1:
        state['unapplied_patches'] = state['unapplied_patches'][1:]
    else:
        state['unapplied_patches'] = list() # not the worst choice
    checkpoint(state)

def pop_applied(state):
    print_log("@@do_pop_applied", state)
    if not top_cites_upstream_or_confirmed_dont_care(state):
        print_log("no upstream citation or confirmation of indifference",
                  state)
        return
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        
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
    print_log(s, state)

def patch_info(state):
    print_log("@@patch_info", state)
    prompted_show_sha_info(state)

def backup_branch(state):
    print_log("@@backup_branch", state)
    line_fn = lambda line, state: print_log(line, state)
    prompt_to_set_or_alter_state('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    cmd = "git " + ' '.join(state['branch_backup_cmd'].split(' ')[1:])
    out = shell_cmd(cmd)
    print_log(out, state)

def move_top_applied_patch_to_unapplied(state):
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
    if not confirm("Are you sure? Enter 'y' if ok, else <enter>: ", ['y']):
    	return
    
    tap_sha = git_top_of_applied_stack_sha(state)
    # "push" tap_sha to unapplied patches
    state['unapplied_patches'] = \
        [make_patch_dict(tap_sha)] + state['unapplied_patches']
    git_pop_applied_stack()

def move_n_pick(state):
    cp_sha = input("enter SHA1 id of  patch or <enter> if none: ")
    if not cp_sha: return
    if not top_cites_upstream_or_confirmed_dont_care(state):
        print_log("no upstream citation or confirmaticbon of indifference",
                  state)
        return
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        
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
    state['unapplied_patches'] = \
        [make_patch_dict(prq_sha)] + state['unapplied_patches']
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

    patches = import_sha_list_file(sha_file, state)
    state['unapplied_patches'] = patches + state['unapplied_patches']
    save_cp(state)

def update_applied_patches(state):
    print_log("@@update_applied_patches", state)
    state['applied_patch_list'] = git_applied_sha_list(state)
    save_cp(state)
    print_log(state['applied_patch_list'], state)

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
    if not confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    if not confirm("enter 'y' if you're really really sure, else <enter>: ", ['y']):
    	return
    git_cherry_pick_abort()

def cherry_pick_by_sha(state):
    print_log("@@cherry_pick_by_sha", state)
    if not top_cites_upstream_or_confirmed_dont_care(state):
        print_log("no upstream citation or confirmation of indifference",
                  state)
        return
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        
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

def shell_one_liner(state):
    cmd = input("enter shell one liner<enter to cancel>: ")
    (ret, output) = shell_cmd(cmd)
    print_log(output, state)

def test(state):
    add_resolvd_patches_to_all_patches(state)
    
bp_universal_utils = {'prompt' :"universal utils", 'sub-menu' : [
        {'prompt' : 'backup branch', 'action' : backup_branch},
        {'prompt' : 'increment git branch', 'action' : next_branch},
        {'prompt' : 'note to log file', 'action' : log_note},
        {'prompt' : 'save checkpoint', 'action' : checkpoint},
        {'prompt' : 'shell one_liner', 'action': shell_one_liner},
        {'prompt' : 'enter pdb', 'action' : do_pdb},
]}

bp_menu_item_list = [
    #
    # main menu
    #
    {'prompt' : 'start_backport', 'action': start_backport},
    {'prompt' : 'main backport actions', 'sub-menu' : [
        {'prompt' : 'show git status', 'action': git_status},
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'show unapplied patches','action': unapplied_patches},
        {'prompt' : 'apply next patch', 'action':  apply_next_patch},
        {'prompt' : 'build', 'action' : build},
        {'prompt' : 'compare patch to upstream',
         'action' : compare_patch_to_upstream},
        bp_universal_utils,
        ]},
    {'prompt' : 'cherry pick actions', 'sub-menu' : [
        {'prompt' : 'show git status', 'action': git_status},
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'cherry-pick --continue',
         'action': cherry_pick_continue},
        {'prompt' : 'cherry-pick -abort',
         'action': cherry_pick_abort},
        {'prompt' : 'cherry-pick by sha',
         'action': cherry_pick_by_sha},
        bp_universal_utils,
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
        {'prompt': 'show all patches', 'action' : show_all_patches},
        ]
     },
    {'prompt' : 'unresolved symbol actions', 'sub-menu' : [
        {'prompt' : 'short display unresolved syms (unprovided)',
         'action': short_display_unres_symbols_unprovided},
        {'prompt' : 'short display unresolved syms (all)',
         'action': short_display_unres_symbols_all},
        {'prompt' : 'find commits referring unresolved symbols',
         'action' : git_logG},
        {'prompt' : 'show one git log result', 'action': show_one_log_result},
        {'prompt' : 'show git log completions', 'action': show_log_completions},
        {'prompt' : 'set provider(resolve) by index',
         'action' : set_unres_provider_by_ix},
        {'prompt' : 'delete unresolved sym by index',
         'action' : delete_unres_sym_by_ix},
        {'prompt' : 'unresolved syms to patch dict list',
         'action': unresolved_syms_to_patch_dict_list},
        {'prompt' : 'detailed display unresolved sym by index',
         'action': detailed_display_unres_symbol_by_index},
        {'prompt' : 'build and parse', 'action': get_needed_symbols},
        bp_universal_utils,
    ],
     },
    {'prompt' : 'utility actions', 'sub-menu' : [
        {'prompt' : 'patch_info(sha)', 'action' : patch_info},
        {'prompt' : 'launch bash', 'action' : bash},
        {'prompt' : 'increment git branch', 'action' : next_branch},
        {'prompt' : 'update applied patch_list',
         'action' : update_applied_patches},
        {'prompt': 'show_patch_by_sha', 'action' : show_patch_by_sha},
        {'prompt' : 'backup branch', 'action' : backup_branch},
        {'prompt' : 'increment git branch', 'action' : next_branch},
        {'prompt' : 'note to log file', 'action' : log_note},
        {'prompt' : 'save checkpoint', 'action' : checkpoint},
        {'prompt' : 'shell one_liner', 'action': shell_one_liner},
        {'prompt' : 'enter pdb', 'action' : do_pdb},
        ]
     },
    {'prompt' : 'enter pdb', 'action' : do_pdb},
    {'prompt' : 'test', 'action' : test},
    {'prompt': 'show all patches', 'action' : show_all_patches},
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
parser.add_argument('--no-auto-save', default = 'n',
                    help='for examining pickles')
# Parse the command line arguments
args = parser.parse_args()
state = state_init(args)

if args.sha_list:
    import_sha_list_file(state['args'].sha_list, 'set', state)

state = load_pickle_file(args, state)

backport_patches(state, bp_menu_item_list)

