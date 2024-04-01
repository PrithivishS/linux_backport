import git_utils

def show_sha_info(sha):
    if not sha: return ""
    subj = git_utils.git_get_subject(sha)
    tag = git_utils.git_first_containing_tag(sha)
    tag_date = git_utils.git_get_commit_date(tag)
    s  = "%s, %s, %s, %s" % (sha, subj, tag, tag_date)
    return s
                  
def prompted_show_sha_info(state):
    sha = input("enter sha1(return to exit): ")
    if not sha: return None
    pl.print_log(show_sha_info(sha), state)

                  
def get_sha_info(sha, subj):
    if not subj:
        subj = git_utils.git_get_subject(sha)

    tag = git_utils.git_first_containing_tag(sha)
    tag_date = git_utils.git_get_commit_date(tag)
    tmp = "%s, %s, %s, %s" % (sha, subj, tag, tag_date)
    return tmp
    
def import_sha_list_file(path, state):
    pl.print_log("@@import_sha_list_file(%s...)" % (path), state)

    patch_list = [make_patch_dict(state, l)
                  for l in open(path,"r")]
    return patch_list

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
    
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
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

