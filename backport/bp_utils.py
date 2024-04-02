#!/usr/bin/python3

import pdb
import pickle
from git_utils import *
import git_utils as git
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
import cherry_pick as cp
    
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


def do_pdb(state): #: @util
    pl.print_log("@@pdb", state)
    pdb.set_trace()

def checkpoint(state): #: @util
    pl.print_log("@@checkpoint", state)
    save_cp(state)

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

def shell_one_liner(state): 
    cmd = input("enter shell one liner<enter to cancel>: ")
    (ret, output) = su.shell_cmd(cmd)
    pl.print_log(output, state)

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
