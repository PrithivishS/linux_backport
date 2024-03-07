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

def unapplied_patches(state):
    print_log("@@how_unapplied_patches", state)
    L = [p for p in state['all_patches'] if not p['downstream']]
    print_patch_list("", L, state)
    return L

def do_pdb(state):
    print_log("@@pdb", state)
    pdb.set_trace()

def checkpoint(state):
    print_log("@@checkpoint", state)
    save_cp(state)

def pop_branch_tos(state):    
    print_log("@@do_pop_branch_tos", state)
    if not top_cites_upstream_or_confirmed_dont_care(state):
        print_log("no upstream citation or confirmation of indifference",
                  state)
        return
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        
    git_utils.git_pop_branch_tos_stack()
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

def unapply_branch_tos(state):
    if not git_repo_is_clean():
        print_log("git status not clean. no changes made", state)
        
    if not confirm("Are you sure? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

    sha = git_top_of_applied_stack_sha(state)
    patch = state['applied_sha_to_patch']
    downstream_sha = patch['downstream']
    patch['downstream'] = None
    del state['applied_sha_to_patch'][downstream_sha]

    git_utils.git_pop_branch_tos()
    del state['downstream_sha_to_patch'][downstream_sha]

    return

def add_sha_list_to_all_patches(state):
    print_log("@@add_sha_list_to_all_patches", state)
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
    for patch in import_sha_list_file(sha_file, state):
        add_to_all_patches(patch, state)

def cherry_pick_continue(state):
    if git_repo_is_clean():
        print_log("repo is clean. can't cherry-pick --continue")
        return
    print_log("@@cherry_pick_continue", state)
    git_cherry_pick_continue()
    if git_repo_is_clean():
        patch['downstream'] = git_top_of_applied_stack_sha(state)
        state['applied_sha_to_patch'][patch['downstream']] = patch
        plh = state['patch_list_history']
        plh.append(list())
        plhe = plh[-1]
        for patch in state['all_patches']:
            plhe.append(patch)

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

def show_top_unapp(state):
    print_patch_list("", unapplied_patches(state)[:1])

def show_patch_by_sha(state):
    sha = input("enter sha of patch to be shown: ")
    (ret, output) = shell_cmd("git show " + sha)
    print_log(output, state)

def shell_one_liner(state):
    cmd = input("enter shell one liner<enter to cancel>: ")
    (ret, output) = shell_cmd(cmd)
    print_log(output, state)

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
        {'prompt' : 'add patch by sha',
         'action' : add_to_all_patches_by_sha},
        bp_universal_utils,
    ]},
    {'prompt' : 'patch stack actions', 'sub-menu' : [
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'show unapplied patches','action': unapplied_patches},
        {'prompt' : 'unapply branch tos',
         'action':  unapply_branch_tos},
        {'prompt' : 'add sha list to all patches',
         'action':  add_sha_list_to_all_patches},
        {'prompt': 'pop cur branch top of stack', 'action' : pop_branch_tos},
        {'prompt' : 'show top unapplied patch','action': show_top_unapp},
        {'prompt': 'show all patches', 'action' : show_all_patches},
        {'prompt' : 'add patch by sha',
         'action' : add_to_all_patches_by_sha},
        bp_universal_utils,
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

