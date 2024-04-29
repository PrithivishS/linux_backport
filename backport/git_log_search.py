#!/usr/bin/python3

import print_log as pl
import patch
import git_utils as gu
import shell_util as su
import pdb
import meta_git as mg

def get_async_result_key_by_index(state): #: workflow
    if 'async_result' not in state: return None
    keys = state['async_result'].keys()
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
    
def search_commit_for_pattern(type, pattern, sha, state):
    cmd = "git show %s | grep %s" % (sha, pattern)
    (ret, out) = su.shell_cmd(cmd)
    return out

def show_one_async_result(state): #: workflow
    if 'async_result' not in state: return
    key = get_async_result_key_by_index(state)
    (type, pattern, min_tag, max_tage)  = key.split(',')
    if not key: return
    sha_str = state['async_result'][key]
    pl.print_log("==== %s ====" % (key), state)

    for sha in [sha.lstrip().rstrip() for sha in sha_str.split('\n')]:
        _d = patch.make_patch_dict(state,sha)
        pl.print_log("== %s ==" % (patch.sha_to_patch_string(state, sha)),
                     state)
        tmp = search_commit_for_pattern(type, pattern, sha, state)
        out = gu.clip_long_output(tmp, state).rstrip()
        pl.print_log(out, state)

def delete_one_async_result(state): #: workflow
    key = get_async_result_key_by_index(state)
    if not key: return
    
    pl.print_log("==== %s ====" % (key), state)
    
    del state['async_result'][key]

# git log is capable of much more than this function shows
#
def git_log_search(search_type, pattern, tag1, tag2, state):
    cmd =  "git log -%s%s" % (search_type, pattern)
    cmd += " --pretty=tformat:\'%<(10) %h\'"
    cmd += " %s..%s" % (tag1, tag2)
    key = search_type + "," + pattern + "," + tag1 +"," + tag2
    su.async_shell_cmd(cmd, key, state)

def git_logG_simple(state):
    try:
        (search_type, pattern) = input("\nenter 'S' or 'G', <pattern> <enter to return>: ").split(' ')
    except:
        pl.print_log(":bad input")
        return

    if not pattern: return
                    
    if search_type != 'S' and search_type != 'G':
        print("oops")
        return

    min = gu.git_log_tag(state, 'min')
    max = gu.git_log_tag(state, 'max')
    print("launching asynchronous git log task")
    git_log_search(search_type, pattern, min, max, state)

def git_logG_syms(state):
    pl.print_log("@@git_logG_syms", state)
    search_type = input("\nenter 'S' or 'G '<enter to return>: ")
    if search_type != 'S' and search_type != 'G':
        print("oops")
        return
    
    syms = state['unresolved_syms']
    needy_syms = [ sym for sym in syms if not sym['provided-by']]

    for sym in needy_syms:
        print("git_log_search for: %s initiated" % (sym['tag']))
        min = gu.git_log_tag(state, 'min')
        max = gu.git_log_tag(state, 'max')
        git_log_search(search_type, sym['tag'], min, max, state)


