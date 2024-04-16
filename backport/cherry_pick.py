#!/usr/bin/python3

import git_utils as gu
import print_log as pl
import meta_git as mg
import shell_util as su
import patch
import persist

def parse_cherry_pick_conflict(state):
    cp_sha = mg.active_cherry_pick_sha(state)
    if not cp_sha:
        pl.print_log("no active cherry-pick", state)
        return (None, None, None)
         
    cp_patch = state['sha_to_patch'][cp_sha]        

    # parse git status --porcelain
    (ret, porcelain_status) = su.shell_cmd("git status --porcelain")
    mod_files = []
    both_mod_files = []
    for line in porcelain_status.split("\n")[: -1]:
        (code, file) = [x for x in line.split(' ') if not x == '']
        if code == 'M': mod_files.append(file)
        if code == 'UU': both_mod_files.append(file)

    return (cp_patch, both_mod_files, mod_files)

def show_stuff_for_conflict_resolution(state):
    (cp_patch,
     both_mod_files,
     mod_files) = parse_cherry_pick_conflict(state)

    if not cp_patch:
        return
    
    cp_sha = cp_patch['sha1']
    
    # clean tmp dir
    su.shell_cmd("mkdir -p " + state['cherry_pick_files'] + "/" + cp_sha)
    
    # emit patch to temp dir
    cmd = "git show %s > %s/%s/patch" % (cp_sha,
                                         state['cherry_pick_files'],
                                         cp_sha)
    su.shell_cmd(cmd)
    
    # emit both_mod files to "both_mod.".filename
    for file in both_mod_files:
        patch.generate_conflict_resolution_files(cp_sha, file, state)

def cherry_pick_by_sha(state, cp_sha):
    pl.print_log("@@cherry_pick_by_sha", state)
    pdb.set_trace()
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
    persist.save_cp(state)
    
def cherry_pick_complete(state, patch):
    patch['prev_downstream'] = patch['downstream']
    patch['downstream'] = git_top_of_applied_stack_sha(state)
    state['downstream_sha_to_patch'][patch['downstream']] = patch
    build(state)
    
def try_to_reuse_old_conflict_resolution(patch, state):
    if not mg.active_cherry_pick_sha(state):
        # we can't use a prev resolution if there is no conflict
        # and we can't have a conflict if not in cherry-pick
        return False
    
    patch['prev_conflicts'] = patch['conflicts']
    patch['conflicts'] = gu.git_get_conflicts()

    if (patch['prev_downstream'] and
        patch['conflicts'] == patch['prev_conflicts']):
        pdb.set_trace() #FIXME
        # abort current cherry pick
        git_cherry_pick_abort()
        # cherry-pick prev downstream
        cherry_pick_by_sha(patch['prev_downstream'])
                           
        if git_repo_is_clean():
            return True
        else:
            return False
    else:
        return False # can't use old resolution
        
