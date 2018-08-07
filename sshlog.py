#!/usr/local/bin/python3.7

import datetime
import subprocess
import argparse
import re
import os

parser = argparse.ArgumentParser(
	description='''search LOGFILE for \'Invalid user\' ssh attempts.
if there are MAX failures within the past HOURS, block source IP in pf TABLE.
''',
	formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
	'-H',
	'--hours',
	default="2",
	type=int,
	help='past hours'
)
parser.add_argument(
	'-l',
	'--logfile',
	default="/var/log/auth.log",
	help='sshd auth.log'
)
parser.add_argument(
	'-m',
	'--max',
	default="3",
	type=int,
	help='maximum failed attempts'
)
parser.add_argument(
	'-t',
	'--table',
	default="blocked3d",
	help='pf table'
)
args = parser.parse_args()

ctime = datetime.datetime.now()
earliest = datetime.datetime.now() - datetime.timedelta(hours=args.hours)

euid = os.geteuid()

if euid == 0:
	cmd='pfctl -t %s -T show' % (args.table)
	existed = subprocess.check_output(cmd.split()).decode().strip().split()

ips = {}

for line in open(args.logfile,'r'):
	r = re.search('^(\S+\s+\S+\s+\S+).+Invalid user \S+ from ([0-9\.]+) port',line)
	if not r:
		continue
	if r.lastindex != 2:
		continue
	timestamp = datetime.datetime.strptime(str(ctime.year) + 
		r.group(1),'%Y%b %d %H:%M:%S')
	if timestamp > ctime:
		timestamp = timestamp.replace(year = ctime.year - 1)
	if timestamp < earliest:
		continue
	ip = r.group(2)
	if euid == 0 and ip in existed:
		continue
	if ip in ips:
		ips[ip] += 1
	else:
		ips[ip] = 1

for ip, count in ips.items():
	if count >= args.max:
		cmd = 'pfctl -t %s -T add %s' % (args.table, ip) 
		print(cmd)
		if euid == 0:
			subprocess.run(cmd.split())
