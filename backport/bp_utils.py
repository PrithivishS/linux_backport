import pdb
import pickle
import sys
import importlib
from git_utils import *
import git_utils
from datetime import datetime
import select
import shutil
import shlex
import tempfile
import difflib
from packaging import version
import print_log as pl
import state_access
import persist
import patch
import menu_util as mu
import meta_git as mg
import shell_util as su
    
def prompt_to_set_or_alter_dict_val(key, d): #: core, @io, @ui, @state, @persist
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
#@@@

def backport_patches(state, menu_item_list): #: @core, @MAIN, @workflow
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pl.print_log("Startup: Current Time = %s" %(current_date_time), state)

    mu.do_menu_choice(menu_item_list, state)
        
def uniqify_dict_list(L, key):#: @unres_syms
    seen = {}
    unq = []
    
    for d in L:
        tag = d[key]
        if tag not in seen:
            seen[key] = d
            unq.append(d)
    return unq


def invalidate_patches_if_new_precedents(state):#: @core, @patch_list
    state['all_patches'].sort(key= lambda x: x['order_in_release'])
    invalidate = False
    for patch in state['all_patches']:
        if not patch['downstream']: invalidate = True
        if invalidate:
            patch['prev_downstream'] = patch['downstream']
            patch['downstream'] = None
        
def git_reset_hard(sha1, state): #: @misplaced, @base-git
    cmd = "git  reset --hard  " + sha1
    print("about to: " + cmd)
    
    if not ui.confirm("\nEnter 'y' to proceed, else <enter>: ", ['y']):
        return -1

    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)

    return result.returncode
    
def reset_branch_to_last_commit_not_preceding_invalidated(state):#: meta-git
    # look for the last "applied" patchdownstream set) not followed by a commit
    # with downstream == None
    #
    # if there are no such patches, then use the base commit 
    #
    # that is the commit that we want to reset the branch to
    #
    # MUST call invalidate_patches_if_new_precedents() before calling this
    #      function

    first_unapplied_patch = [ p for p in state['all_patches']
                              if not p['downstream']][0]

    if first_unapplied_patch == state['all_patches'][0]:
        reset_to_sha = state['first_commit']
    else:
        ix = state['all_patches'].index(first_unapplied_patch)
        reset_to_sha = state['all_patches'][ix - 1]['sha1']
        
    patch = make_patch_dict(state, reset_to_sha)
    patch.print_dict("\n", patch, state)
    if ui.confirm("about to reset --hard to this commit\nEnter 'y' to proceed, else <enter>: ", ['y']):
        return
    if git_top_of_applied_stack_sha(state) != state['first_commit']:
        git_reset_hard(reset_to_sha, state)
    
def add_to_all_patches(patch,state): #: @patch-list
    state['all_patches'].append(patch)
    state['sha_to_patch'] = {p['sha1'] : p for p in state['all_patches']}

def after_add_to_all_patches(state):#: @patch-list
    pdb.set_trace()
    invalidate_patches_if_new_precedents(state)
    reset_branch_to_last_commit_not_preceding_invalidated(state)
    reset_branch_to_last_commit_not_preceding_invalidated(state)         
    save_cp(state)

def add_to_all_patches_by_sha(state):#: @patch-list
     sha = input("enter SHA1 id or comma separated list providing symbol <enter> if none: ")
     if not sha: return
    
     for sha in sha.split(','):
         patch = make_patch_dict(state, sha)
         add_to_all_patches(patch, state)
         
     after_add_to_all_patches(state)
     
   
def uniqify_list(L): #: @core, @generic
    ret = list()
    tmp = dict()
    for elt in L:
        if elt in ret:
            continue
        ret.append(elt)
    return ret
    
def uniqify_dict_list(dict_list, key_list): #: @core, @generic
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

def commit_order_in_tag_sha_list(state, tag, sha):#: @meta-git
    if not tag: return -1
    slbt = state['sha_lists_by_tag']
    if not slbt:
        print(f"sha_lists_by_tag not in state: {tag}")
        state['sha_lists_by_tag'] = dict()
        slbt = state['sha_lists_by_tag']

    if tag not in slbt:
        L = git_utils.get_short_sha_list_by_key(tag)
        slbt[tag] = L
    else:
        L = slbt[tag]

    try:
        ix = len(L) - L.index(sha)
    except:
        print(f"CAN'T FIND RELEASE CONTAINING {sha}")
        return -1
    return ix

def update_rls_tag_order_in_patch_list(patch_list, state):#: @meta-git
    P = state['all_patches']
    max_tag = sorted([x for x in  {patch['tag'] for patch in P}])[-1]
    for _p in patch_list:
        _p['order_in_release'] = \
            int(commit_order_in_tag_sha_list(state, max_tag,
                                             _p['sha1']))
def show_all_patches(state):#: patch_list
    update_rls_tag_order_in_patch_list(state['all_patches'], state)
    state['all_patches'].sort(key= lambda x: x['order_in_release'])
    patch.print_list("all patches", state['all_patches'], state)
        
def del_from_all_patches(sha, state):#: patch_list
    
    sha = sha[:12] #FIXME we need to do this in one place and one place only
    try:
        patch = state['sha_to_patch'][sha]
        print("found it")
    except:
        print("could not find patch with sha %s\n" % (sha))
    state['all_patches'].remove(patch)
    del state['sha_to_patch'][sha]
    
def experimental_feature_enabled(state, name):#: @bsolete, @nuke
    msg = "no soup for you: %s" % (name)
    try:
        if state['experimental'][name]:
            return True
        print(msg)
        return False
    except:
        print(msg)
        return False

def test(state):#: @bsolete, @nuke
    pdb.set_trace()
    pass

def start_backport(state):#: @unclear?, @workflow
    if not git_utils.git_repo_is_clean():
        pl.print_log("repo is not clean. bailing out", state)
        return
    if state['backport_in_progress']:
        print("OOPS: backport already in progress")
        return

    state['backport_in_progress'] = True
    git_utils.next_branch(state)
    git_reset_hard(state['first_commit'], state)

def restart_backport(state):#: @unclear?, @workflow
    if active_cherry_pick_sha(state):
        git_cherry_pick_abort()

    state['backport_in_progress'] = False
    git_utils.next_branch(state)
    git_reset_hard(state['first_commit'], state)
    start_backport(state)

def active_cherry_pick_sha(state):#: @meta_git
    # parse git status and find sha we're cherry_picking
    (ret, classic_status) = su.shell_cmd("git status")
    (ret, porcelain_status) = su.shell_cmd("git status --porcelain")

    classic_pat = "(.*cherry-picking commit )([a-fA-F0-9]+)(.*)"
    match = re.search(classic_pat, classic_status)
    try:
        cherry_pick_sha = match.group(2)
        return cherry_pick_sha
    except:
        return None
    
def generate_blame_files(sha, file, state):#: @meta_git, @workflow?
    dir = state['cherry_pick_files'] + '/' + sha
    fbase = os.path.split(file)[1]
    for _sha in ['HEAD', sha]:
        for sfx in  ['^', '']:
            SHA = _sha + sfx
            cmd = f"git blame {SHA} -- {file} > {dir}/{SHA}.{fbase}"
            print(cmd)
            su.shell_cmd(cmd)

def show_patch(cherry_pick_sha, file, state):#: @patch
    cmd = "git show %s:%s > %s/%s/%s" % (cherry_pick_sha, file,
                                         state['cherry_pick_files'],
                                         cherry_pick_sha,

                                         os.path.split(file)[1])
    su.shell_cmd(cmd)
    
def generate_conflict_resolution_files(cherry_pick_sha, file, state):#: @workflow
    show_patch(cherry_pick_sha, file, state)
    generate_blame_files(cherry_pick_sha, file, state)

def get_sorted_patch_list_from_sha_list(patch, file, state):#: meta_git
    min = state['git_log_min_tag']
    max = patch['sha1']
    cmd = f"git log --pretty=tformat:'%h' {min}..{max} {file}"
    (ret, out) = su.shell_cmd(cmd)
    sha_list = uniqify_list(out.split("\n"))[:-1]
    patch_list = [make_patch_dict(state, sha) for sha in sha_list]
    patch_list.sort(key= lambda x: x['order_in_release'])
    patch.print_list("", patch_list, state)
    return patch_list

def add_commits_touching_file_to_all_patches(patch, file, state): #: @workflow
    patch_list = get_sorted_patch_list_from_sha_list(patch, file, state)
    prompt_every_time = True
    ix = 0
    
    for patch in patch_list:
        sha = patch['sha1']
        if sha not in state['all_patches']:
            p = make_patch_dict(state, sha)
            # confirm if they want this commit
            if prompt_every_time:
                prompt = get_menu_trailer(state)
                prompt += "\n==== pre-requisite review(%d/%d): %s ===\n" % (
                    ix, len(patch_list), file)
                prompt += patch_dict_to_string("", p, state)
                prompt += "add to patch list??\n"
                prompt += "\t'y': add this patch\n"
                prompt += "\t'*': add this and following patches\n"
                prompt += "\t'!': DONT add this or following patches\n"
                prompt += "\n"
                ans = ui.confirm(prompt, ['y', '*', '!' ])
                ix += 1
                if not ans:
                    continue
                if ans == "*":
                    prompt_every_time = False
                if ans == "!":
                    return
            patch_list.append(p)

    patch.print_list("", patch_list, state)
    print("ABOUT TO ENTER THESE %d PATCHES IN state['all_patches']" %
          len(patch_list))

    if not ui.confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    
    for p in patch_list:
        add_to_all_patches(p, state)

    if active_cherry_pick_sha(state):
        git_cherry_pick_abort()
        
    after_add_to_all_patches(state)

    return out

def parse_cherry_pick_conflict(state): #: @meta_git
    cp_sha = active_cherry_pick_sha(state)
    if not cp_sha:
        pl.print_log("no active cherry-pick", state)
        return (None, None, None)
         
    cp_patch = state['sha_to_patch'][cp_sha]        

    # parse git status --porcelain
    (ret, porcelain_status) = su.shell_cmd("git status --porcelain")
    mod_files = []
    both_mod_files = []
    for line in porcelain_status.split("\n")[: -1]:
        (code, file) = [x for x in line.split(' ') if not x == '']
        if code == 'M': mod_files.append(file)
        if code == 'UU': both_mod_files.append(file)

    return (cp_patch, both_mod_files, mod_files)

def show_stuff_for_conflict_resolution(state):#: @workflow
    (cp_patch,
     both_mod_files,
     mod_files) = parse_cherry_pick_conflict(state)

    if not cp_patch:
        return
    
    cp_sha = cp_patch['sha1']
    
    # clean tmp dir
    su.shell_cmd("mkdir -p " + state['cherry_pick_files'] + "/" + cp_sha)
    
    # emit patch to temp dir
    cmd = "git show %s > %s/%s/patch" % (cp_sha,
                                         state['cherry_pick_files'],
                                         cp_sha)
    su.shell_cmd(cmd)
    
    # emit both_mod files to "both_mod.".filename
    for file in both_mod_files:
        generate_conflict_resolution_files(cp_sha, file, state)

def cherry_pick_by_sha(state, cp_sha):#: @meta_git
    pl.print_log("@@cherry_pick_by_sha", state)
    pdb.set_trace()
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
    save_cp(state)
    
def cherry_pick_complete(state, patch):#: @meta_git
    patch['prev_downstream'] = patch['downstream']
    patch['downstream'] = git_top_of_applied_stack_sha(state)
    state['downstream_sha_to_patch'][patch['downstream']] = patch
    build(state)
    
def try_to_reuse_old_conflict_resolution(patch, state): #: @workflow
    if not active_cherry_pick_sha(state):
        # we can't use a prev resolution if there is no conflict
        # and we can't have a conflict if not in cherry-pick
        return False
    
    patch['prev_conflicts'] = patch['conflicts']
    patch['conflicts'] = git_get_conflicts()

    if (patch['prev_downstream'] and
        patch['conflicts'] == patch['prev_conflicts']):
        pdb.set_trace() #FIXME
        # abort current cherry pick
        git_cherry_pick_abort()
        # cherry-pick prev downstream
        cherry_pick_by_sha(patch['prev_downstream'])
                           
        if git_repo_is_clean():
            return True
        else:
            return False

    else:
        return False # can't use old resolution
        
def apply_next_patch(state):#: @workflow, @rename:cherry_pick_next_patch
    pl.print_log("@@apply_next_patch", state)
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    L = [p for p in state['all_patches'] if not p['downstream']]
    if len(L) == 0:
        pl.print_log("THERE ARE NO PATCHES TO APPLY", state)
        return
    patch = L[0]

    patch.print_dict("@@ cherry picking :", patch, state)
    git_cherry_pick(patch['sha1'])
    
    if git_repo_is_clean():
        cherry_pick_complete(state, patch)
    else:
        show_stuff_for_conflict_resolution(state)
        if try_to_reuse_old_conflict_resolution(patch, state):
            cherry_pick_complete(state, patch)
    save_cp(state)

def unapplied_patches(state): #: @patch_list
    pl.print_log("@@how_unapplied_patches", state)
    L = [p for p in state['all_patches'] if not p['downstream']]
    patch.print_list("", L, state)
    return L

def do_pdb(state): #: @util
    pl.print_log("@@pdb", state)
    pdb.set_trace()

def checkpoint(state): #: @util
    pl.print_log("@@checkpoint", state)
    save_cp(state)

def pop_branch_tos(state): #: @obsolete?
    pl.print_log("@@do_pop_branch_tos", state)
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    git_utils.git_pop_branch_tos_stack()
    short_git_log(state)

def short_git_log(state): #: @meta_git
    pl.print_log("@@how_short_git_log", state)
    git_short_log('%<(10) %h  %<(12) %an : %s', state)

def bash(state): #: @util
    pl.print_log("@@bash", state)
    subprocess.run(['bash'])

def log_note(state): #: @util
    pl.print_log("@@log_note", state)
    s = input("enter text to be appended to the log: ")
    pl.print_log(s, state)

def patch_info(state): #: @workflow
    pl.print_log("@@patch_info", state)
    mg.prompted_show_sha_info(state)

def backup_branch(state): #: @workflow
    pl.print_log("@@backup_branch", state)
    line_fn = lambda line, state: pl.print_log(line, state)
    prompt_to_set_or_alter_dict_val('branch_backup_cmd', state)
    if not state['branch_backup_cmd']:
        return

    # do it
    cmd = "git " + ' '.join(state['branch_backup_cmd'].split(' ')[1:])
    out = su.shell_cmd(cmd)
    pl.print_log(out, state)

def unapply_branch_tos(state): #: @obsolete
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        
    if not ui.confirm("Are you sure? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

    sha = git_top_of_applied_stack_sha(state)
    patch = state['downstream_sha_to_patch']
    downstream_sha = patch['downstream']
    patch['downstream'] = None
    del state['downstream_sha_to_patch'][downstream_sha]

    git_utils.git_pop_branch_tos()
    del state['downstream_sha_to_patch'][downstream_sha]

    return

def add_sha_list_to_all_patches(state): #: @workflow, @patch_list
    pl.print_log("@@add_sha_list_to_all_patches", state)
    if not git_repo_is_clean():
        pl.print_log("git status not clean. no changes made", state)
        return
    if not ui.confirm("Are you sure you don't need to pop top applied patch? Enter 'y' if ok, else <enter>: ", ['y']):
    	return

     # get the name of the sha file
    print("enter the path of a file containing one sha per line <enter> if none")
    sha_file = input("sha_file: ")
    if not sha_file: return

    patches = import_sha_list_file(sha_file, state)
    for patch in import_sha_list_file(sha_file, state):
        add_to_all_patches(patch, state)
    after_add_to_all_patches(state)

def cherry_pick_continue(state):#: @workflow
    cherry_pick_sha = active_cherry_pick_sha(state)
    if not cherry_pick_sha:
        pl.print_log("No cherry-pick in progress. can't cherry-pick --continue",
                  state)
        return
    patch = state['sha_to_patch'][cherry_pick_sha]
    pl.print_log("@@cherry_pick_continue", state)
    git_cherry_pick_continue()
    if git_repo_is_clean():
        downstream_sha = git_top_of_applied_stack_sha(state)
        patch['downstream'] = downstream_sha
        state['downstream_sha_to_patch'][downstream_sha] = patch
        plh = state['patch_list_history']
        plh.append(list())
        plhe = plh[-1]
        for patch in state['all_patches']:
            plhe.append(patch)

def cherry_pick_abort(state):#: @workflow
    pl.print_log("@@cherry_pick_abort", state)
    if git_repo_is_clean():
        pl.print_log("repo is clean. can't cherry-pick --abort", state)
        return
    if not ui.confirm("enter 'y' if ok, else <enter>: ", ['y']):
    	return
    if not ui.confirm("enter 'y' if you're really really sure, else <enter>: ", ['y']):
    	return
    git_cherry_pick_abort()

def show_top_unapp(state): #: obsolete?
    patch.print_list("", unapplied_patches(state)[:1], state)

def show_patch_by_sha(state): #: @git
    sha = input("enter sha of patch to be shown: ")
    (ret, output) = su.shell_cmd("git show " + sha)
    pl.print_log(output, state)

def shell_one_liner(state): #: @util
    cmd = input("enter shell one liner<enter to cancel>: ")
    (ret, output) = su.shell_cmd(cmd)
    pl.print_log(output, state)

def git_status_log(state): #: @obsolete
    s = git_utils.git_status(state)
    
def do_git_status(state): #: @meta_git
    s = git_status()
    pl.print_log(s, state)

def get_log_result_key_by_index(state): #: workflow
    keys = state['git_log_results'].keys()
    keys_l = list(keys)
    
    for (key, i) in zip(keys, range(len(keys))):
        print(str(i) + ":" + key)
        
    ix = input("enter index <enter to return>: ")
    if not ix:
        return
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if i > len(keys) or ix < 0:
        return
          
    key = keys_l[ix]
    return key
    
def show_one_log_result(state): #: workflow
    key = get_log_result_key_by_index(state)
    if not key: return
    
    pl.print_log("==== %s ====" % (key), state)
    
    sha_out_list = state['git_log_results'][key]
    for sha in sha_out_list.keys():
        _d = make_patch_dict(state,sha)
        pl.print_log("== %s ==" % (sha_to_patch_string(state, sha)), state)
        out = clip_long_output(sha_out_list[sha], state)
        pl.print_log(out, state)

def delete_one_log_result(state): #: workflow
    key = get_log_result_key_by_index(state)
    if not key: return
    
    pl.print_log("==== %s ====" % (key), state)
    
    del state['git_log_results'][key]

    
def hackery(state):#: obsolete
    for patch in state['all_patches']:
        patch['conflicts'] = None
        patch['prev_conflicts'] = None
        patch['downstream'] = None
        patch['prev_downstream'] = None
        
def both_mod_commits(state):#: @workflow
    (cp_patch,
     both_mod_files,
     mod_files) = parse_cherry_pick_conflict(state)

    if not cp_patch:
        return

    for file in both_mod_files:
        add_commits_touching_file_to_all_patches(cp_patch, file, state)
