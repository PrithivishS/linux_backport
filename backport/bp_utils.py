#!/usr/bin/python3

import pdb
import pickle
from git_utils import *
import git_utils
from datetime import datetime
import select
import shutil
import shlex
import tempfile
import difflib
from packaging import version
import print_log as pl
import state_access
import persist
import patch
import menu_util as mu
import meta_git as mg
import shell_util as su
    
def prompt_to_set_or_alter_dict_val(key, d): #: core, @io, @ui, @state, @persist
    # if no saved value for key
    #	prompt for it
    #	save to d
    # else 
    #	show saved value, ask if they want to change
    #	save in d if changed
    if not key in d:
        cmd = input("enter %s or <enter> to skip: " % (key))
        if cmd:
            d[key] = cmd
    else:
        cmd = d[key]
        print("build command is: " + cmd)
        tmp = input("enter %s to change or <enter> to use existing: "
                    % (key))
        if tmp:
            d[key] = tmp

def backport_patches(state, menu_item_list): #: @core, @MAIN, @workflow
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pl.print_log("Startup: Current Time = %s" %(current_date_time), state)

    mu.do_menu_choice(menu_item_list, state)
           
def uniqify_list(L): #: @core, @generic
    ret = list()
    tmp = dict()
    for elt in L:
        if elt in ret:
            continue
        ret.append(elt)
    return ret
    
def uniqify_dict_list(dict_list, key_list): #: @core, @generic
    print("FIXME:BUG: defining 2 fns uniqify_dict_list 1st def is lost")
    ret = list()
    tmp = dict()
    for _dict in dict_list:
        key_str = ""
        for key in key_list:
            key_str += _dict[key]
        if key in tmp:
            continue
        ret.append(_dict)
    return ret

#@@@
def parse_cherry_pick_conflict(state): #: @meta_git
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

def show_stuff_for_conflict_resolution(state):#: @workflow
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
        generate_conflict_resolution_files(cp_sha, file, state)

def cherry_pick_by_sha(state, cp_sha):#: @meta_git
    pl.print_log("@@cherry_pick_by_sha", state)
    pdb.set_trace()
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
    save_cp(state)
    
def cherry_pick_complete(state, patch):#: @meta_git
    patch['prev_downstream'] = patch['downstream']
    patch['downstream'] = git_top_of_applied_stack_sha(state)
    state['downstream_sha_to_patch'][patch['downstream']] = patch
    build(state)
    
def try_to_reuse_old_conflict_resolution(patch, state): #: @workflow
    if not mg.active_cherry_pick_sha(state):
        # we can't use a prev resolution if there is no conflict
        # and we can't have a conflict if not in cherry-pick
        return False
    
    patch['prev_conflicts'] = patch['conflicts']
    patch['conflicts'] = git_get_conflicts()

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
        
def apply_next_patch(state):#: @workflow, @rename:cherry_pick_next_patch
    pl.print_log("@@apply_next_patch", state)
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    L = [p for p in state['all_patches'] if not p['downstream']]
    if len(L) == 0:
        pl.print_log("THERE ARE NO PATCHES TO APPLY", state)
        return
    patch = L[0]

    patch.print_dict("@@ cherry picking :", patch, state)
    git_cherry_pick(patch['sha1'])
    
    if git_repo_is_clean():
        cherry_pick_complete(state, patch)
    else:
        show_stuff_for_conflict_resolution(state)
        if try_to_reuse_old_conflict_resolution(patch, state):
            cherry_pick_complete(state, patch)
    save_cp(state)

def do_pdb(state): #: @util
    pl.print_log("@@pdb", state)
    pdb.set_trace()

def checkpoint(state): #: @util
    pl.print_log("@@checkpoint", state)
    save_cp(state)

def pop_branch_tos(state): #: @obsolete?
    pl.print_log("@@do_pop_branch_tos", state)
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    git_utils.git_pop_branch_tos_stack()
    short_git_log(state)

def short_git_log(state): #: @meta_git
    pl.print_log("@@how_short_git_log", state)
    git_short_log('%<(10) %h  %<(12) %an : %s', state)

def bash(state): #: @util
    pl.print_log("@@bash", state)
    subprocess.run(['bash'])

def log_note(state): #: @util
    pl.print_log("@@log_note", state)
    s = input("enter text to be appended to the log: ")
    pl.print_log(s, state)

def patch_info(state): #: @workflow
    pl.print_log("@@patch_info", state)
    mg.prompted_show_sha_info(state)

def backup_branch(state): #: @workflow
    pl.print_log("@@backup_branch", state)
    line_fn = lambda line, state: pl.print_log(line, state)
    prompt_to_set_or_alter_dict_val('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    cmd = "git " + ' '.join(state['branch_backup_cmd'].split(' ')[1:])
    out = su.shell_cmd(cmd)
    pl.print_log(out, state)

def unapply_branch_tos(state): #: @obsolete
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    if not ui.confirm("Are you sure? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

    sha = git_top_of_applied_stack_sha(state)
    patch = state['downstream_sha_to_patch']
    downstream_sha = patch['downstream']
    patch['downstream'] = None
    del state['downstream_sha_to_patch'][downstream_sha]

    git_utils.git_pop_branch_tos()
    del state['downstream_sha_to_patch'][downstream_sha]

    return

def add_sha_list_to_all_patches(state): #: @workflow, @patch_list
    pl.print_log("@@add_sha_list_to_all_patches", state)
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        return
    if not ui.confirm("Are you sure you don't need to pop top applied patch? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

     # get the name of the sha file
    print("enter the path of a file containing one sha per line <enter> if none")
    sha_file = input("sha_file: ")
    if not sha_file: return

    patches = import_sha_list_file(sha_file, state)
    for patch in import_sha_list_file(sha_file, state):
        add_to_all_patches(patch, state)
    after_add_to_all_patches(state)

def cherry_pick_continue(state):#: @workflow
    cherry_pick_sha = mg.active_cherry_pick_sha(state)
    if not cherry_pick_sha:
        pl.print_log("No cherry-pick in progress. can't cherry-pick --continue",
                  state)
        return
    patch = state['sha_to_patch'][cherry_pick_sha]
    pl.print_log("@@cherry_pick_continue", state)
    git_cherry_pick_continue()
    if git_repo_is_clean():
        downstream_sha = git_top_of_applied_stack_sha(state)
        patch['downstream'] = downstream_sha
        state['downstream_sha_to_patch'][downstream_sha] = patch
        plh = state['patch_list_history']
        plh.append(list())
        plhe = plh[-1]
        for patch in state['all_patches']:
            plhe.append(patch)

def cherry_pick_abort(state):#: @workflow
    pl.print_log("@@cherry_pick_abort", state)
    if git_repo_is_clean():
        pl.print_log("repo is clean. can't cherry-pick --abort", state)
        return
    if not ui.confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    if not ui.confirm("enter 'y' if you're really really sure, else <enter>: ", ['y']):
    	return
    git_cherry_pick_abort()

def show_top_unapp(state): #: obsolete?
    patch.print_list("", unapplied_patches(state)[:1], state)

def show_patch_by_sha(state): #: @git
    sha = input("enter sha of patch to be shown: ")
    (ret, output) = su.shell_cmd("git show " + sha)
    pl.print_log(output, state)

def shell_one_liner(state): #: @util
    cmd = input("enter shell one liner<enter to cancel>: ")
    (ret, output) = su.shell_cmd(cmd)
    pl.print_log(output, state)

def git_status_log(state): #: @obsolete
    s = git_utils.git_status(state)
    
def do_git_status(state): #: @meta_git
    s = git_status()
    pl.print_log(s, state)

def get_log_result_key_by_index(state): #: workflow
    keys = state['git_log_results'].keys()
    keys_l = list(keys)
    
    for (key, i) in zip(keys, range(len(keys))):
        print(str(i) + ":" + key)
        
    ix = input("enter index <enter to return>: ")
    if not ix:
        return
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if i > len(keys) or ix < 0:
        return
          
    key = keys_l[ix]
    return key
    
def show_one_log_result(state): #: workflow
    key = get_log_result_key_by_index(state)
    if not key: return
    
    pl.print_log("==== %s ====" % (key), state)
    
    sha_out_list = state['git_log_results'][key]
    for sha in sha_out_list.keys():
        _d = make_patch_dict(state,sha)
        pl.print_log("== %s ==" % (sha_to_patch_string(state, sha)), state)
        out = clip_long_output(sha_out_list[sha], state)
        pl.print_log(out, state)

def delete_one_log_result(state): #: workflow
    key = get_log_result_key_by_index(state)
    if not key: return
    
    pl.print_log("==== %s ====" % (key), state)
    
    del state['git_log_results'][key]

    
def hackery(state):#: obsolete
    for patch in state['all_patches']:
        patch['conflicts'] = None
        patch['prev_conflicts'] = None
        patch['downstream'] = None
        patch['prev_downstream'] = None
        
def both_mod_commits(state):#: @workflow
    (cp_patch,
     both_mod_files,
     mod_files) = parse_cherry_pick_conflict(state)

    if not cp_patch:
        return

    for file in both_mod_files:
        add_commits_touching_file_to_all_patches(cp_patch, file, state)
