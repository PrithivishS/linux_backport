import subprocess
import re
import os
from bp_utils import *

EG_pretty_fmt=" --pretty=tformat:'%<(10) %h  %<(12) %an : %s: %cd' "

def git_get_subject(sha1):
    cmd = "git  log -1 --pretty=tformat:'%<(10) %h  %<(12) %an : %s' " + sha1
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = ": ".join(result.stdout.decode().split(": ")[1:])
    s= s.rstrip("\n")
    return s
    
def menu_action_git_status(state):
    result = subprocess.run("git status", shell=True,
                            stdout=subprocess.PIPE)
    s = result.stdout.decode().strip().rstrip()
    s = "\n\n=========\n %s \n=========\n\n" % (s)
    print_log(s, state['log_fobj'])
    
def git_short_log(state, fmt):
    range = "%s^..HEAD" % (state['first_commit'])
    cmd = "git log " + range + " --pretty=tformat:'%<(10) %h  %<(12) %an : %s'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip()
    print_log(s.rstrip("\n"), state['log_fobj'])
    
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
    
def git_reset_hard(sha1):
    cmd = "git  reset --hard  " + sha1
    print("about to: " + cmd)
    input("<enter> to continue, else <control-c>")
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return result.returncode
    
def git_cherry_pick__continue():
    cmd = "git  cherry-pick --continue"
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

def menu_action_next_branch(state):
    cmd = "git checkout -b " +  add_or_inc_ver_num(get_current_branch())
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip().rstrip()
    menu_action_git_status(state)
    print_log(s, state['log_fobj'])

def git_applied_sha_list(state):
    range = "%s^..HEAD" % (state['first_commit'])
    cmd = "git log " + range + " --pretty=tformat:'%<(10) %h'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    s = result.stdout.decode().strip()
    s = s.split("\n")
    return s[: -1]

