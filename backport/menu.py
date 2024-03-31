import  bp_utils as bpu
import git_utils as git

bp_menu_item_list = [
    #
    # main menu
    #
    {'prompt' : 'show git status', 'action': bpu.do_git_status},
    {'prompt' : 'short_git_log', 'action': bpu.short_git_log},
    {'prompt' : 'show unapplied patches','action': bpu.unapplied_patches},
    {'prompt': 'show all patches', 'action' : bpu.show_all_patches},
    {'prompt' : 'cherry pick next patch', 'action':  bpu.apply_next_patch},
    {'prompt' : 'patch_info(sha)', 'action' : bpu.patch_info},
    {'prompt' : 'find commits referring to pattern',
     'action' : git.git_logG_simple},
    {'prompt' : 'find commits touching "both modified" files',
     'action' : bpu.both_mod_commits},
    {'prompt' : 'add patch by sha',
     'action' : bpu.add_to_all_patches_by_sha},
    {'prompt' : 'show one git log result', 'action': bpu.show_one_log_result},
    {'prompt' : 'delete one git log result',
     'action': bpu.delete_one_log_result},
    {'prompt' : 'build', 'action' : bpu.build},
    {'prompt' : 'cherry-pick --continue',
     'action': bpu.cherry_pick_continue},#@
    {'prompt' : 'cherry-pick -abort', 'action': bpu.cherry_pick_abort},
    {'prompt' : 'compare patch to upstream',
     'action' : bpu.compare_patch_to_upstream},
    {'prompt' : 'show one git log result', 'action': bpu.show_one_log_result},
    {'prompt' : 'show git log completions', 'action': git.show_log_completions},
    {'prompt' : 'add sha list to all patches',
     'action':  bpu.add_sha_list_to_all_patches},
    {'prompt' : 'utility actions', 'sub-menu' : [
        {'prompt' : 'backup branch', 'action' : bpu.backup_branch},
        {'prompt' : 'increment git branch', 'action' : git.next_branch},
        {'prompt' : 'note to log file', 'action' : bpu.log_note},
        {'prompt' : 'save checkpoint', 'action' : bpu.checkpoint},
        {'prompt' : 'shell one_liner', 'action': bpu.shell_one_liner},
        {'prompt' : 'enter pdb', 'action' : bpu.do_pdb},
        {'prompt' : 'launch bash', 'action' : bpu.bash},
        {'prompt': 'show_patch_by_sha', 'action' : bpu.show_patch_by_sha},
        {'prompt' : 'start_backport', 'action': bpu.start_backport},
        {'prompt' : 'REstart_backport', 'action': bpu.restart_backport},
        ]
     },
     {'prompt' : 'experimental actions', 'sub-menu' : [
        {'prompt' : 'short display unresolved syms (unprovided)',
         'action': bpu.short_display_unres_symbols_unprovided},
        {'prompt' : 'short display unresolved syms (all)',
         'action': bpu.short_display_unres_symbols_all},
        {'prompt' : 'find commits referring unresolved symbols',
         'action' : git.git_logG_syms},
        {'prompt' : 'set provider(resolve) by index',
         'action' : bpu.set_unres_provider_by_ix},
        {'prompt' : 'delete unresolved sym by index',
         'action' : bpu.delete_unres_sym_by_ix},
        {'prompt' : 'unresolved syms to patch dict list',
         'action': bpu.unresolved_syms_to_patch_dict_list},
        {'prompt' : 'detailed display unresolved sym by index',
         'action': bpu.detailed_display_unres_symbol_by_index},
        {'prompt' : 'build and parse', 'action': bpu.get_needed_symbols},
     ]},
]
