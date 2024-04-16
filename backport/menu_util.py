import git_utils as git
import meta_git as mg
import bp_utils as bpu
import print_log as pl
import persist

def get_menu_trailer(state):
    trailer = "\n\n%d commits (%d applied)" % (len(state['all_patches']),
                                           sum(1 for p
                                               in state['all_patches']
                                               if p['downstream']))
    if not git.git_repo_is_clean():
        trailer += "\n** working tree UNCLEAN **"

    if mg.active_cherry_pick_sha(state):
        trailer += "\n** active cherry-pick ** "
        
    if trailer:
        trailer += '\n'
        
    return trailer

        
def show_menu_trailer(state):
    print(get_menu_trailer(state))
    
def show_menu(menu, state):
    print("\n\n==================")
    for (ix, d) in zip(range(len(menu) + 1), menu):
        print(str(ix) + ": " + menu[ix]['prompt'])
    show_menu_trailer(state)

def do_menu_choice(menu, state):
    while True:
        while True:
            show_menu(menu, state)
            x = input("enter choice(<enter> to exit menu): ")
            if not x: persist.save_cp(state);return
            try:
                x = int(x)
            except:
                pl.print_log("oops", state)
                continue
            if x in range(len(menu)): break
            else: print("bad input")
        if 'sub-menu' in menu[x].keys():
            do_menu_choice(menu[x]['sub-menu'], state)
        else:
            menu[x]['action'](state)
            state['log_fobj'].flush()

        # log unapplied and active(on git log) patches after every menu op
        state['out_dest'] = 'log_only'
        pl.print_log("menu choice was <%s>" % (x), state)
        git.git_short_log('%<(10) %h  %<(12) %an : %s', state)
        state['out_dest'] = 'both'

