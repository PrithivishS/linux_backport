#!/usr/bin/python3

import git_utils as gu
import print_log as pl
import meta_git as mg
import patch as _patch
import cherry_pick as cp
import persist

def start_backport(state):#: @unclear?, @workflow
    if not gu.git_repo_is_clean():
        pl.print_log("repo is not clean. bailing out", state)
        return
    if state['backport_in_progress']:
        print("OOPS: backport already in progress")
        return

    state['backport_in_progress'] = True
    gu.next_branch(state)
    gu.git_reset_hard(state['first_commit'], state)

def restart_backport(state):#: @unclear?, @workflow
    if mg.active_cherry_pick_sha(state):
        gu.git_cherry_pick_abort()

    state['backport_in_progress'] = False
    gu.next_branch(state)
    start_backport(state)

def cherry_pick_next_patch(state):
    pl.print_log("@@apply_next_patch", state)
    if not gu.git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    L = [p for p in state['all_patches'] if not p['downstream']]
    if len(L) == 0:
        pl.print_log("THERE ARE NO PATCHES TO APPLY", state)
        return
    patch = L[0]

    _patch.print_dict("@@ cherry picking :", patch, state)
    gu.git_cherry_pick(patch['sha1'])
    
    if gu.git_repo_is_clean():
        cp.cherry_pick_complete(state, patch)
    else:
        cp.show_stuff_for_conflict_resolution(state)
        if cp.try_to_reuse_old_conflict_resolution(patch, state):
            cp.cherry_pick_complete(state, patch)
    persist.save_cp(state)

def cherry_pick_continue(state):
    cherry_pick_sha = mg.active_cherry_pick_sha(state)
    if not cherry_pick_sha:
        pl.print_log("No cherry-pick in progress. can't cherry-pick --continue",
                  state)
        return
    patch = state['sha_to_patch'][cherry_pick_sha]
    pl.print_log("@@cherry_pick_continue", state)
    gu.git_cherry_pick_continue()
    if gu.git_repo_is_clean():
        downstream_sha = gu.git_top_of_applied_stack_sha(state)
        patch['downstream'] = downstream_sha
        state['downstream_sha_to_patch'][downstream_sha] = patch
        plh = state['patch_list_history']
        plh.append(list())
        plhe = plh[-1]
        for patch in state['all_patches']:
            plhe.append(patch)

def both_mod_commits(state):#: @workflow
    (cp_patch,
     both_mod_files,
     mod_files) = cp.parse_cherry_pick_conflict(state)

    if not cp_patch:
        return

    for file in both_mod_files:
        add_commits_touching_file_to_all_patches(cp_patch, file, state)

def cherry_pick_abort(state):#: @workflow
    pl.print_log("@@cherry_pick_abort", state)
    if gu.git_repo_is_clean():
        pl.print_log("repo is clean. can't cherry-pick --abort", state)
        return
    if not ui.confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    if not ui.confirm("enter 'y' if you're really really sure, else <enter>: ", ['y']):
    	return
    gu.git_cherry_pick_abort()

