import pdb
import pickle
import sys
import importlib
import glob
from git_utils import *
import git_utils

def print_log(s, fobj):
    print(s)
    if fobj:
        print(s, file=fobj)
        fobj.flush()

def save_cp(state):
    st = state
    tmp = state['log_fobj']
    state['log_fobj'] = None
    f = state['pickle_dir'] + "/" + state['pickle_file'] + "." +\
        str(state['cp_num'])
    with open(f, 'wb') as handle:
        pickle.dump(st, handle, protocol=pickle.HIGHEST_PROTOCOL)
    state['cp_num']  = int(state['cp_num']) + 1
    state['log_fobj'] = tmp
    print_log("@@save_cp: " + f, tmp)

def restore_cp(fpath):
    with open(fpath, 'rb') as handle:
        return pickle.load(handle)

def print_patch_dict(msg, patch, fobj):  # do we really re-use this?
    s = "%s, %s, %s, %s, %s, prq(%s)" % (
        msg, patch['sha1'], patch['subject'], patch['tag'],
              patch['tag_date'], patch['is_pre_req'])
    print_log(s, fobj)

def make_patch_dict(sha1):
    print("lookup %s" % (sha1))
    d = dict()
    d['sha1'] = sha1
    d['done'] = False
    d['pre_reqs'] = list()
    d['is_pre_req'] = False
    #why is it suddenly needed to prefix the "git_utils." bit?
    d['subject'] = git_utils.git_get_subject(sha1)
    d['tag'] = git_utils.git_first_containing_tag(sha1)
    d['tag_date'] = git_utils.git_get_commit_date(d['tag'])
    print("%s, %s, %s, %s, prq(%s)" %
          (d['sha1'], d['subject'], d['tag'],
           d['tag_date'], d['is_pre_req']))
    return d

def print_patch_list(msg, patch_list, fobj):
    i = 0
    print_log(">>>>>: %s" % (msg), fobj)
    for patch in patch_list:
        print_patch_dict(str(i), patch, fobj)
        i += 1
    print_log("<<<<<: %s" % (msg), fobj)

def show_menu(menu):
    for (ix, d) in zip(range(len(menu) + 1), menu):
        print(str(ix) + ": " + menu[ix]['prompt'])

def do_menu_choice(menu, state):
    while True:
        show_menu(menu)
        x = int(input("enter choice: "))
        if x in range(len(menu)): break
        else: print("bad input")

    menu[x]['action'](state)

def do_bash(fobj):
    print("entering bash", file=fobj);fobj.flush()
    subprocess.run(['bash'])

def next_cp_num(args):
    pfre = args.pickle_dir + "/" + args.pickle_file + ".*"
    L = glob.glob(pfre)
    L.sort()
    if len(L) < 1:
        return 1
    return int(L[-1:][0].split(".")[-1:][0]) + 1

#
# we look for pickle files in this order:
#
#    - if args.pickle_num is given, only that pickle file
#    - if files match "pickle.*", the largest one
#    - otherwise fail since the initial picke file should be created by
#      sha2pckl
#
def load_pickle_file(state):
    print("loading state")
    pd = state['args'].pickle_dir
    pf = state['args'].pickle_file
    
    if state['args'].pickle_num:
        f = pd + "/" + pf + "." + state['args'].pickle_num
        st = restore_cp(f)
    else:
        max_pickle_num = str(next_cp_num(state['args']) - 1)
        f = pd + "/" + pf + "." + max_pickle_num
        st = restore_cp(f)
        
    state['patch_list'] = st['patch_list']

def sha_file_to_pickled_state(state):
    sha_list = state['args'].sha_list
    
    # as if it wasn't obvious <patch> should be class ...
    patch_list = [make_patch_dict(l.strip())
                  for l in open(sha_list,"r")]

    state['patch_list'] = patch_list
    save_cp(state)

def show_sha_info(fobj):
    sha = input("enter sha1(return to exit): ")
    if not sha: return Nnone
    subj = git_utils.git_get_subject(sha)
    tag = git_utils.git_first_containing_tag(sha)
    tag_date = git_utils.git_get_commit_date(tag)
    s  = "%s, %s, %s, %s" % (sha, subj, tag, tag_date)
    print_log(s, fobj)
                  
