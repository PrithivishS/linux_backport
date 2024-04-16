import print_log as pl
import git_utils
import meta_git as mg
import pdb
import os
import shell_util as su

def status(patch, state):
    if patch['downstream']: return 'applied'
    if patch['sha1'] == mg.active_cherry_pick_sha(state):
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
    sha1 = sha1.lstrip().rstrip()
    d['sha1'] = sha1
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

def commit_order_in_tag_sha_list(state, tag, sha):
    if not tag: return -1
    slbt = state['sha_lists_by_tag']
    if not slbt:
        state['sha_lists_by_tag'] = dict()
        slbt = state['sha_lists_by_tag']

    if tag not in slbt:
        L = git_utils.get_short_sha_list_by_key(tag)
        slbt[tag] = L
    else:
        L = slbt[tag]

    try:
        ix = len(L) - L.index(sha)
    except:
        print(f"CAN'T FIND RELEASE CONTAINING {sha}")
        return -1
    return ix
def generate_blame_files(sha, file, state):#: @meta_git, @workflow?
    dir = state['cherry_pick_files'] + '/' + sha
    fbase = os.path.split(file)[1]
    for _sha in ['HEAD', sha]:
        for sfx in  ['^', '']:
            SHA = _sha + sfx
            cmd = f"git blame {SHA} -- {file} > {dir}/{SHA}.{fbase}"
            print(cmd)
            su.shell_cmd(cmd)

def show_patch(cherry_pick_sha, file, state):#: @patch
    cmd = "git show %s:%s > %s/%s/%s" % (cherry_pick_sha, file,
                                         state['cherry_pick_files'],
                                         cherry_pick_sha,

                                         os.path.split(file)[1])
    su.shell_cmd(cmd)
    
def generate_conflict_resolution_files(cherry_pick_sha, file, state):#: @workflow
    show_patch(cherry_pick_sha, file, state)
    generate_blame_files(cherry_pick_sha, file, state)

def get_sorted_patch_list_from_sha_list(patch, file, state):#: meta_git
    min = state['git_log_min_tag']
    max = patch['sha1']
    cmd = f"git log --pretty=tformat:'%h' {min}..{max} {file}"
    (ret, out) = su.shell_cmd(cmd)
    sha_list = uniqify_list(out.split("\n"))[:-1]
    patch_list = [make_patch_dict(state, sha) for sha in sha_list]
    patch_list.sort(key= lambda x: x['order_in_release'])
    patch.print_list("", patch_list, state)
    return patch_list

