# blockip
block ssh probes that show up in auth.log as 'Invalid user xxxx from [ip]'
offending ip are added to pf tables and blocked.  daily cron jobs expires
entries that are older than n days:
```
pfctl -t blocked1d -T expire 86400
pfctl -t blocked3d -T expire 259200
```

Plan:
- generalize this to use a config file e.g. /etc/blockip:
```
#logfile          #hours  #maxAttempts  #pf_table #pattern
/var/log/auth.log 2       3             blocked1d "Invalid user .* from"
/var/log/maillog  1       1             blocked3d "Rejected"
```

for now these are separate scripts.  they are meant to be invoke from cron:
```
*/11    *       *       *       *       root    /home/ping/bin/sshlog.py -t blocked3d -m 2
*/7     *       *       *       *       root    /home/ping/bin/maillog.py -t blocked3d > /dev/null 2>&1
```

command line options:
```
[2050]ping@xmxwest1:~$ bin/sshlog.py -h
usage: sshlog.py [-h] [-H HOURS] [-l LOGFILE] [-m MAX] [-t TABLE]

search LOGFILE for 'Invalid user' ssh attempts. if there are MAX failures
within the past HOURS, block source IP in pf TABLE.

optional arguments:
  -h, --help            show this help message and exit
  -H HOURS, --hours HOURS
                        past hours (default: 2)
  -l LOGFILE, --logfile LOGFILE
                        sshd auth.log (default: /var/log/auth.log)
  -m MAX, --max MAX     maximum failed attempts (default: 3)
  -t TABLE, --table TABLE
                        pf table (default: blocked3d)
[2051]ping@xmxwest1:~$ bin/maillog.py -h
usage: maillog.py [-h] [-H HOURS] [-l LOGFILE] [-m MAX] [-t TABLE]

search LOGFILE for rejected mail attempts. if there are MAX failures within
the past HOURS, block source IP in pf TABLE.

optional arguments:
  -h, --help            show this help message and exit
  -H HOURS, --hours HOURS
                        past hours (default: 2)
  -l LOGFILE, --logfile LOGFILE
                        sendmail log (default: /var/log/maillog)
  -m MAX, --max MAX     maximum failed attempts (default: 1)
  -t TABLE, --table TABLE
                        pf table (default: blocked1d)
```



