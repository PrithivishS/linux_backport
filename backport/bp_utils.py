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
from packaging import version

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
    if not state or 'log_fobj' not in state:
        print("<no logf> " + s)
        return
    if get_out_dest(state) == 'both':
        print(s)
    if state['log_fobj']:
        print(s, file=state['log_fobj'])
        state['log_fobj'].flush()

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
    print_log("@@save_cp: " + f, state)

def restore_cp(fpath):
    try:
        with open(fpath, 'rb') as handle:
            return pickle.load(handle)
    except:
        print("*WARNING* cannot restore pickle file: " + fpath)
        if not confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
            sys.exit
        return None

def print_patch_dict(msg, patch, state):  # do we really re-use this?
    s = "%s, %s, %s, %s, %s" % (
        msg, patch['sha1'], patch['subject'], patch['tag'],
              patch['tag_date'])
    print_log(s, state)

def make_patch_dict(state, sha1):
    print("lookup %s" % (sha1))
    d = dict()
    d['sha1'] = sha1.lstrip().rstrip()
    d['sha1'] = d['sha1'][:12]
    d['done'] = False
    d['pre_reqs'] = list()
    d['is_pre_req'] = False
    #why is it suddenly needed to prefix the "git_utils." bit?
    d['subject'] = git_utils.git_get_subject(sha1)
    d['tag'] = git_utils.git_first_containing_tag(sha1)
    d['tag_date'] = git_utils.git_get_commit_date(d['tag'])
    d['order_in_release'] = \
            commit_order_in_tag_sha_list(state, d['tag'], d['sha1'])
    print("%s, %s, %s, %s, prq(%s)" %
          (d['sha1'], d['subject'], d['tag'],
           d['tag_date'], d['is_pre_req']))
    return d

def print_patch_list(msg, patch_list, state):
    i = 0
    print_log(">>>>>: %s" % (msg), state)
    for patch in patch_list:
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
    print("\n\n==================")
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
        #print_patch_list("__PATCH LIST__", state['unapplied_patches'], state)
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
def load_pickle_file(args, state):
    pd = state['args'].pickle_dir
    pf = state['args'].pickle_file
    
    if state['args'].pickle_num:
        f = pd + "/" + pf + "." + state['args'].pickle_num
    else:
        max_pickle_num = str(next_cp_num(state['args']) - 1)
        f = pd + "/" + pf + "." + max_pickle_num
    print_log("loading state: " + f, state)

    state = restore_cp(f)
    if not state: state = state_init()
    state['log_fobj'] = open(args.log_file, 'a')
    state['cp_num'] = next_cp_num(args)
    
    state['sha_to_patches'] = {p['sha1'] : p for p in state['all_patches']}
    return state

def sha_file_to_pickled_state(state):
    sha_list = state['args'].sha_list
    
    # as if it wasn't obvious <patch> should be class ...
    patch_list = [make_patch_dict(state, l)
                  for l in open(sha_list,"r")]

    state['unapplied_patches'] = patch_list
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
    state['unapplied_patches'] = list()
    state['all_patches'] = list()
    state['pickle_dir'] = args.pickle_dir
    state['pickle_file'] = args.pickle_file
    state['first_commit'] = args.first_commit
    state['args'] = args
    state['sha_lists_by_tag'] = dict()
    #TBD:, FIXME:  get rid of state fields from args that !change
    state['patch_list_history'] = []
    state['backport_in_progress'] = False
    return state

def backport_patches(state, menu_item_list):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_log("Startup: Current Time = %s" %(current_date_time), state)

    do_menu_choice(menu_item_list, state)
        
def get_sha_info(sha, subj):
    if not subj:
        subj = git_utils.git_get_subject(sha)

    tag = git_utils.git_first_containing_tag(sha)
    tag_date = git_utils.git_get_commit_date(tag)
    tmp = "%s, %s, %s, %s" % (sha, subj, tag, tag_date)
    return tmp
    
def import_sha_list_file(path, state):
    print_log("@@import_sha_list_file(%s...)" % (path), state)

    patch_list = [make_patch_dict(state, l)
                  for l in open(path,"r")]
    return patch_list

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

    print_log("** top patch does not cite upstream **", state)
    if confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
        return True

    return False

def build(state):
    print_log("@@build", state)
    line_fn = lambda line, state: print_log(line, state)
    prompt_to_set_or_alter_state('build_cmd', state)
    if not state['build_cmd']:
        return

    # do it, ignore ret text(for now @ least)
    # assume build_cmd is of the form: <cmd> <arg string>
    L = state['build_cmd'].split(' ')
    shell_args = ' '.join(L[1:])
    spew = poll_shell_cmd(L[0], shell_args, line_fn, state)
    print_log(spew, state)
    return spew

def old_build(state):
    print_log("@@build", state)
    line_fn = lambda line, state: print_log(line, state)
    prompt_to_set_or_alter_state('build_cmd', state)
    if not state['build_cmd']:
        return

    (ret, spew) = shell_cmd(state['build_cmd'])
    return spew

pats = {
    'undecl-fn' :  {
        'pat': "(.*error: implicit declaration of function ‘)([a-zA-Z_][a-zA-Z0-9_]*)(’.*)",
            'groups' : [2]
    },
    'no_mbr' :  {
        #arch/x86/kvm/../../../virt/kvm/kvm_main.c:2504:29: error: ‘struct kvm_vcpu_stat’ has no member named ‘generic’
        
        'pat': "(.*error: ‘struct )([a-zA-Z_][a-zA-Z0-9_]*)(’ has no member named ‘)([a-zA-Z_][a-zA-Z0-9_]*)(.*)",
            'groups' : [2, 4]
    },
    're_decl_enum' : {
        'pat' :"(.*error: redeclaration of ‘enum )([a-zA-Z_][a-zA-Z0-9_]*).*",
        'groups' : [2]
        },
    're_decl_enumeratior' : {
        'pat' : "(.*error: redeclaration of enumerator ‘)([a-zA-Z_][a-zA-Z0-9_]*)’.*",
        'groups' : [2]
        },
    'undecl_here' : {
        'pat' : "(.*error: ‘)([a-zA-Z_][a-zA-Z0-9_]*)’ undeclared here.*",
        'groups' : [2]
        },
    'invld_use_undef_type' : {
        'pat' : "(.*error: invalid use of undefined type ‘)(.*)’.*",
        'groups' : [2]
        },
    'undecl' : {
        'pat' : "(.*error: ‘)(.*)’ undeclared.*",
        'groups' : [2]
        },
    'void_not_ignored' : {
        'pat' : ".*void value not ignored as it ought to be",
        'group' : None,
        'dont-care' : True
        },
    'stat_non_stat' : {
        'pat' : ".*static declaration of.*follows non-static declaration",
        'group' : None,
        'dont-care' : True
        },
    'conflicting_types' : {
        'pat' : ".*error: conflicting types for.*",
        'group' : None,
        'dont-care' : True
        },
    'XXX3' : {
        'pat' : "",
        'group' : None,
        'dont-care' : True
        },
    'XXX3' : {
        'pat' : "",
        'group' : None,
        'dont-care' : True
        },
}

def extract_symbols(lines, pat_name, pat):
    syms = list()
    matched = list()
    
    for l in lines:
        match = re.search(pat['pat'], l)
        if match:
            if 'dont-care' in pat:
                matched.append(l)
            else:
                if not pat['groups'] is None:
                    groups = pat['groups']
                    syms.append({
                        'tag' : ','.join([match.group(x) for x in groups]),
                        'type' : pat_name,
                        'provided-by' : [],
                        'pat' : pat,
                        'line' : l})
                        
                matched.append(l)

    return (syms, matched)

def report_unmatched_errors(errors):
    if len(errors) == 0: return

    print("\n*** UNMATCHED ERRORS ***\n")
    
    for error in errors: print(error)

def uniqify_dict_list(L, key):
    seen = {}
    unq = []
    
    for d in L:
        tag = d[key]
        if tag not in seen:
            seen[key] = d
            unq.append(d)
    return unq


def _get_needed_symbols(lines, state):
    syms = list()
    errors = [line for line in lines if re.search('.*error: .*', line)]
    
    for key in pats.keys():
        (pat_syms, matched) = extract_symbols(errors, key, pats[key])
        syms += pat_syms
        errors = list(set(errors) - set(matched))

    syms = uniqify_dict_list(syms, tag)

    report_unmatched_errors(errors)
    state['unresolved_syms'] = syms
    state['unmatched_errors'] = errors
    save_cp(state)
    return (syms, errors)

def get_needed_symbols(state):
    print("*WARNING* proceeding will replace state for unresolved syms")
    print("and unmatched errors")
    if not confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
            return
    spew = build(state)
    _get_needed_symbols(spew, state)

def _short_display_unres_symbols(state, skip_provided):
    unres_syms = state['unresolved_syms']
    for (i, sym) in zip(range(0, len(unres_syms) , 1), unres_syms):
        if skip_provided and 'provided-by' in sym:
            if sym['provided-by']:
                continue
        print("%d: %s, %s, %s" % (i, sym['tag'], sym['type'],
                                  str(sym['provided-by'])))

def short_display_unres_symbols_all(state):
    _short_display_unres_symbols(state, False)

def short_display_unres_symbols_unprovided(state):
    _short_display_unres_symbols(state, True)

def detailed_display_unres_symbol_by_index(state):
    unres_syms = state['unresolved_syms']
    short_display_unres_symbols_unprovided(state)
    
    ix = input("enter index of unresolved symbol to for: ")
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if ix > len(unres_syms) or ix < 0:
        print_log("index %d out of range" %(ix), state)
    print_log(unres_syms[ix], state)

def set_unres_provider_by_ix(state):
    unres_syms = state['unresolved_syms']
    short_display_unres_symbols_unprovided(state)
    
    ix = input("enter index of unresolved symbol to set provider for: ")
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if ix > len(unres_syms) or ix < 0:
        print_log("index %d out of range" %(ix), state)
        
    if not confirm("are you sure?: ", ['y']):
        return
    
    sha = input("enter SHA1 id or comma separated list providing symbol <enter> if none: ")
    if not sha: return

    unres_syms[ix]['provided-by'] = sha.split(',')
    save_cp(state)

# this and prev function have bothersome amounts of duplicate code
def delete_unres_sym_by_ix(state):
    unres_syms = state['unresolved_syms']
    short_display_unres_symbols_all(state)
    
    ix = input("enter index of unresolved symbol to delete: ")
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if ix > len(unres_syms) or ix < 0:
        print_log("index %d out of range" %(ix), state)
        
    if not confirm("are you sure?: ", ['y']):
        return
    
    unres_syms.pop(ix)

def unresolved_syms_to_patch_dict_list(state):
    sha_list = []

    for s in state['unresolved_syms']:
        if 'provided-by' in s:
            sha_list += s['provided-by']
    sha_list = list(set(sha_list))
    patch_list = [make_patch_dict(state, sha) for sha in sha_list]
    return patch_list

def uniqify_list(L):
    ret = list()
    tmp = dict()
    for elt in L:
        if elt in ret:
            continue
        ret.append(elt)
    return ret
    
def uniqify_dict_list(dict_list, key_list):
    ret = list()
    tmp = dict()
    for _dict in dict_list:
        key_str = ""
        for key in key_list:
            key_str += _dict[key]
        if key in tmp:
            continue
        ret.append(_dict)
    return ret

def commit_order_in_tag_sha_list(state, tag, sha):
    slbt = state['sha_lists_by_tag']

    if tag not in slbt:
        L = git_utils.get_short_sha_list_by_tag(tag)
        slbt[tag] = L
    else:
        L = slbt[tag]

    ix = -1
    try:
        ix = len(L) - L.index(sha)
    except:
        print(f"\t\tBAD JU-JU: {tag}, {sha}")
        pdb.set_trace()
    return ix

def update_rls_tag_order_in_patch_list(patch_list, state):
    P = state['all_patches']
    max_tag = sorted([x for x in  {patch['tag'] for patch in P}])[-1]
    for _p in patch_list:
        _p['order_in_release'] = \
            int(commit_order_in_tag_sha_list(state, max_tag,
                                             _p['sha1']))
        print("ix: %d, tag:%s, sha: %s, %s" %
              ( _p['order_in_release'],  _p['tag'], _p['sha1'],
                _p['subject']))

def add_resolvd_patches_to_all_patches(state):
    L1 = list()
    syms = [sym for sym in state['unresolved_syms']]
    for sym in syms:
        shas = sym['provided-by']
        for sha in shas:
            if len(sha) > 12: # FIXME: this must be cleaned up
                sha = sha[0:12]
            L1.append(sha)
    pdb.set_trace()
    L2 = uniqify_list(L1)
    P = [make_patch_dict(state, sha) for sha in L2]
    #
    pdb.set_trace()
    for _p in P: state['all_patches'].append(_p)
    update_rls_tag_order_in_patch_list(state['all_patches'], state)
    state['all_patches'].sort(key= lambda x: x['order_in_release'])

def show_all_patches(state):
    update_rls_tag_order_in_patch_list(state['all_patches'], state)
    state['all_patches'].sort(key= lambda x: x['order_in_release'])
    L = ["%s: %s, %s" % (p['sha1'], p['tag'], p['subject'])
              for p in state['all_patches']]
    for (i, l) in zip(range(0, len(L)), L):
        print(str(i) + ": " +l)
        
