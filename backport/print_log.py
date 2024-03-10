import print_log

def get_out_dest(state):
    if not state: return ""
    if not 'out_dest' in state.keys():
        state['out_dest'] = 'both'
    return state['out_dest']
    
def print_log(s, state):
    if not state or 'log_fobj' not in state:
        print("<no logf> " + s)
        return
    if get_out_dest(state) == 'both':
        print(s)
    if state['log_fobj']:
        print(s, file=state['log_fobj'])
        state['log_fobj'].flush()
