
def get_out_dest(state):
    if not state: return ""
    if not 'out_dest' in state.keys():
        state['out_dest'] = 'both'
    return state['out_dest']

def state_init(args): # anoter obvious objuect #: state, @persist
    state = dict()
    state['cherry_pick_files'] = "/tmp/cp__files"
    state['all_patches'] = list()
    state['pickle_dir'] = args.pickle_dir
    state['pickle_file'] = args.pickle_file
    state['first_commit'] = args.first_commit
    state['args'] = args
    state['sha_lists_by_tag'] = dict()
    #TBD:, FIXME:  get rid of state fields from args that !change
    state['patch_list_history'] = []
    state['backport_in_progress'] = False
    state['sha_to_patch'] = dict()
    state['downstream_sha_to_patch'] = dict()
    return state

