# operations that modify or iterate over the whole list of patches
#

import patch
import print_log as pl
import pdb
import ui
import git_utils as git
import persist

def invalidate_patches_if_new_precedents(state):#: @core, @patch_list
    state['all_patches'].sort(key= lambda x: x['order_in_release'])
    invalidate = False
    for patch in state['all_patches']:
        if not patch['downstream']: invalidate = True
        if invalidate:
            patch['prev_downstream'] = patch['downstream']
            patch['downstream'] = None
        
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
        
    _patch = patch.make_patch_dict(state, reset_to_sha)
    patch.print_dict("\n", _patch, state)
    if ui.confirm("about to reset --hard to this commit\nEnter 'y' to proceed, else <enter>: ", ['y']):
        return
    if git.git_top_of_applied_stack_sha(state) != state['first_commit']:
        git.git_reset_hard(reset_to_sha, state)
    
def add_to_all_patches(patch,state): #: @patch-list
    state['all_patches'].append(patch)
    state['sha_to_patch'] = {p['sha1'] : p for p in state['all_patches']}

def after_add_to_all_patches(state):#: @patch-list
    invalidate_patches_if_new_precedents(state)
    reset_branch_to_last_commit_not_preceding_invalidated(state)
    persist.save_cp(state)

def add_to_all_patches_by_sha(state):#: @patch-list
     sha = input("enter SHA1 id or comma separated list providing symbol <enter> if none: ")
     if not sha: return
    
     for sha in sha.split(','):
         patch = make_patch_dict(state, sha)
         add_to_all_patches(patch, state)
         
     after_add_to_all_patches(state)
     
def update_rls_tag_order_in_patch_list(patch_list, state):#: @meta-git
    P = state['all_patches']
    max_tag = sorted([x for x in  {patch['tag'] for patch in P}])[-1]
    for _p in patch_list:
        _p['order_in_release'] = \
            int(patch.commit_order_in_tag_sha_list(state, max_tag,
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
    
def add_commits_touching_file_to_all_patches(patch, file, state):

    # FIXME: this is currently dead code but shouldn't be
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

def unapplied_patches(state): #: @patch_list
    pl.print_log("@@how_unapplied_patches", state)
    L = [p for p in state['all_patches'] if not p['downstream']]
    patch.print_list("", L, state)
    return L

