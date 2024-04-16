#!/usr/bin/python3

import print_log as pl
import patch
import git_utils as gu
import threading
import shell_util as su
import pdb
import meta_git as mg

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
        _d = patch.make_patch_dict(state,sha)
        pl.print_log("== %s ==" % (sha_to_patch_string(state, sha)), state)
        out = clip_long_output(sha_out_list[sha], state)
        pl.print_log(out, state)

def delete_one_log_result(state): #: workflow
    key = get_log_result_key_by_index(state)
    if not key: return
    
    pl.print_log("==== %s ====" % (key), state)
    
    del state['git_log_results'][key]

def search_commit_for_pattern(search_type, pattern, tag1, tag2, line_fn, state,
                              sha):
    debug_print_log("search_commit_for_pattern.1", state)
    key = search_type + "," + pattern + "," + tag1 +"," + tag2
    cmd = "git show %s | grep %s" % (sha, pattern)
    _pdb = pdb.Pdb();_pdb.set_trace()
    debug_print_log("search_commit_for_pattern.2", state)
    (ret, out) = su.shell_cmd(cmd)

    debug_print_log("search_commit_for_pattern.3", state)

    if 'git_log_results' not in state:
        state['git_log_results'] = dict()

    if key not in state['git_log_results']:
        state['git_log_results'][key] = dict()

    if sha in state['git_log_results'][key]:
        print("uh-oh")
    else:
        state['git_log_results'][key][sha] = out

# git log is capable of much more than this function shows
#
def git_log_search(search_type, pattern, tag1, tag2, line_fn, state):
    pl.debug_print_log("git_log_search.1", state)
    cmd =  "git log -%s%s" % (search_type, pattern)
    cmd += " --pretty=tformat:\'%<(10) %h\'"
    cmd += " %s..%s" % (tag1, tag2)
    pl.debug_print_log("git_log_search.1:cmd", state)
    (ret, out) = su.shell_cmd(cmd)
    _pdb = pdb.Pdb();_pdb.set_trace()
    out = [x.lstrip() for x in out.rstrip("\n").split("\n")]

    for sha in out:
        search_commit_for_pattern(search_type, pattern, tag1, tag2, line_fn,
                                  state, sha)
    key = search_type + "," + pattern + "," + tag1 +"," + tag2
    pl.debug_print_log("git_log_search.2", state)
    state['git_log_completed'].append(key)
    return ret
    
def git_logG_simple_v2(state):
    pass

def git_logG_simple(state):
    pl.debug_print_log("git_logG_simple.1", state)
    # https://realpython.com/intro-to-python-threading
    pl.debug_print_log("git_logG_simple.2", state)
    state['git_log_completed'] = list()
    pl.print_log("@@git_logG_simple.2", state)
    line_fn = lambda line, state: pl.print_log(mg.get_sha_info(line, ''), state)

    (search_type, pattern) = input("\nenter 'S' or 'G', <pattern> <enter to return>: ").split(' ')
    pl.print_log("@@git_logG_simple.3", state)
    if not pattern: return
                    
    pl.print_log("@@git_logG_simple.4", state)
    if search_type != 'S' and search_type != 'G':
        print("oops")
        return
    pl.print_log("@@git_logG_simple.5", state)

    min = gu.git_log_tag(state, 'min')
    max = gu.git_log_tag(state, 'max')
    print("launching asynchronous git log task")
    pdb.set_trace()
    pl.print_log("@@git_logG_simple: launch async task", state)
    thrd = threading.Thread(target=git_log_search,
                            args = (search_type, pattern, min, max, line_fn,
                                    state),
                            daemon=True)
    thrd.start()
    pl.print_log("git_logG_syms/exit", state)
    

def git_logG_syms(state):
    # https://realpython.com/intro-to-python-threading
    
#   threads = []
    pl.debug_print_log("git_logG_syms", state)
    pl.print_log("@@git_logG_syms", state)
    state['git_log_completed'] = list()
    pl.print_log("@@git_logG_syms", state)
    line_fn = lambda line, state: pl.print_log(mg.get_sha_info(line, ''), state)
    search_type = input("\nenter 'S' or 'G '<enter to return>: ")
    if search_type != 'S' and search_type != 'G':
        print("oops")
        return
    
    syms = state['unresolved_syms']
    needy_syms = [ sym for sym in syms if not sym['provided-by']]

    for sym in needy_syms:
        #G v6.0 v6.2
        print("git_log_search for: %s initiated" % (sym['tag']))
        min = gu.git_log_tag(state, 'min')
        max = gu.git_log_tag(state, 'max')
        print("launching asynchronous git log task")
        thrd = threading.Thread(target=git_log_search,
                                args = (search_type, sym['tag'], min, max,
                                        line_fn, state),
                                daemon=True)

        #       threads.append(thrd)
        thrd.start()
#        if threads:
#            for thrd in threads:
#                thrd.join()
        pl.print_log("git_logG_syms/exit", state)

def show_log_completions(state):
    try:
        print(state['git_log_completed'])
    except:
        return

