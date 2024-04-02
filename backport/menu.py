#!/usr/bin/python3

import bp_utils as bu
import git_utils as git
import meta_git as mg
import patch as patch
import unres_syms as us
import shell_util as su
import all_patches as ap
import workflow as wf


bp_menu_item_list = [
    #
    # main menu
    #
    {'prompt' : 'show git status', 'action': bu.do_git_status},
    {'prompt' : 'short_git_log', 'action': bu.short_git_log},
    {'prompt' : 'show unapplied patches','action': ap.unapplied_patches},
    {'prompt': 'show all patches', 'action' : ap.show_all_patches},
    {'prompt' : 'cherry pick next patch',
     'action':  wf.cherry_pick_next_patch},
    {'prompt' : 'patch_info(sha)', 'action' : bu.patch_info},
    {'prompt' : 'find commits referring to pattern',
     'action' : mg.git_logG_simple},
    {'prompt' : 'find commits touching "both modified" files',
     'action' : wf.both_mod_commits},
    {'prompt' : 'add patch by sha',
     'action' : ap.add_to_all_patches_by_sha},
    {'prompt' : 'show one git log result', 'action': bu.show_one_log_result},
    {'prompt' : 'delete one git log result',
     'action': bu.delete_one_log_result},
    {'prompt' : 'build', 'action' : su.build},
    {'prompt' : 'cherry-pick --continue',
     'action': wf.cherry_pick_continue},
    {'prompt' : 'cherry-pick -abort', 'action': wf.cherry_pick_abort},
    {'prompt' : 'compare patch to upstream',
     'action' : patch.compare_patch_to_downstream},
    {'prompt' : 'show one git log result', 'action': bu.show_one_log_result},
    {'prompt' : 'show git log completions', 'action': git.show_log_completions},
    {'prompt' : 'add sha list to all patches',
     'action':  bu.add_sha_list_to_all_patches},
    {'prompt' : 'utility actions', 'sub-menu' : [
        {'prompt' : 'backup branch', 'action' : bu.backup_branch},
        {'prompt' : 'increment git branch', 'action' : git.next_branch},
        {'prompt' : 'note to log file', 'action' : bu.log_note},
        {'prompt' : 'save checkpoint', 'action' : bu.checkpoint},
        {'prompt' : 'shell one_liner', 'action': bu.shell_one_liner},
        {'prompt' : 'enter pdb', 'action' : bu.do_pdb},
        {'prompt' : 'launch bash', 'action' : bu.bash},
        {'prompt': 'show_patch_by_sha', 'action' : git.show_patch_by_sha},
        {'prompt' : 'start_backport', 'action': wf.start_backport},
        {'prompt' : 'REstart_backport', 'action': wf.restart_backport},
        ]
     },
     {'prompt' : 'experimental actions', 'sub-menu' : [
        {'prompt' : 'short display unresolved syms (unprovided)',
         'action': us.short_display_unres_symbols_unprovided},
        {'prompt' : 'short display unresolved syms (all)',
         'action': us.short_display_unres_symbols_all},
        {'prompt' : 'find commits referring unresolved symbols',
         'action' : mg.git_logG_syms},
        {'prompt' : 'set provider(resolve) by index',
         'action' : us.set_unres_provider_by_ix},
        {'prompt' : 'delete unresolved sym by index',
         'action' : us.delete_unres_sym_by_ix},
        {'prompt' : 'unresolved syms to patch dict list',
         'action': us.unresolved_syms_to_patch_dict_list},
        {'prompt' : 'detailed display unresolved sym by index',
         'action': us.detailed_display_unres_symbol_by_index},
        {'prompt' : 'build and parse', 'action': us.get_needed_symbols},
     ]},
]
