#!/usr/bin/python3

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

def git_logG_simple(state):
    # https://realpython.com/intro-to-python-threading
    state['git_log_completed'] = list()
    print_log("@@git_logG_simple", state)
    line_fn = lambda line, state: print_log(get_sha_info(line, ''), state)

    (search_type, pattern) = input("\nenter 'S' or 'G', <pattern> <enter to return>: ").split(' ')
    if not pattern: return
                    
    if search_type != 'S' and search_type != 'G':
        print("oops")
        return

    min = git_log_tag(state, 'min')
    max = git_log_tag(state, 'max')
    print("launching asynchronous git log task")
    thrd = threading.Thread(target=git_log_search,
                            args = (search_type, pattern, min, max, line_fn,
                                    state),
                            daemon=True)
    thrd.start()
    print_log("git_logG_syms/exit", state)
    

def git_logG_syms(state):
    # https://realpython.com/intro-to-python-threading
    
#   threads = []
    state['git_log_completed'] = list()
    print_log("@@git_logG_syms", state)
    line_fn = lambda line, state: print_log(get_sha_info(line, ''), state)
    search_type = input("\nenter 'S' or 'G '<enter to return>: ")
    if search_type != 'S' and search_type != 'G':
        print("oops")
        return
    
    syms = state['unresolved_syms']
    needy_syms = [ sym for sym in syms if not sym['provided-by']]

    for sym in needy_syms:
        #G v6.0 v6.2
        print("git_log_search for: %s initiated" % (sym['tag']))
        min = git_log_tag(state, 'min')
        max = git_log_tag(state, 'max')
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
        print_log("git_logG_syms/exit", state)

def show_log_completions(state):
    try:
        print(state['git_log_completed'])
    except:
        return

