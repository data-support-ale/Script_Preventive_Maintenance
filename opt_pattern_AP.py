#!/usr/bin/env python3

import sys
import os

pattern = sys.argv[1]
text = """
if $msg contains '""" + pattern + """' then {
       action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_AP_get_log.py \\\"""" + pattern + """\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}
:syslogtag, contains, "montag" /var/log/devices/script_execution.log
& stop
"""

with open(r"/etc/rsyslog.conf", 'r+') as fp:
    # read an store all lines into list
    lines = fp.readlines()
    # move file pointer to the beginning of a file
    fp.seek(0)
    # truncate the file
    fp.truncate()

    # start writing lines except the last line
    # lines[:-1] from line 0 to the second last line
    fp.writelines(lines[:-2])


with open("/etc/rsyslog.conf", "a+") as file:
    file.write(text)
