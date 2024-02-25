#!/bin/bash
#
#
# input is a file of output from show unresolved symbols
#
# ex:
#
# 4: lockdep_hardirqs_on_prepare, undecl-fn, []
# 5: context_tracking_guest_exit, undecl-fn, []
# 6: vtime_account_guest_exit, undecl-fn, []
#

date

for sym in `cat $1 | awk '{print $2}' | sed 's/,.*$//'`
do
    date
    echo "==== $sym ==="
    for sha in "`git log -G${sym} --pretty=tformat:'%<(10) %h' v4.1..v6.2`"
    do
	echo "== $sha =="
	git show $sha |grep $sym
    done
done    
