import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ALE_v2.settings')
django.setup()

from pathlib import Path
import glob
import zipfile
import pandas as pd
import shutil

from ALE_v2.ALEUser.models import *

template = '''
template (name="{0}" type="string" 
    string="/var/log/devices/{1}.json")
'''

rule = '''
{0} then {{
    $RepeatedMsgReduction on
    action(type="omfile" DynaFile="deviceloghistory" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
    action(type="omfile" DynaFile="{4}" template="json_syslog" DirCreateMode="0755" FileCreateMode="0755")
    action(type="omprog" name="{1}" binary="{2} \\\"{3}\\\"" queue.type="LinkedList" queue.size="1" queue.workerThreads="1")
    stop
}}
:syslogtag, contains, "montag" /var/log/devices/script_execution.log
& stop
'''

os.system("sudo apt-get update")
# os.system("apt list | grep preventivemaintenance")
os.system("sudo apt-get --only-upgrade install preventivemaintenance")

try:
    path = os.path.dirname(__file__)
    
    # source path and destination paths
    source_path = r'/opt/ALE_Scripts'
    destination_path = str(os.path.join(path, "ale_scripts"))

    # path to source folder after extraction
    script_folder = [ name for name in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, name)) ][0]
    script_folder_path = str(os.path.join(source_path, script_folder))

    # fetching of the excel file
    csv_files = glob.glob(os.path.join(source_path, "*.xlsx"))
    print('csv files', csv_files)

    f = csv_files[0]

    # read the csv file
    df = pd.read_excel(f)                                        
    head = df.head()
    print('head:', head)

    for index, row in df.iterrows():
        # print('data -> ', index, row['Pattern'], row['Script'])
        pattern = row['Pattern']
        script = row['Script']
        dynaFile = row['DynaFile']
        log_filename = row['LogFilename']
        commandlineArgs = row['CommandLineArgs']
        description = row['Description']

        if len(script.split(' ')) > 1:
            python_script, data = script.split(' ', 1)
            data = "\\\"{0}\\\"".format(data)
        else:
            python_script, data = script, ''

        # python script destination path
        source = str(os.path.join(script_folder_path, python_script))
        destination = str(os.path.join(destination_path, python_script))

        # copy the file from source to destination
        shutil.copyfile(source, destination)

        # create/update rule
        action = 'Execute Scripts'  
        action = Actions.objects.get(action = action)
        ruletype = RulesTypes.objects.get(type_name = 'Default')

        rules, rules_created_bool = Rules.objects.update_or_create(rule_name = pattern,
                                                                    defaults = {
                                                                        'rule_type_id': ruletype,
                                                                        'action_id': action,
                                                                        'enabled': True,
                                                                        'timeout': 5,
                                                                        'rule_description': description
                                                                    })
        
        # _rule = Rules.objects.filter(rule_name = pattern)
        # if len(_rule) == 0:
        #     rules = Rules.objects.create(rule_name = pattern, rule_type_id = ruletype, action_id = action, enabled = True, timeout = 5, rule_description = description)

        # rsyslog template
        rsyslog_template_flag = True
        rsyslog_template = template.format(dynaFile, log_filename)

        # if rule is already present in rsyslog.conf then remove it
        with open(r'/etc/rsyslog.conf', "r") as file_input:
            file_data = file_input.readlines()

        with open(r'/etc/rsyslog.conf', "w") as output: 
            count = 0
            while file_data:
                line = file_data.pop(0)

                if rsyslog_template_flag and 'template (name=\"{0}\" type=\"string\"'.format(dynaFile) in line.strip("\n"):
                    rsyslog_template_flag = False
                    file_data.pop(0)
                    output.write(rsyslog_template.lstrip("\n")) 
                    continue

                if pattern in line.strip("\n"):
                    if '{' in line:
                        count += 1
                        
                    while count:
                        line = file_data.pop(0)
                        if '{' in line:
                            count += 1
                        elif '}' in line:
                            count -= 1
                    
                    file_data.pop(0)

                elif count == 0:
                    output.write(line)

        # write in Rsyslog.conf
        rsyslog_rule = rule.format(pattern, python_script.split('.')[0], destination + ((' ' + data) if data else ''), commandlineArgs, dynaFile)

        with open(r'/etc/rsyslog.conf', 'r+') as fp:
            # read an store all lines into list
            lines = fp.readlines()
            # move file pointer to the beginning of a file
            fp.seek(0)
            # truncate the file
            fp.truncate()

            # start writing lines except the last line
            # lines[:-1] from line 0 to the second last line
            fp.writelines(lines[:-2])

        with open(r'/etc/rsyslog.conf', 'a+') as file:
            if rsyslog_template_flag:
                file.write(rsyslog_template)

            file.write(rsyslog_rule)

        # changing the permissions of the files
        os.chmod(destination, 0o755)
        shutil.chown(destination, 'admin-support', 'admin-support')

    # restart the rsyslog
    os.system("systemctl restart rsyslog")
    print('success')

except Exception as e:
    # restart the rsyslog
    os.system("systemctl restart rsyslog")
    print('failure, exception is ' + e)
