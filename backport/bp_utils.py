import pdb
import pickle
import sys
import importlib
import glob
from git_utils import *

def save_cp(state):
    st = state
    tmp = state['log_fobj']
    f = state['pickle_dir'] + "/" + state['pickle_file'] + "." +\
        str(state['cp_num'])
    with open(f, 'wb') as handle:
        pickle.dump(st, handle, protocol=pickle.HIGHEST_PROTOCOL)
    state['cp_num']  = int(state['cp_num']) + 1
    state['log_fobj'] = tmp

def restore_cp(fpath):
    with open(fpath, 'rb') as handle:
        return pickle.load(handle)

def print_log(s, fobj):
    print(s)
    if fobj:
        print(s, file=fobj)
        fobj.flush()

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
    d['subject'] = git_get_subject(sha1)
    d['tag'] = git_first_containing_tag(sha1)
    d['tag_date'] = git_get_commit_date(d['tag'])
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
def load_pickle_file(args):
    if args.pickle_num:
        f = args.pickle_dir + "/" + args.pickle_file + "." + args.pickle_num
        return restore_cp(f)
    else:
        max_pickle_num = str(next_cp_num(args) - 1)
        f = args.pickle_dir + "/" + args.pickle_file + "." + max_pickle_num
        return restore_cp(f)

def add_common_args(parser):
    parser.add_argument('--pickle-file', default='backport.pickle',
                        help='pickle file to load')
    parser.add_argument('--pickle-dir', default='/tmp',
                        help='where to store checkpoints')
    parser.add_argument('--log-depth', default='10',
                    help='# of commits to show on git log menu item')

def sha_file_to_pickled_state(args):
    if not args.sha_list or not args.pickle_dir \
       or not args.pickle_file or not args.pickle_num:
        print("use sha_list, pickle_dir, pickle_file, pickle_num")
        return
    
    # as if it wasn't obvious <patch> should be class ...
    patch_list = [make_patch_dict(l.strip())
                  for l in open(args.sha_list,"r")]

    state = {'pickle_dir' : args.pickle_dir,
             'pickle_file': args.pickle_file,'cp_num': args.pickle_num,
             'patch_list': patch_list}
    save_cp(state)
    return state
