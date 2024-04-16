import ui
import pickle
import glob
import print_log as pl
import sys
import state_access as sa
import persist
import os

def create_pickle_dir_if_needed(state):
    pd = state['pickle_dir']
    if not os.path.isdir(pd):
        os.mkdir(pd)
        if not os.path.isdir(pd):
            return False # mkdir failed
    return True
    
def save_cp(state):
    if not create_pickle_dir_if_needed(state):
        pl.print_log("WARNING CAN'T CREATE PICKLE DIR: " + state['pickle_dir'])
        return
    st = state
    tmp = state['log_fobj']
    for slot in ['log_fobj', 'args', 'sha_lists_by_tag', 'unresolved_syms',
                 'unmatched_errors']:
        state[slot] = None

    f = state['pickle_dir'] + "/" + state['pickle_file'] + "." +\
        str(state['cp_num'])
    with open(f, 'wb') as handle:
        pickle.dump(st, handle, protocol=pickle.HIGHEST_PROTOCOL)
    state['cp_num']  = int(state['cp_num']) + 1
    state['log_fobj'] = tmp
    pl.print_log("@@save_cp: " + f, state)

def restore_cp(fpath):
    try:
        with open(fpath, 'rb') as handle:
            return pickle.load(handle)
    except:
        print("*WARNING* cannot restore pickle file: " + fpath)
        if not ui.confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
            sys.exit
        return None
    
def next_cp_num(args):  #: core, @ui, @io, state
    pfre = args.pickle_dir + "/" + args.pickle_file + ".*"
    L = glob.glob(pfre)
    L.sort()
    if len(L) < 1:
        return 1
    ret = max([int(l.split('.')[-1]) for l in L]) + 1
    return ret

#
# we look for pickle files in this order:
#
#    - if args.pickle_num is given, only that pickle file
#    - if files match "pickle.*", the largest one
#    - otherwise fail since the initial picke file should be created by
#      sha2pckl
#
def load_pickle_file(args, state):#: core, @ui, @io, state
    pd = state['args'].pickle_dir
    pf = state['args'].pickle_file
    
    if state['args'].pickle_num:
        f = pd + "/" + pf + "." + state['args'].pickle_num
    else:
        max_pickle_num = str(next_cp_num(state['args']) - 1)
        f = pd + "/" + pf + "." + max_pickle_num
    pl.print_log("loading state: " + f, state)

    state = restore_cp(f)
    if not state: state = sa.state_init(args)
    state['log_fobj'] = open(args.log_file, 'a')
    state['cp_num'] = persist.next_cp_num(args)
    state['sha_to_patch'] = {p['sha1'] : p for p in state['all_patches']}
    return state

