#!/usr/bin/python3

import git_utils as gu
import print_log as pl
import meta_git as mg

def start_backport(state):#: @unclear?, @workflow
    if not gu.git_repo_is_clean():
        pl.print_log("repo is not clean. bailing out", state)
        return
    if state['backport_in_progress']:
        print("OOPS: backport already in progress")
        return

    state['backport_in_progress'] = True
    gu.next_branch(state)
    git_reset_hard(state['first_commit'], state)

def restart_backport(state):#: @unclear?, @workflow
    if active_cherry_pick_sha(state):
        git_cherry_pick_abort()

    state['backport_in_progress'] = False
    gu.next_branch(state)
    gu.git_reset_hard(state['first_commit'], state)
    start_backport(state)

