#!/usr/bin/python3

#
# ocos_analysis.py --vendor_tree_path=~/wrk/amd/OpenCloudOS-Kernel --vendor_branch=5.4.119-20.0009.30.spr.0001 --upstream_tree_path=/home/evantass/wrk/amd/linux.git
#

#their modules
import argparse
import pdb

#our modules
import git_utils as git
import meta_git as mg

def report_stats_short(stats_by_tag):
    print("\n=============== quick stats ===============\n")
    for key in stats_by_tag.keys():
        print("%s: %d" % (key, len(stats_by_tag[key])))
    print("\n========================================\n")

def report_stats_long(stats_by_tag):
    print("\n=============== details  ===============\n")
    for key in stats_by_tag.keys():
        print(key)
        for s in stats_by_tag[key]:
            print("\t" + s)
        print("\n")
    print("\n========================================\n")

def main():        
    vendor_subject_list = git.log_sync(args.vendor_tree_path, args.vendor_branch, "'%s'")
    upstream_subj_to_sha_hash = git.subj_to_sha_list_hash(args.upstream_tree_path,
                                                      args.upstream_branch)
    stats_by_tag = dict()
    stats_by_tag['key error'] = list()

    if not upstream_subj_to_sha_hash:
        sys.exit("FATAL: upstream_subj_to_sha_hash is None")

    count = 0
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
            print("%s, %s" % (subj, tag))
        count += 1
        if count == 200:
            report_stats_short(stats_by_tag)
            count = 0

    report_stats_short(stats_by_tag)
    report_stats_long(stats_by_tag)

    
parser = argparse.ArgumentParser()

parser.add_argument('--upstream_tree_path', help='path to upstream_git_tree')
parser.add_argument('--upstream_branch', help='upstream branch')
parser.add_argument('--vendor_tree_path', help='path to vendor_git_tree')
parser.add_argument('--vendor_branch', help='vendor branch')

# Parse the command line arguments
args = parser.parse_args()
main()

