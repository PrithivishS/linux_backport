#unresolved defense

import all_patches as ap
import persist

pats = { #: @unres_syms
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

def extract_symbols(lines, pat_name, pat):#: @unres_syms
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

def report_unmatched_errors(errors):#: @unres_syms
    if len(errors) == 0: return

    print("\n*** UNMATCHED ERRORS ***\n")
    
    for error in errors: print(error)

def _get_needed_symbols(lines, state):#: @unres_syms
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
    persist.save_cp(state)
    return (syms, errors)

def get_needed_symbols(state):#: @unres_syms
    print("*WARNING* proceeding will replace state for unresolved syms")
    print("and unmatched errors")
    if not ui.confirm("Enter 'y' to proceed, else <enter>: ", ['y']):
            return
    spew = build(state)
    _get_needed_symbols(spew, state)

def _short_display_unres_symbols(state, skip_provided):#: @unres_syms
    unres_syms = state['unresolved_syms']
    for (i, sym) in zip(range(0, len(unres_syms) , 1), unres_syms):
        if skip_provided and 'provided-by' in sym:
            if sym['provided-by']:
                continue
        print("%d: %s, %s, %s" % (i, sym['tag'], sym['type'],
                                  str(sym['provided-by'])))

def short_display_unres_symbols_all(state):#: @unres_syms
    _short_display_unres_symbols(state, False)

def short_display_unres_symbols_unprovided(state):#: @unres_syms
    _short_display_unres_symbols(state, True)

def detailed_display_unres_symbol_by_index(state):#: @unres_syms
    unres_syms = state['unresolved_syms']
    short_display_unres_symbols_unprovided(state)
    
    ix = input("enter index of unresolved symbol to for: ")
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if ix > len(unres_syms) or ix < 0:
        pl.print_log("index %d out of range" %(ix), state)
    pl.print_log(unres_syms[ix], state)

def set_unres_provider_by_ix(state):#: unres_syms
    unres_syms = state['unresolved_syms']
    short_display_unres_symbols_unprovided(state)
    
    ix = input("enter index of unresolved symbol to set provider for: ")
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if ix > len(unres_syms) or ix < 0:
        pl.print_log("index %d out of range" %(ix), state)
        
    if not ui.confirm("are you sure?: ", ['y']):
        return
    
    sha = input("enter SHA1 id or comma separated list providing symbol <enter> if none: ")
    if not sha: return

    unres_syms[ix]['provided-by'] = sha.split(',')
    for sha in sha.split(','):
        ap.add_to_all_patches(state, sha)
        patch['provides_for'] = unres_syms[ix]
    ap.after_add_to_all_patches(state)

# this and prev function have bothersome amounts of duplicate code
def delete_unres_sym_by_ix(state):#: unres_syms
    unres_syms = state['unresolved_syms']
    short_display_unres_symbols_all(state)
    
    ix = input("enter index of unresolved symbol to delete: ")
    try:
        ix = int(ix)
    except:
        print("oops")
        return
    
    if ix > len(unres_syms) or ix < 0:
        pl.print_log("index %d out of range" %(ix), state)
        
    if not ui.confirm("are you sure?: ", ['y']):
        return
    
    unres_syms.pop(ix)

def unresolved_syms_to_patch_dict_list(state):#: unres_syms
    sha_list = []

    for s in state['unresolved_syms']:
        if 'provided-by' in s:
            sha_list += s['provided-by']
    sha_list = list(set(sha_list))
    patch_list = [make_patch_dict(state, sha) for sha in sha_list]
    return patch_list

