import git_utils
import shell_util as su
import re
import print_log as pl
import patch

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

# Following the Genoa Patch List format, the file format is expected to be
#	<sha> <version introduced> 
def genoa_patch_list_format_to_sha_list(path, state):
    def is_hex_str(s):
        try:
            int(s, 16)
            return True # there would have been exception if not valid hex string
        except:
            return False

    ret = list()
    for l in open(path, "r"):
        _l = l
        _l = l.split(' ')
        sha = _l[0]
        if is_hex_str(sha):
            ret.append(sha)
        else:
            pl.print_log("rejecting %s" % (l), state)
    return ret

def import_sha_list_file(path, state):

    patch_list = [patch.make_patch_dict(state, sha, True)
                  for sha in genoa_patch_list_format_to_sha_list(path, state)]
    return patch_list

def active_cherry_pick_sha(state):#: @meta_git
    # parse git status and find sha we're cherry_picking
    (ret, classic_status) = su.shell_cmd("git status")
    (ret, porcelain_status) = su.shell_cmd("git status --porcelain")

    classic_pat = "(.*cherry-picking commit )([a-fA-F0-9]+)(.*)"
    match = re.search(classic_pat, classic_status)
    try:
        cherry_pick_sha = match.group(2)
        return cherry_pick_sha
    except:
        return None
    
