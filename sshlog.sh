#!/bin/sh -f
#
# Check 'Invalid user' attempts on sshd in auth.log (LOGFILE).
# If there are more than 5 (MAX_TRY) failed attempts within
# the last hour (EARLIEST), source ip is added to PF_TABLE table in pf
#
MAX_TRY=3
LOGFILE=/var/log/clients/ftp.pinelake.stepnet.com/auth.log
# last 24 hour
EARLIEST=`date -v-24H +%s`
PF_TABLE=blocked3d

tmpfile=`mktemp`
trap 'rm -f $tmpfile' EXIT
pfctl -t $PF_TABLE -T show > $tmpfile

grep "Invalid user" $LOGFILE | while read d0 d1 d2 rest; do
	timestamp=`date -j -f "%b %d %H:%M:%S" "$d0 $d1 $d2" +%s`
	test $timestamp -lt $EARLIEST && continue
	echo $rest | cut -d ":" -f2- | cut -d " " -f6
done | sort | uniq -c | while read count ip; do
	test $count -lt $MAX_TRY && continue
	grep -q $ip $tmpfile || pfctl -t $PF_TABLE -T add $ip
done
