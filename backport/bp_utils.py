import pdb
import pickle
import sys
import importlib
import glob
from git_utils import *
import git_utils
from datetime import datetime

def get_out_dest(state):
    if not 'out_dest' in state.keys():
        state['out_dest'] = 'both'
    return state['out_dest']
    
def print_log(s, state):
    if get_out_dest(state) == 'both':
        print(s)
    if state['log_fobj']:
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

def print_patch_list(msg, state):
    i = 0
    print_log(">>>>>: %s" % (msg), state)
    for patch in state['patch_list']:
        print_patch_dict(str(i), patch, state)
        i += 1
    print_log("<<<<<: %s" % (msg), state)

def show_menu(menu, state):
    for (ix, d) in zip(range(len(menu) + 1), menu):
        print(str(ix) + ": " + menu[ix]['prompt'])
    if not git_utils.git_repo_is_clean():
        print_log("\n** working tree UNCLEAN **", state)

def do_menu_choice(menu, state):
    while True:
        while True:
            show_menu(menu, state)
            x = input("enter choice(<enter> to exit menu): ")
            if not x: save_cp(state);return
            x = int(x)
            if x in range(len(menu)): break
            else: print("bad input")
        if 'sub-menu' in menu[x].keys():
            do_menu_choice(menu[x]['sub-menu'], state)
        else:
            menu[x]['action'](state)
            state['log_fobj'].flush()

def next_cp_num(args):
    pfre = args.pickle_dir + "/" + args.pickle_file + ".*"
    L = glob.glob(pfre)
    L.sort()
    if len(L) < 1:
        return 1
    return int(L[-1:][0].split(".")[-1:][0]) + 1

def copy_keval_if_present(key, dst_hash, src_hash, state):
    if key in src_hash.keys():
        dst_hash[key] = src_hash[key]
    else:
        print_log("WARNING: pickle file lacks %s" % (key), state)
        
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
        
    # not an accident that <state> is repeated. it wont always be <dst_hash>
    copy_keval_if_present('patch_list', state, st, state)
    copy_keval_if_present('applied_patch_list', state, st, state)
    copy_keval_if_present('build_cmd', state, st, state)
    copy_keval_if_present('branch_backup_cmd', state, st, state)

def sha_file_to_pickled_state(state):
    sha_list = state['args'].sha_list
    
    # as if it wasn't obvious <patch> should be class ...
    patch_list = [make_patch_dict(l.strip())
                  for l in open(sha_list,"r")]

    state['patch_list'] = patch_list
    save_cp(state)

def show_sha_info(sha):
    if not sha: return ""
    subj = git_utils.git_get_subject(sha)
    tag = git_utils.git_first_containing_tag(sha)
    tag_date = git_utils.git_get_commit_date(tag)
    s  = "%s, %s, %s, %s" % (sha, subj, tag, tag_date)
    return s
                  
def prompted_show_sha_info(fobj):
    sha = input("enter sha1(return to exit): ")
    if not sha: return Nnone
    print_log(show_sha_info(sha), fobj)

                  
def prompt_to_set_or_alter_state(key, d):
    # if no saved value for key
    #	prompt for it
    #	save to d
    # else 
    #	show saved value, ask if they want to change
    #	save in d if changed
    if not key in d:
        cmd = input("enter %s or <enter> to skip: " % (key))
        if cmd:
            d[key] = cmd
    else:
        cmd = d[key]
        print("build command is: " + cmd)
        tmp = input("enter %s to change or <enter> to use existing: "
                    % (key))
        if tmp:
            d[key] = tmp
            
# should subsume some of the duplicate code in git_utils.py over time
def general_shell_cmd(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return (result.returncode, result.stdout.decode('latin-1'))

def state_init(args): # anoter obvious objuect
    state = dict()
    state['cp_num'] = next_cp_num(args)
    state['pickle_dir'] = args.pickle_dir
    state['pickle_file'] = args.pickle_file
    state['log_fobj'] = open(args.log_file, 'a')
    state['first_commit'] = args.first_commit
    state['args'] = args
    #TBD:, FIXME:  get rid of state fields from args that !change
    return state

def backport_patches(state, menu_item_list):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Startup: Current Time =", current_date_time,
          file = state['log_fobj'])

    state['log_fobj'].flush()
    do_menu_choice(menu_item_list, state)
        
