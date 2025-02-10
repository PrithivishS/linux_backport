#!/usr/bin/python3

import os
import subprocess
import sys
import pdb
import pickle

# DONT USE PRINT UNLESS UNAVOIDABLE

def emit(msg):
    print("## %s: %s" % (sys.argv[0], msg))

def exit(val):
    sys.exit(val)

def argc():
    return len(sys.argv)

def argv(index):
    return sys.argv[index]

def show_args():
    emit("##: hook: %s" % (sys.argv[1:]))

def sha_expr_to_sha(sha_expr): #ex: HEAD~5, HEAD^, <sha_id>^, ...
    result = subprocess.run("git rev-parse  HEAD",
                            shell=True, stdout=subprocess.PIPE)
    return result.stdout.decode("latin-1").strip()
   
def getenv_ifset(vbl_name):
    try:
        val = os.environ[vbl_name]
    except:
        val = None
        
def check_github_comment_preserving_hooks_enabled():
    if getenv_ifset("DISABLE_GITHUB_COMMENT_HOOKS") == 'y':
        emit("DISABLE_GITHUB_COMMENT_HOOKS set github comments not saved")
        return False
    else:
        emit("DISABLE_GITHUB_COMMENT_HOOKS not set github comments saved")
        return True

def get_sha_list(first_sha):
    result = subprocess.run("git rev-list %s^..HEAD" % (first_sha),
                            shell=True, stdout=subprocess.PIPE)
    return result.stdout.decode('latin-1').split('\n')

def get_pickle_file_name():
    return "pickle"

def load_state():
    try:
        with open(get_pickle_file_name(), 'rb') as handle:
            return pickle.load(handle)
    except:
        emit("*WARNING* cannot restore pickle file: " + fpath)

def state_file_exists():
    if os.path.exists(get_pickle_file_name()):
        return True
    else:
        return False

def save_state(state_dict):
    with open(get_pickle_file_name(), 'wb') as handle:
        pickle.dump(state_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def invoke_hook_main(main):
    if main():
        exit(0)
    else:
        exit(1)
