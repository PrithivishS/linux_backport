#!/usr/bin/python3

import pdb
import pickle
import argparse

from bp_utils import *

parser = argparse.ArgumentParser()
parser.add_argument('--pickle-path', default='/tmp/backport.pickle', help='pickle file to load')
# Parse the command line arguments
args = parser.parse_args()
state = restore_cp(args.pickle_path)
print(str(state))
print_patch_list("", state)



