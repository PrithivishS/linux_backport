import pdb
import pickle
import sys
import importlib
import glob
from git_utils import *
import git_utils
from datetime import datetime
import select
import shutil
import shlex
import tempfile
import difflib

def confirm(prompt, legal_response_list):
    tmp = input(prompt)
    if tmp in legal_response_list:
        return tmp
    else:
        return ''
    
def get_out_dest(state):
    if not state: return ""
    if not 'out_dest' in state.keys():
        state['out_dest'] = 'both'
    return state['out_dest']
    
def print_log(s, state):
    if get_out_dest(state) == 'both':
        print(s)
    if state['log_fobj']:
        print(s, file=state['log_fobj'])
        state['log_fobj'].flush()

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
    print_log("@@save_cp: " + f, state)

def restore_cp(fpath):
    try:
        with open(fpath, 'rb') as handle:
            return pickle.load(handle)
    except:
        print("*WARNING* cannot restore pickle file: " + fpath)
        if not confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
            sys.exit

def print_patch_dict(msg, patch, state):  # do we really re-use this?
    s = "%s, %s, %s, %s, %s, prq(%s)" % (
        msg, patch['sha1'], patch['subject'], patch['tag'],
              patch['tag_date'], patch['is_pre_req'])
    print_log(s, state)

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

def top_patch_has_upstream_citation(state):
    tap_sha = git_utils.git_top_of_applied_stack_sha(state)
    if not tap_sha:
        return
    if patch_cites_upstream(tap_sha):
        return True
    else:
        return False

    
def show_menu_trailer(state):
    trailer = ""
    if not git_utils.git_repo_is_clean():
        trailer = "\n** working tree UNCLEAN **"
        
    if not top_patch_has_upstream_citation(state):
        trailer += "** top applied patch lacks 'commit <sha> upstream' **"
    if trailer:
        trailer = '\n' + trailer +'\n'
        print_log(trailer, state)
        
def show_menu(menu, state):
    for (ix, d) in zip(range(len(menu) + 1), menu):
        print(str(ix) + ": " + menu[ix]['prompt'])
    show_menu_trailer(state)

def do_menu_choice(menu, state):
    while True:
        while True:
            show_menu(menu, state)
            x = input("enter choice(<enter> to exit menu): ")
            if not x: save_cp(state);return
            try:
                x = int(x)
            except:
                print_log("oops", state)
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
        print_log("menu choice was <%s>" % (x), state)
        print_patch_list("__PATCH LIST__", state)
        git_utils.git_short_log('%<(10) %h  %<(12) %an : %s', state)
        state['out_dest'] = 'both'

def next_cp_num(args):
    pfre = args.pickle_dir + "/" + args.pickle_file + ".*"
    L = glob.glob(pfre)
    L.sort()
    if len(L) < 1:
        return 1
    ret = max([int(l.split('.')[-1]) for l in L]) + 1
    return ret

def copy_key_val_if_present(key, dst_hash, src_hash, state):
    if src_hash is None: return
    
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
    pd = state['args'].pickle_dir
    pf = state['args'].pickle_file
    
    if state['args'].pickle_num:
        f = pd + "/" + pf + "." + state['args'].pickle_num
    else:
        max_pickle_num = str(next_cp_num(state['args']) - 1)
        f = pd + "/" + pf + "." + max_pickle_num
    print_log("loading state: " + f, state)
    st = restore_cp(f)
        
    # not an accident that <state> is repeated. it wont always be <dst_hash>
    copy_key_val_if_present('patch_list', state, st, state)
    copy_key_val_if_present('applied_patch_list', state, st, state)
    copy_key_val_if_present('build_cmd', state, st, state)
    copy_key_val_if_present('branch_backup_cmd', state, st, state)

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
                  
def prompted_show_sha_info(state):
    sha = input("enter sha1(return to exit): ")
    if not sha: return Nnone
    print_log(show_sha_info(sha), state)

                  
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
def shell_cmd(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return (result.returncode, result.stdout.decode('latin-1'))

def poll_shell_cmd(cmd, shell_args, line_fn, state):
    cmd = shutil.which(cmd)
    shell_args = shlex.split(shell_args)
    cmd = [ cmd] + shell_args
    shell_args = ' '.join(shell_args)
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    # Create empty buffers and a polling object
    poll = select.poll()
    poll.register(process.stdout, select.POLLIN)
    poll.register(process.stderr, select.POLLIN)

    # Continuously poll the stdout and stderr streams to capture output as it
    # appears
    spew = []
    while process.poll() is None:
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [])
        for stream in rlist:
            line = stream.readline().decode().rstrip("\n")
            spew.append(line)
            line_fn(line, state)
          
    return spew
              
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
        
def get_sha_info(sha, subj):
    if not subj:
        subj = git_utils.git_get_subject(sha)

    tag = git_utils.git_first_containing_tag(sha)
    tag_date = git_utils.git_get_commit_date(tag)
    tmp = "%s, %s, %s, %s" % (sha, subj, tag, tag_date)
    return tmp
    
def import_sha_list_file(path, action, state):
    legal_actions = {
        'set'     : lambda x: x,
        'prepend' : lambda x: x + state['patch_list'],
        'append'  : lambda x: state['patch_list'] + x
    }
    
    print_log("@@import_sha_list_file(%s, %s,...)" % (path, action),
              state)

    if not action in legal_actions:
        print_log("error bad action", state['log_fobj'])
        
    #sha_list = state['args'].sha_list
    # as if it wasn't obvious <patch> should be class ...
    patch_list = [make_patch_dict(l.strip())
                  for l in open(path,"r")]
    if not confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
        return
    state['patch_list'] = legal_actions[action](patch_list)
    save_cp(state)

def patch_cites_upstream(local_sha):
    (ret, log_lines) = shell_cmd("git log -1 %s" % (local_sha))
    pat = "(commit )([0-9a-f]+)( upstream)"
    matches = []
    log_lines = [l.strip() for l in log_lines.split('\n')]
    for l in log_lines:
        match = re.search(pat, l)
        if match:
            matches.append(match.group(2))

    if len(matches) == 1:
        return matches[0] # upstream sha
    else:
        return False

def compare_patch_to_upstream(state):
    if not git_utils.git_repo_is_clean():
        print_log("git status not clean. no action taken", state)
        return
    # prompt for patch to compare
    s = "enter sha of commit to compare .vs. upstream(<enter> => top patch):"
    local_sha = input(s)
    if not local_sha:
        local_sha = git_utils.git_top_of_applied_stack_sha(state)

    # check if patch notes upstream
    upstream_sha = patch_cites_upstream(local_sha)
    if not upstream_sha:
        print("no upstream citation found, returning")
        return
    
    
    # show_diff
    (ret, local_patch) = shell_cmd("git show " + local_sha)
    (ret, upstream_patch) = shell_cmd("git show " + upstream_sha)
    local_line_list = [x + '\n' for x in local_patch.split('\n')]
    upstream_line_list = [x + '\n' for x in upstream_patch.split('\n')]
    sys.stdout.writelines(difflib.unified_diff(upstream_line_list,
                                               local_line_list))
    state['log_fobj'].writelines(difflib.unified_diff(upstream_line_list,
                                                      local_line_list))
    
def show_top_unapplied_patch(state):
    tap_sha = git_utils.git_top_of_applied_stack_sha(state)
    (ret, output) = shell_cmd("git show " + tap_sha)
    print_log(output, state)

def top_cites_upstream_or_confirmed_dont_care(state):
    tap_sha = git_utils.git_top_of_applied_stack_sha(state)

    if patch_cites_upstream(tap_sha): return True

    print_log("** top patch does not cite upstream **")
    if onfirm("Enter 'y' to proceed, else <enter>: ", ['y']):
        return True

    return False
