#!/usr/bin/python3

#
# vendor_tree_analysis.py --vendor_tree_path=~/wrk/amd/anolis.git --vendor_branch=5.10.134-16.3 --upstream_tree_path=/home/evantass/wrk/amd/linux.git --upstream_branch=v6.8 --log-file=/home/evantass/tmp/analysis.log
#

#their modules
import argparse
import pdb
from datetime import datetime

#our modules
import git_utils as git
import meta_git as mg
import print_log as pl
import persist

def report_stats_short(stats_by_tag):
    pl.print_log("\n=============== quick stats ===============\n", state)
    for key in stats_by_tag.keys():
        pl.print_log("%s: %d" % (key, len(stats_by_tag[key])), state)
    pl.print_log("\n========================================\n", state)

def report_stats_long(stats_by_tag):
    pl.print_log("\n=============== details  ===============\n", state)
    for key in stats_by_tag.keys():
        pl.print_log(key, state)
        for s in stats_by_tag[key]:
            pl.print_log("\t" + s, state)
        pl.print_log("\n", state)
    pl.print_log("\n========================================\n", state)

def main():        
    modulus = 5000 
    vendor_subject_list = git.log_sync(args.vendor_tree_path, args.vendor_branch, "'%s'")
    upstream_subj_to_sha_hash = git.subj_to_sha_list_hash(args.upstream_tree_path,
                                                      args.upstream_branch)
    stats_by_tag = dict()
    stats_by_tag['key error'] = list()
    state['stats_by_tag'] = stats_by_tag
    t0 = datetime.now()

    if not upstream_subj_to_sha_hash:
        sys.exit("FATAL: upstream_subj_to_sha_hash is None")

    count = 0
    pl.print_log("boy howdy", state)
    for subj in vendor_subject_list:
        try:
            upstream_sha_list = upstream_subj_to_sha_hash[subj]
        except:
            stats_by_tag['key error'].append(subj)
            continue
        for us_sha in upstream_sha_list:
            tag = git.find_tag_by_sha1(us_sha, args.upstream_tree_path)
            if not tag: tag = 'tag not found'
            try:
                rec = stats_by_tag[tag]
            except:
                rec = list()
            rec.append(us_sha + ', ' + subj)
            stats_by_tag[tag] = rec
            #pl.print_log("%s, %s" % (subj, tag), state)

        count += 1
        
        if count % modulus == 0:
            t1 = datetime.now()
            dt = t1 - t0
            print("%s: %s, %f (secs/commit)" % (count,
                                                str(dt),
                                                dt.seconds / count))
            if count % (10 * modulus) == 0:
                state['last_cp_ix'] = count
                persist.save_cp(state)
                report_stats_short(stats_by_tag)

    report_stats_short(stats_by_tag)
    report_stats_long(stats_by_tag)

def state_init():
    state = dict()
    state['args'] = args
    state['pickle_dir'] = args.pickle_dir
    state['pickle_file'] = args.pickle_file
    
    try:
        state['log_fobj'] = open(args.log_file, 'a')
    except:
        pdb.set_trace()
        state['log_fobj'] = open(args.log_file, 'w')
    state['cp_num'] = 0
   
    return state

    
parser = argparse.ArgumentParser()

parser.add_argument('--upstream_tree_path', help='path to upstream_git_tree')
parser.add_argument('--upstream_branch', help='upstream branch')
parser.add_argument('--vendor_tree_path', help='path to vendor_git_tree')
parser.add_argument('--vendor_branch', help='vendor branch')
parser.add_argument('--log-file', default="/home/evantass/tmp/analysis.log",
                    help='path to log file')
parser.add_argument('--pickle-file', default='analysis.pickle',
                    help='pickle file to load')
parser.add_argument('--pickle-dir', default='/home/evantass/tmp',
                    help='where to store checkpoints')

# Parse the command line arguments
args = parser.parse_args()
state = state_init()

main()

