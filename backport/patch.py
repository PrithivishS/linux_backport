import print_log as pl

def status(patch, state):
    if patch['downstream']: return 'applied'
    if patch['sha1'] == active_cherry_pick_sha(state):
        return "cherry-pick active"
    return "unapplied"

def to_string(msg, patch, state):
    s = "%s, %s, %s, %s, %s, %s" % (
        msg, patch['sha1'], patch['subject'], patch['tag'],
              patch['tag_date'], status(patch, state))
    return s

def print_dict(msg, patch, state):
    s = to_string(msg, patch, state)
    pl.print_log(s, state)

def make_patch_dict(state, sha1):
    d = dict()
    d['sha1'] = sha1.lstrip().rstrip()
    d['sha1'] = d['sha1'][:12]
    d['done'] = False
    d['pre_reqs'] = list()
    d['is_pre_req'] = False
    #why is it suddenly needed to prefix the "git_utils." bit?
    d['subject'] = git_utils.git_get_subject(sha1)
    d['tag'] = git_utils.git_first_containing_tag(sha1)
    d['tag_date'] = git_utils.git_get_commit_date(d['tag'])
    d['order_in_release'] = \
            commit_order_in_tag_sha_list(state, d['tag'], d['sha1'])
    d['downstream'] = None
    d['prev_downstream'] = None
    d['conflicts'] = ""
    d['prev_conflicts'] = ""

    return d

def sha_to_patch_string(state, sha):
    _d = make_patch_dict(state, sha)
    s = to_string("", _d, state)
    return s

def print_list(msg, patch_list, state):
    i = 0
    pl.print_log(">>>>>: %s" % (msg), state)
    for patch in patch_list:
        print_dict(str(i), patch, state)
        i += 1
    pl.print_log("<<<<<: %s" % (msg), state)


def compare_patch_to_downstream(state):
    print("compare_patch_to_downstream(): NEEDS RETEST **********")
    if not git_utils.git_repo_is_clean():
        pl.print_log("git status not clean. no action taken", state)
        return
    # prompt for patch to compare
    s = "enter sha of commit to compare .vs. downstream(<enter> => cancel):"
    upstream_sha = input(s)
    if not local_sha:
        return
    
    downstream_sha = state['sha_to_patch'][upstream_sha]['downstream']

    # show_diff
    (ret, local_patch) = su.shell_cmd("git show " + downstream_sha)
    (ret, upstream_patch) = su.shell_cmd("git show " + upstream_sha)
    local_line_list = [x + '\n' for x in local_patch.split('\n')]
    upstream_line_list = [x + '\n' for x in upstream_patch.split('\n')]
    sys.stdout.writelines(difflib.unified_diff(upstream_line_list,
                                               local_line_list))
    state['log_fobj'].writelines(difflib.unified_diff(upstream_line_list,
                                                      local_line_list))

