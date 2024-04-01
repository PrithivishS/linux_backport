import state_access

def print_log(s, state):
    if not state or 'log_fobj' not in state:
        print("<no logf> " + s)
        return
    if state_access.get_out_dest(state) == 'both':
        print(s)
    if state['log_fobj']:
        print(s, file=state['log_fobj'])
        state['log_fobj'].flush()
