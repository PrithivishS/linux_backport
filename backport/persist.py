import ui
import pickle

def save_cp(state):
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
    
