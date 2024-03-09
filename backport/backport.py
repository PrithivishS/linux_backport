#!/usr/bin/python3

import argparse
from bp_utils import *

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
     {'prompt' : 'main backport actions', 'sub-menu' : [
        {'prompt' : 'show git status', 'action': do_git_status},
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'show unapplied patches','action': unapplied_patches},
        {'prompt' : 'apply next patch', 'action':  apply_next_patch},
        {'prompt' : 'build', 'action' : build},
        {'prompt' : 'compare patch to upstream',
         'action' : compare_patch_to_upstream},
        bp_universal_utils,
        ]},
    {'prompt' : 'cherry pick actions', 'sub-menu' : [
        {'prompt' : 'show git status', 'action': do_git_status},
        {'prompt' : 'short_git_log', 'action': short_git_log},
        {'prompt' : 'cherry-pick --continue',
         'action': cherry_pick_continue},
        {'prompt' : 'cherry-pick -abort',
         'action': cherry_pick_abort},
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
        {'prompt' : 'start_backport', 'action': start_backport},
        {'prompt' : 'enter pdb', 'action' : do_pdb},
        ]
     },
    {'prompt' : 'obsolete, should not be used', 'sub-menu' : [
        {'prompt' : 'cherry-pick by sha',
         'action': cherry_pick_by_sha},
    ],
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

