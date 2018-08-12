#!/usr/local/bin/python3.7

import datetime
import subprocess
import argparse
import re
import os

parser = argparse.ArgumentParser(
	description='''search LOGFILE for rejected mail attempts.
if there are MAX failures within the past HOURS, block source IP in pf TABLE.
''',
	formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
	'-f',
	'--config_file',
	default="/etc/blockip",
	help='configuration file'
)
parser.add_argument(
	'-a',
	'--archive_dir',
	help='archive directory of older logs'
)
args = parser.parse_args()
euid = os.geteuid()

#file				failure	table	search_string
#/var/log/auth.log	3/1H	blocked	Invalid user \w+ from

class config():
	def __init__(self,configfile):
		try:
			lineno = 0
			errors = {}
			for line in open(configfile,'r'):
				lineno += 1
				l = re.sub('#.*$', '', line)
				if not l.strip():
					continue
				entry = {}
				a = l.split(maxsplit=4)
				if len(a) != 4:
					errors[lineno] = 'insufficent number of parameters'
					continue
				file,rate,table,filter = a

				# file
				if os.access(file, os.R_OK):
					entry['file'] = file
				else:
					errors[lineno] = 'cannot read file ' . file
					continue
				rate = rate.split('/')
				if len(rate) != 2:
					errors[lineno] = 'invalid rate'
					continue

				# rate
				max = rate[0]
				if max.isdigit():
					entry['max'] = int(max)
				else:
					errors[lineno] = 'invalid max rate'
					continue
				interval = rate[1]
#				rx = re.compile(r'((?P<hours>\d+?)H)?((?P<minutes>\d+?)M)?' \
#					r'((?P<seconds>\d+?)S)?',re.I)
				rx = re.compile(r'((?P<hours>\d+)H)?((?P<minutes>\d+)M)?' \
					r'((?P<seconds>\d+)S)?',re.I)
				res = re.match(rx,interval)
				if not res.lastindex:
					error[lineno] = 'invalid interval'
					continue
				res = res.groupdict()
				timep = {}
				for k,v in res.items():
					if v:
						timep[k] = int(v)
				# timedelta( hours = x, minutes = y, seconds = z )
				entry['interval'] = timedelta(**timep)

				# table
				if euid == 0:
	    			cmd='pfctl -s Tables'
				    tables = subprocess.check_output(cmd.split()).decode()\
						.split()
					if table not in tables:
						error[lineno] = 'cannot find table '.table
						continue
				entry['table'] = table
				
				entry['filter'] = filter

		except IOError:
			print("could not read file %s" % configfile)
	

ctime = datetime.datetime.now()
earliest = datetime.datetime.now() - datetime.timedelta(hours=args.hours)

if euid == 0:
    cmd='pfctl -t %s -T show' % (args.table)
    existed = subprocess.check_output(cmd.split()).decode().strip().split()

for line in open(args.config_file,'r'):
ips = {}
reIp = r"((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"\
           r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))"
reTimestamp=r"(\w\w\w\s+\d+\s+\d\d:\d\d:\d\d)"

rePattern = '^' + reTimestamp + '.*reject=554 5.7.1 Rejected\s+' + reIp + \
	'\s+found in'

#import pdb; pdb.set_trace()

for line in open(args.logfile,'r'):
	r = re.search(rePattern,line)
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
