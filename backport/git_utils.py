import subprocess
import re
import os
import threading
from print_log import *
import shell_util as su
import pdb

EG_pretty_fmt=" --pretty=tformat:'%<(10) %h  %<(12) %an : %s: %cd' "

# should subsume some of the duplicate code in git_utils.py over time
def shell_cmd(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return (result.returncode, result.stdout.decode('latin-1'))

def git_repo_is_clean():
    (ret, tmp) = su.shell_cmd("git status --porcelain")
    if tmp:
        return False
    else:
        return True
    
def git_get_subject(sha1):
    cmd = "git  log -1 --pretty=tformat:'%<(10) %h  %<(12) %an : %s' " + sha1
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = ": ".join(result.stdout.decode().split(": ")[1:])
    s= s.rstrip("\n")
    return s
    
def git_status():
    result = subprocess.run("git status", shell=True,
                            stdout=subprocess.PIPE)
    s = result.stdout.decode().strip().rstrip()
    s = "\n\n=========\n %s \n=========\n\n" % (s)
    return s
    
def git_short_log(fmt, state):
    commit_range = "%s^..HEAD" % (state['first_commit'])
    cmd = "git log " + commit_range + " --pretty=tformat:'%<(10) %h  %<(12) %an : %s'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip()
    lines = s.split("\n")
    n = len(lines)

    for (ix, line)  in zip(range(1, len(lines), 1), lines):
        print_log(str(ix) + ": " + line, state)
    
def git_get_commit_date(commitish):
    cmd = "git log -1 --pretty=format:'%ad' --date=format:'%m/%d/%y' " + commitish
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip()
    return s

def find_tag_by_sha1(sha1):
    cmd = "git tag --contains " + sha1
    ret = subprocess.check_output(cmd, shell=True)
    text = ret.decode('latin-1')
    text = text.split("\n")
    return text[0]

#
# this next function is a half baked attempt at dealing with commits that are
# in RC tags but didnt make it to a dot release
#
def git_first_containing_tag(sha1):
    result = subprocess.run("git tag --contains " + sha1, shell=True, stdout=subprocess.PIPE, encoding='utf-8')
    tags = result.stdout.split("\n");
    if len(tags) == 0: return None
    if len(tags) == 1: return tags[0]
    
    p = re.compile(tags[0] + "[0-9]*")
    if p.match(tags[1]):
        return tags[1]
    else:
        return tags[1]
        
def git_cherry_pick(sha1):
    cmd = "git  cherry-pick " + sha1
    print("* " + sha1)
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    print(result.stdout)
    os.system("git status")
    os.system("git log -5 " + EG_pretty_fmt)
    return result.returncode
    
def git_cherry_pick_continue():
    cmd = "git  cherry-pick --continue"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.returncode
    
def git_cherry_pick_abort():
    cmd = "git  cherry-pick --abort"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.returncode
    
def git_cherry_pick_by_sha(sha):
    cmd = "git  cherry-pick " + sha
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.returncode
    
def find_sha1_by_subject(subject, max_ver):
    fmt = " --pretty=tformat:'%<(10) %h  %<(12) %an : %s: %cd' "
    cmd = "git  log " + max_ver + fmt
    ret = subprocess.check_output(cmd, shell=True)
    text = ret.decode('latin-1')
    text = text.split("\n")
    doozer = [x for x in text if re.search(subject, x, re.IGNORECASE)]
    if len(doozer) > 1:
        sys.exit("more than one match for: %s" % (subject))
    if len(doozer) == 0:
        sys.exit("No matching commit for: " + subject)
    duh = doozer[0].strip()
    return duh.split(" ")[0]

def add_or_inc_ver_num(path):
    L = path.split(".")
    if  L[-1:][0].isnumeric():
        s = ".".join(L[:-1] + [str(int(L[-1:][0]) + 1)])
    else:
        s = path + ".1"
    return s

def get_current_branch(): # works on git < 2.22
    result = subprocess.run("git rev-parse --abbrev-ref HEAD",
                            shell=True, stdout=subprocess.PIPE)
    return result.stdout.decode("latin-1").strip()

def next_branch(state):
    if not git_repo_is_clean():
        print_log("git status not clean. no action taken", state)
        return
    cmd = "git checkout -b " +  add_or_inc_ver_num(get_current_branch())
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip().rstrip()
    git_status()
    print_log(s, state)

def git_applied_sha_list(state):
    range = "%s^..HEAD" % (state['first_commit'])
    cmd = "git log " + range + " --pretty=tformat:'%<(10) %h'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip()
    s = s.split("\n")
    return s[: -1]

def clip_long_output(s, state):
    if 'clip_long_output' in state:
        clip_len = int(state['clip_long_output'])
        if len(s) > clip_len:
            s = s[0: clip_len - 1]
    return s

def git_log_tag(state, min_max):
    if min_max == "min":
        key = 'git_log_min_tag'
    elif min_max == "max":
        key = 'git_log_max_tag'
    else:
        print("bad input")
        return None
    if key not in state:
        val = input("enter release tag for %s: " % (key))
        state[key] = val
        return val
    else:
        return state[key]
    
def search_commit_for_pattern(search_type, pattern, tag1, tag2, line_fn, state,
                              sha):
    key = search_type + "," + pattern + "," + tag1 +"," + tag2
    cmd = "git show %s | grep %s" % (sha, pattern)
    #_pdb = pdb.Pdb();_pdb.set_trace()
    (ret, out) = su.shell_cmd(cmd)

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
    cmd =  "git log -%s%s" % (search_type, pattern)
    cmd += " --pretty=tformat:\'%<(10) %h\'"
    cmd += " %s..%s" % (tag1, tag2)
    (ret, out) = su.shell_cmd(cmd)
    #_pdb = pdb.Pdb();_pdb.set_trace()
    out = [x.lstrip() for x in out.rstrip("\n").split("\n")]

    for sha in out:
        search_commit_for_pattern(search_type, pattern, tag1, tag2, line_fn,
                                  state, sha)
    key = search_type + "," + pattern + "," + tag1 +"," + tag2
    state['git_log_completed'].append(key)
    return ret
    
def git_top_of_applied_stack_sha(state):
    (ret,tap_sha) = su.shell_cmd("git rev-parse --short HEAD")
    if not tap_sha:
        print_log("** something is very wrong. can't find sha of top commit**",
                  state)
    return tap_sha.rstrip('\n')

def git_get_conflicts():
    cmd = "git diff --diff-filter=U"
    (ret, out) = su.shell_cmd(cmd)
    return out

def git_reset_hard(sha1, state): #: @misplaced, @base-git
    cmd = "git  reset --hard  " + sha1
    print("about to: " + cmd)
    
    if not ui.confirm("\nEnter 'y' to proceed, else <enter>: ", ['y']):
        return -1

    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)

    return result.returncode    

def show_patch_by_sha(state): #: @git
    sha = input("enter sha of patch to be shown: ")
    (ret, output) = su.shell_cmd("git show " + sha)
    pl.print_log(output, state)

def git_status_log(state): #: @obsolete
    s = git_utils.git_status(state)
    
def do_git_status(state): #: @meta_git
    s = git_status()
    pl.print_log(s, state)

def get_short_sha_list_by_key(key, git_path = None):
    if git_path:
        cmd = f"git -C {git_path} log --pretty=tformat:'%h' {key}"
    else:
        cmd = f"git log --pretty=tformat:'%h' {key}"
    (ret, out) = su.shell_cmd(cmd)
    out = out.split("\n")
    return out

def log_sync(git_path = None, commitish = None, fmt = "'%h'",):
    # synchronous git log
    # example
    # ocos_analysis.py --vendor_tree_path=~/wrk/amd/OpenCloudOS-Kernel \
    # --vendor_branch=5.4.119-20.0009.30.spr.0001
    #FIXME: existing git log cmds should be rewritten in terms of this
    # returns list of git log output lines
    if git_path:
         cmd = f"git -C {git_path} log"
    if fmt:
        cmd += f" --pretty=tformat:{fmt}"
    if commitish:
         cmd += f" {commitish}"

    (ret, out) = su.shell_cmd(cmd)
    out = out.split("\n")
    return out[:-1]
