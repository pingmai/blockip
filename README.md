# blockip.py
block ssh probes that show up in auth.log as 'Invalid user xxxx from [ip]'

Plan:
- generalize this to use a config file e.g. /etc/blockip:
'''
#logfile          #hours  #maxAttempts  #pf_table #pattern
/var/log/auth.log 2       3             blocked1d "Invalid user .* from"
/var/log/maillog  1       1             blocked3d "Rejected"
'''


