
def get_out_dest(state):
    if not state: return ""
    if not 'out_dest' in state.keys():
        state['out_dest'] = 'both'
    return state['out_dest']
    
