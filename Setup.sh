#!/bin/bash

#1. Do you want to be notified by email, rainbow bot or both?
#==> variable notif= (1) email (2) rainbow (3) both


if [ "$EUID" -ne 0 ]
  then echo "Please execute with root privileges or use sudo"
  exit
fi

if ! [ "`ls  |grep ${0##*/}`" == "${0##*/}" ]
  then echo "Please execute the script Setup.sh when you are in the same directory."
  exit
fi

if ! [ "`ls  |grep Devices.csv`" == "Devices.csv" ]
  then echo "Please make sure you have the file Device.csv file is in the same directory as Setup.sh before execute the program."
  exit
fi


dir="/opt/ALE_Script"
sudo useradd -U admin-support >& /dev/null
sudo groupadd -g 1500 admin-support >& /dev/null
sudo usermod -a -G admin-support admin-support >& /dev/null

mkdir $dir >& /dev/null
mkdir /tftpboot/upgrades >& /dev/null
cp ./Setup.sh $dir/
#Analytics
archi=`dpkg --prinlst-architecture >& /dev/null` 
if [[ $archi == *"arm"* ]]
then
     cp -r ./Analytics/arm/* $dir/Analytics/
else
     cp -r ./Analytics/amd64/* $dir/Analytics/
fi
cp -r ./VNA_Workflow $dir/

cp ./*.py $dir/
cp ./*.csv $dir/ >& /dev/null
chmod 755 $dir/*
chown admin-support:admin-support $dir/*


unset company
unset rainbow_jid
unset mails
unset allows_ip
unset login_switch
unset pass_switch
unset ip_server_log
unset pattern_1
unset pattern_2
unset pattern_3
unset login_AP
unset pass_AP
unset tech_pass
unset pattern_1_AP
unset pattern_2_AP
unset pattern_3_AP
unset gmail_user
unset gmail_passwd
unset ap
#If 1 or 3 is selected
#===> variable gmail_user = 'data.emea@gmail.com';
#===> variable gmail_password = 'Geronim0*'

while [ -z "$mails" ]
do
  echo
  #===> variable email_address = 'toto@gmail.com'; or 'patrice.paul@al-enterprise.com';, 'palani.srinivasan@al-enterprise.com';
  echo "Please provide the email address you want to be notified. If several emails addresses, please separate by a semicolon (;)"
  read -p "Enter address(es) : " mails
  if [ -z "$mails" ]
  then
    echo "Email cannot be empty"
#     elif !  [[ $mails =~ (([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5};))*(([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5}))$ ]]
#     then
#    echo "The emails list doesn't correspond with what was expected, retry."
 unset mails
  fi
done
gmail_user="data.emea@gmail.com"
gmail_passwd="Geronim0*"
while [ -z "$rainbow_jid" ]
do
  echo -e "\e[32mTip:\e[39m to find your Rainbow JID, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
  read -p "Enter your Rainbow JID (ex :j_xxx@openrainbow.com) : " rainbow_jid
  if [ -z "$rainbow_jid" ]
  then
    echo "Rainbow JID cannot be empty"
  elif ! [[ $rainbow_jid =~ ^.*@openrainbow.com$ ]]
   then
     echo "The Rainbow JID doesn't correspond with what was expected, retry."
     unset rainbow_jid
  fi
done

#===> variable company used when calling setup_called.py script
echo "What is your Company Name?"
read -p "Company Name : " company
if [ -z "$company" ]
      then
        echo "Company Name cannot be empty"
        read -p "Company Name : " company
fi

echo
echo "What are the string patterns you want to apply in the switch collection rules (we support up to 3 patterns)?
==> "Example: policy exception"
==> "Example: crash"
==> "Example: reboot""
echo

reponse_tab=()
reponse=""
while [ -z "$reponse" ] || [ "$reponse" != "stop" ]
do
    read -p 'Enter stop for exiting: ' reponse
    echo "$reponse"
    if [ "$reponse" == "stop" ]
    then
        echo 
    else
        reponse_tab+=("$reponse")
    fi
done

#===> variable login='admin', prefilled with value "admin", means if the user press enters we use the default value
echo
echo "What are the switches credentials?"
default="admin"
read -p "Login [default="$default"] : " login_switch 
login_switch=${login_switch:-$default}

#===> variable password='switch', prefilled with value "admin", means if the user press enters we use the default value

default="switch"
read -p "Password [default="$default"] : " pass_switch
pass_switch=${pass_switch:-$default}

while [[ $yn != "Y" && $yn != "N" && $yn != "y" && $yn != "n" ]]
do
read -p "Do you want configure you Stellar AP?(Y/N) " yn
    case $yn in
          [Nn]* ) ap="0" ;;
          [Yy]* ) ap="1"
                echo "What are the Stellar AP credentials?"
                read -p "Login : " login_AP
                read -p "Password : " pass_AP
                read -p "Technical Support code : " tech_pass
                echo
                echo "What are the string patterns you want to apply in the Stellar Access Point collection rules ?
                ==> "Example: policy exception"
                ==> "Example: crash"
                ==> "Example: reboot""
                echo
                reponse_tab_AP=()
                reponse_AP=""
                while [ -z "$reponse_AP" ] || [ "$reponse_AP" != 'stop' ]
                do
                read -p 'Enter stop for exiting: ' reponse_AP
                echo "$reponse_AP"
                for i in "${reponse_tab[@]}"
                do
                     if [ "$i" == "$reponse_AP" ]
                     then
                          echo "pattern already exist, try another one"
                     else
                          reponse_tab_AP+=("$reponse_AP")
                     fi
                done
                done  ;;


          * ) echo "Please answer Y or N.";;
    esac

done
unset yn


# Please provide the Server log ip address on which you want receive logs.

while [ -z "$ip_server_log" ]
do
   read -p "# Please provide the Server log ip address on which you want receive logs. :  " ip_server_log
   if [ -z "$ip_server_log" ]
   then
      echo "Cannot be empty"
   elif ! [[ $ip_server_log =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]
   then
        echo "The IP Address doesn't correspond with what was expected, retry."
        unset ip_server_log

   fi
done

# Please provide the Networks allow to send logs with the format subnet/netmask
echo
while [ -z "$ip_allows" ]
do
   echo  "Please provide the network subnets you want to allow to send logs with the format subnet/netmask if you have more than 1 separate with a comma (,). " 
   read -p "(ex : 10.0.0.0/16, 192.168.1.1/24, 172.16.20.0/16) :  " ip_allows
   if [ -z "$ip_allows" ]
   then
     echo "Cannot be empty"

  elif ! [[ $ip_allows =~ (([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2}, ?)*(([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2})$ ]]
   then
        echo "The IP Address list doesn't correspond with what was expected, retry."
        unset ip_allows
    fi
 done

echo
echo -e "\e[32mSummary of your informations:\e[39m"
echo "login of switches : $login_switch"
echo "password of switches : $pass_switch"
if [[ "$notif" == 2 || "$notif" == 3 ]]
then
echo "your rainbow JID :  $rainbow_jid"
fi
echo
if [[ "$notif" == 1 || "$notif" == 3 ]]
then
echo "Your mails addresses : $mails"
fi
echo "Your company name : $company"
echo "Your switch parttens :"

for rep in "${reponse_tab[@]}"
do
        echo "- $rep"
done

echo "Networks allowed : $ip_allows"
echo
if [ "$ap" == "1" ]
then
echo "login of APs : $login_AP"
echo "password of APs : $pass_AP"
echo "support technical code of APs : $tech_pass"
echo "Your AP parttens :"
for rep in "${reponse_tab_AP[@]}"
do
        echo "- $rep"
done
fi

while [[ $yn != "Y" && $yn != "N" && $yn != "y" && $yn != "n" ]]
do
  read -p   "Do you want to confirm? (Y/N)" yn
    case $yn in
          [Nn]* ) notif=0 ;;
          [Yy]* ) echo "$login_switch,$pass_switch,$mails,$rainbow_jid,$ip_server_log,$login_AP,$pass_AP,$tech_pass,$((1000 + $RANDOM % 9999))$((1000 + $RANDOM % 9999))$((10 + $RANDOM % 99)),$company" > $dir/ALE_script.conf;;
          * ) echo "Please answer Y or N.";;
    esac
done

#Then script will do:
#- installation/configuration of rsyslog.conf
#- installation/configuration of logrotate
#- installation/configuration of iptables
#- installation/configuration of sshpass, python others


echo
echo -e "\e[32mConfiguration of Rsyslog\e[39m"

echo "#  /etc/rsyslog.conf    Configuration file for rsyslog.
#
#                       For more information see
#                       /usr/share/doc/rsyslog-doc/html/rsyslog_conf.html
### Allowed IP Addresses ####
\$AllowedSender UDP,127.0.0.1, $ip_allows
#################
#### MODULES ####
#################
module(load=\"imuxsock\") # provides support for local system logging
module(load=\"imklog\")   # provides kernel logging support
#module(load=\"immark\")  # provides --MARK-- message capability
module(load=\"omprog\") # provides support for script
# provides UDP syslog reception
module(load=\"imudp\")
input(type=\"imudp\" port=\"10514\")

# provides stats for node exporter - Prometheus
module(
  load=\"impstats\"
  interval=\"300\"
  format=\"json\"
  resetCounters=\"off\"
  ruleset=\"process_stats\"
  log.file=\"/var/log/rsyslog-stats\"
)

ruleset(name=\"process_stats\") {
  action(
    type=\"omprog\"
    name=\"to_exporter\"
    binary=\"/opt/rsyslog_exporter/rsyslog_exporter\"
  )
}

### Template definition ####
\$template DynamicFile,\"/var/log/devices/%hostname%/syslog.log\"

\$template MACSEC_DynamicFile,\"/var/log/devices/MACSEC/%hostname%_macsec.log\"

template (name=\"devicelogmacsec\" type=\"string\"
     string=\"/var/log/devices/lastlog_macsec.json\")

template (name=\"devicelog\" type=\"string\"
     string=\"/var/log/devices/lastlog.json\")

template (name=\"deviceloghistory\" type=\"string\"
     string=\"/var/log/devices/%fromhost-ip%_%\$YEAR%-%\$MONTH%-%\$DAY%_history.json\")

template (name=\"devicelogloop\" type=\"string\"
     string=\"/var/log/devices/lastlog_loop.json\")

template (name=\"devicelogflapping\" type=\"string\"
     string=\"/var/log/devices/lastlog_flapping.json\")

template (name=\"devicelogddosdebug\" type=\"string\"
     string=\"/var/log/devices/lastlog_ddos.json\")

template (name=\"devicelogddosip\" type=\"string\"
     string=\"/var/log/devices/lastlog_ddos_ip.json\")

template (name=\"deviceloggetlogap\" type=\"string\"
     string=\"/var/log/devices/get_log_ap.json\")

template (name=\"deviceloggetlogswitch\" type=\"string\"
     string=\"/var/log/devices/get_log_switch.json\")

template (name=\"devicelogreboot\" type=\"string\"
     string=\"/var/log/devices/lastlog_reboot.json\")

template (name=\"devicelogdeauth\" type=\"string\"
     string=\"/var/log/devices/lastlog_deauth.json\")

template (name=\"devicelogpmd\" type=\"string\"
     string=\"/var/log/devices/lastlog_pmd.json\")

template (name=\"devicelogauth\" type=\"string\"
     string=\"/var/log/devices/lastlog_wlan_authentication.json\")

template (name=\"devicelogmacauth\" type=\"string\"
     string=\"/var/log/devices/lastlog_mac_authentication.json\")

template (name=\"devicelog8021Xauth\" type=\"string\"
     string=\"/var/log/devices/lastlog_8021X_authentication.json\")

template (name=\"devicelogpolicy\" type=\"string\"
     string=\"/var/log/devices/lastlog_policy.json\")

template (name=\"devicelogdhcp\" type=\"string\"
     string=\"/var/log/devices/lastlog_dhcp.json\")

template (name=\"devicelogwcf\" type=\"string\"
     string=\"/var/log/devices/lastlog_wcf.json\")

template (name=\"devicelogvcdown\" type=\"string\"
     string=\"/var/log/devices/lastlog_vc_down.json\")

template (name=\"devicelogpowersupplydown\" type=\"string\"
     string=\"/var/log/devices/lastlog_power_supply_down.json\")

template (name=\"devicelogdupip\" type=\"string\"
     string=\"/var/log/devices/lastlog_dupip.json\")

template (name=\"devicelogauthfail\" type=\"string\"
     string=\"/var/log/devices/lastlog_authfail.json\")

template (name=\"devicelogviolation\" type=\"string\"
     string=\"/var/log/devices/lastlog_violation.json\")

template (name=\"devicelogwips\" type=\"string\"
     string=\"/var/log/devices/lastlog_wips.json\")

template (name=\"devicelogospf\" type=\"string\"
     string=\"/var/log/devices/lastlog_ospf.json\")

template (name=\"devicelogspb\" type=\"string\"
     string=\"/var/log/devices/lastlog_spb.json\")

template (name=\"devicelogbgp\" type=\"string\"
     string=\"/var/log/devices/lastlog_bgp.json\")

template (name=\"devicelogddm\" type=\"string\"
     string=\"/var/log/devices/lastlog_ddm.json\")

template(name=\"json_syslog\"
  type=\"list\") {
    constant(value=\"{\")
    constant(value=\"\\"\"@timestamp\\"\":\\"\""\")       property(name=\"timereported\" dateFormat=\"rfc3339\")
      constant(value=\"\\\",\\"\""type\\\":\\"\""syslog_json\")
#      constant(value=\"\\\",\\"\"""tag\\\":\\"\""\"")           property(name=\"syslogtag\" format=\"json\")
#      constant(value=\"\\\",\\"\"""relayhost\\\":\\"\""\"")     property(name=\"fromhost\")
      constant(value=\"\\\",\\"\"""relayip\\\":\\"\""\"")       property(name=\"fromhost-ip\")
#     constant(value=\"\\\",\\"\"""logsource\\\":\\"\""\"")     property(name=\"source\")
      constant(value=\"\\\",\\"\"""hostname\\\":\\"\""\"")      property(name=\"hostname\" caseconversion=\"lower\")
#      constant(value=\"\\\",\\"\"""program\\\":\\"\""\"")      property(name=\"programname\")
#      constant(value=\"\\\",\\"\"""priority\\\":\\"\""\"")      property(name=\"pri\")
#      constant(value=\"\\\",\\"\"""severity\\\":\\"\""\"")      property(name=\"syslogseverity\")
#      constant(value=\"\\\",\\"\"""facility\\\":\\"\""\"")      property(name=\"syslogfacility\")
#      constant(value=\"\\\",\\"\"""severity_label\\\":\\"\""\"")   property(name=\"syslogseverity-text\")
#      constant(value=\"\\\",\\"\"""facility_label\\\":\\"\""\"")   property(name=\"syslogfacility-text\")
      constant(value=\"\\\",\\"\"""message\\\":\\"\""\"")       property(name=\"rawmsg\" format=\"json\")
      constant(value=\"\\\",\\"\"""end_msg\\\":\\"\""\"") 
    constant(value=\"\\"\"}\\\n\"")
}
# provides TCP syslog reception
#module(load=\"imtcp\")
#input(type=\"imtcp\" port=\"514\")
###########################
#### GLOBAL DIRECTIVES ####
###########################
#
# Use traditional timestamp format.
# To enable high precision timestamps, comment out the following line.
#
\$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat
#
# Set the default permissions for all log files.
#
\$FileOwner root
\$FileGroup adm
\$FileCreateMode 0666
\$DirCreateMode 0755
\$Umask 0022
#
# Where to place spool and state files
#
\$WorkDirectory /var/spool/rsyslog
#
# Include all config files in /etc/rsyslog.d/
#
\$IncludeConfig /etc/rsyslog.d/*.conf
###############
#### RULES ####
###############
#
# First some standard log files.  Log by facility.
#
auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none          -/var/log/syslog
#cron.*                         /var/log/cron.log
daemon.*                        -/var/log/daemon.log
kern.*                          -/var/log/kern.log
lpr.*                           -/var/log/lpr.log
mail.*                          -/var/log/mail.log
user.*                          -/var/log/user.log
#
# Logging for the mail system.  Split it up so that
# it is easy to write scripts to parse these files.
#
mail.info                       -/var/log/mail.info
mail.warn                       -/var/log/mail.warn
mail.err                        /var/log/mail.err
#
# Some \"catch-all\" log files.
#
*.=debug;\\\
        auth,authpriv.none;\\\
        news.none;mail.none     -/var/log/debug
*.=info;*.=notice;*.=warn;\\\
        auth,authpriv.none;\\\
        cron,daemon.none;\\\
        mail,news.none          -/var/log/messages
#
# Emergencies are sent to everybody logged in.
#
*.emerg                         :omusrmsg:*
#############
## GARBAGE ##
#############
:msg, contains, \"FIPS\" stop
:msg, contains, \"integrity test passed\" stop
:msg, contains, \"DBG3\" stop
:msg, contains, \"DBG2\" stop

if \$msg contains 'ConsLog' then {
     action(type=\"omfile\" File=\"/var/log/devices/Console_Logs.log\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     stop
}

# if a syslog message contains \"error\" string, we redirect to a specific log
#:msg, contains, \"error\"         /var/log/syslog-error.log
*.* ?DynamicFile;json_syslog

############### Rules Preventive Maintenance ##########
#

##### WLAN Rules for Stellar AP Quality User Experience #####
if \$msg contains 'Recv the  wam module  notify  data user' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_auth_step1\" binary=\"/opt/ALE_Script/support_wlan_generic.py auth_step1\")
     stop
}

if \$msg contains ':authorize' or \$msg contains 'from MAC-Auth' or \$msg contains 'Access Role' then {
     \$RepeatedMsgReduction on
     if \$msg contains 'from STA' then {
     stop
     }
     if \$msg contains 'Access Role'  or \$msg contains 'Access Role' then {
     action(type=\"omfile\" DynaFile=\"devicelogmacauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_mac_auth\" binary=\"/opt/ALE_Script/support_wlan_generic.py mac_auth\")
     stop
     }
     else if \$msg contains 'Get PolicyList' then {
     action(type=\"omfile\" DynaFile=\"devicelogpolicy\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_policy\" binary=\"/opt/ALE_Script/support_wlan_generic.py policy\")
     stop
     }
}

if \$msg contains '8021x-Auth' or \$msg contains 'RADIUS' or \$msg contains '8021x Authentication' then {
     \$RepeatedMsgReduction on
     if \$msg contains 'Retry attempts' or \$msg contains 'RADIUS Authentication server' then {
     action(type=\"omfile\" name=\"support_wlan_generic_radius\" DynaFile=\"devicelog8021Xauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     stop
     }
     else if  \$msg contains '8021x-Auth' or \$msg contains '8021x Authentication' or \$msg contains 'RADIUS packet send to' then {
     action(type=\"omfile\" DynaFile=\"devicelog8021Xauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_radius\" binary=\"/opt/ALE_Script/support_wlan_generic.py 8021X\")
     stop
     }

     else if \$msg contains 'too many failed retransmit attempts' or \$msg contains 'No response' then {
     action(type=\"omfile\" DynaFile=\"devicelog8021Xauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_radius\" binary=\"/opt/ALE_Script/support_wlan_generic.py failover\")
     stop
     }
}

if \$msg contains 'Recv the  eag module  notify  data user' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_auth_step2\" binary=\"/opt/ALE_Script/support_wlan_generic.py auth_step2\")
     stop
}

if \$msg contains 'Found DHCPACK for STA' or \$msg contains 'Found dhcp ack for STA' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdhcp\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_dhcp\" binary=\"/opt/ALE_Script/support_wlan_generic.py dhcp\")
     stop
}

##### WLAN Rules for Stellar AP Web Control Filtering #####

if \$msg contains 'verdict:[NF_DROP]' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogwcf\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_wcf\" binary=\"/opt/ALE_Script/support_wlan_generic.py wcf_block\")
     stop
}

##### WLAN Rules for Stellar AP deassociation or deauthentication #####

if \$msg contains 'Send deauth, reason 1' or \$msg contains 'deauth reason 1' or \$msg contains 'Send deauth from wam, reason 36' then {
  \$RepeatedMsgReduction on
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  action(type=\"omprog\" name=\"support_wlan_generic_roaming\" binary=\"/opt/ALE_Script/support_wlan_generic.py roaming\")
  stop
}

if \$msg contains 'Send deauth, reason' or \$msg contains 'Send deauth from wam, reason' or \$msg contains 'Received disassoc' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_deauth\" binary=\"/opt/ALE_Script/support_wlan_generic.py deauth\")
     stop
}

if \$msg contains 'Received deauth' then {
  \$RepeatedMsgReduction on
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  action(type=\"omprog\" name=\"support_wlan_generic_leaving\" binary=\"/opt/ALE_Script/support_wlan_generic.py leaving\")
  stop
}

##### WLAN Rules for Stellar AP upgrade or reboot #####

if \$msg contains 'sysreboot' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_sysreboot\" binary=\"/opt/ALE_Script/support_wlan_generic.py reboot\")
     stop
}

if \$msg contains 'enter in sysupgrade' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_sysupgrade\" binary=\"/opt/ALE_Script/support_wlan_generic.py upgrade\")
     stop
}

##### WLAN Rules for handling all abnormal operations #####

if \$msg contains 'TARGET ASSERTED' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_target_asserted\" binary=\"/opt/ALE_Script/support_wlan_generic.py target_asserted\")
     stop
}

if \$msg contains 'Internal error' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_internal_error\" binary=\"/opt/ALE_Script/support_wlan_generic.py internal_error\")
     stop
}

if \$msg contains 'Fatal exception' or \$msg contains 'Kernel panic' or \$msg contains 'Exception stack' or \$msg contains 'parse condition rule is error' or \$msg contains 'core-monitor reboot' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_exception\" binary=\"/opt/ALE_Script/support_wlan_generic.py exception\")
     stop
}

if \$msg contains 'Unable to handle kernel'  then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_kernel_panic\" binary=\"/opt/ALE_Script/support_wlan_generic.py kernel_panic\")
     stop
}

##### Rules WLAN if we reached the limit of Associated WLAN Clients ########
if \$msg contains 'STA limit reached' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_limit_reached\" binary=\"/opt/ALE_Script/support_wlan_generic.py limit_reached\")
     stop
}

if \$msg contains 'incremented iv_sta_assoc' or \$msg contains 'decremented iv_sta_assoc' then {
  \$RepeatedMsgReduction on
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  stop
}

##### Rules WLAN WIPS under progress ########
#if \$msg contains '[Lbd-Deny-Cnt] : Set Client' then {
#  \$RepeatedMsgReduction on
#  action(type=\"omfile\" DynaFile=\"devicelogwips\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
#  action(type=\"omprog\" name=\"support_wlan_generic_wips\" binary=\"/opt/ALE_Script/support_wlan_generic.py wips\")
#  stop
#}


##### Rules MAC-SEC ########
if \$msg contains 'intfNi Mka' or \$msg contains 'intfNi Drv' or \$msg contains 'intfNi Msec' then {
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" dirCreateMode=\"0755\" FileCreateMode=\"0755\")
  if \$msg contains 'ieee802_1x_cp_connect_secure' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
 #   action(type=\"omprog\" name=\"support_lan_generic_macsec\" binary=\"/opt/ALE_Script/send_email_macsec.py macsec\")
    stop
  }
  if \$msg contains 'Delete MKA' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" name=\"support_lan_generic_macsec\" binary=\"/opt/ALE_Script/send_email_macsec.py delete_mka\")
    stop
  }
  if \$msg contains 'CP entering state' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  }
  if \$msg contains 'CP entering state CHANGE' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" name=\"support_lan_generic_macsec\" binary=\"/opt/ALE_Script/send_email_macsec.py change\")
    stop
  }
  if \$msg contains 'CP entering state RETIRE' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" name=\"support_lan_generic_macsec\" binary=\"/opt/ALE_Script/send_email_macsec.py retire\")
    stop
  }
  if \$msg contains 'Delete transmit SA' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" name=\"support_lan_generic_macsec\" binary=\"/opt/ALE_Script/send_email_macsec.py delete_sa\")
    stop
  }
}

#### Rules Core DUMP - LAN #########

if \$msg contains 'PMD generated at' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpmd\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_pmd\" binary=\"/opt/ALE_Script/support_switch_pmd.py\")
     stop
}

#### Rules Port Flapping - LAN ######
if \$msg contains 'pmnHALLinkStatusCallback:206' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogflapping\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
#queue.size=\"1\" queue.discardmark=\"1\" queue.TimeoutActionCompletion=\"2000\")
     action(type=\"omprog\" name=\"support_lan_generic_flapping\" binary=\"$dir/support_switch_port_flapping.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rules DDOS - LAN #####
if \$msg contains 'Denial of Service attack detected: <port-scan>' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogddosdebug\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ddos\" binary=\"/opt/ALE_Script/support_switch_debugging_ddos.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'ALV4 event: PSCAN' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogddosip\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ddos\" binary=\"/opt/ALE_Script/support_switch_enable_qos.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rule Duplicate IP Address - LAN ####
if \$msg contains 'duplicate IP address' or \$msg contains 'Duplicate IP address' then{
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogdupip\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_dupip\" binary=\"/opt/ALE_Script/support_switch_duplicate_ip.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rule Authentication Failure - LAN ####
if \$msg contains 'SES AAA' and \$msg contains 'Failed' then{
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogauthfail\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_auth_failure\" binary=\"/opt/ALE_Script/support_switch_auth_fail.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rule Network Loop - LAN ####
if \$msg contains 'Buffer list is empty' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelog\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_loop\" binary=\"$dir/support_switch_debugging.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'slnHwlrnCbkHandler' and \$msg contains 'port' and \$msg contains 'bcmd' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogloop\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_loop\" binary=\"$dir/support_switch_port_disable.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rule Port Violation - LAN ####
if \$msg contains 'Violation set' or \$msg contains 'in violation'  then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogviolation\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_violation\" binary=\"/opt/ALE_Script/support_switch_violation.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### VC Unit DOWN - LAN ####
if \$msg contains 'bootMgrVCMTopoDataEventHandler' and \$msg contains 'no longer' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'cmmEsmHandleNIDown' and \$msg contains 'chassis' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'Sending VC Takeover to NIs and applications' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'The switch was restarted by' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### PS Unit DOWN - LAN ####
if \$msg contains 'Power Supply' and \$msg contains 'Removed'  then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpowersupplydown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ps\" binary=\"$dir/support_switch_power_supply.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### SPB Adjacency DOWN - LAN ####
if \$msg contains 'ADJACENCY INFO: Lost L1 adjacency' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"devicelogspb\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" name=\"support_lan_generic_spb\" binary=\"/opt/ALE_Script/support_switch_spb.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

#### OSPF Neighbor DOWN - LAN ####
if \$msg contains 'OSPF neighbor state change' then {
       \$RepeatedMsgReduction on
       action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"devicelogospf\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" name=\"support_lan_generic_ospf\" binary=\"/opt/ALE_Script/support_switch_ospf.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

#### BGP Neighbor DOWN - LAN ####
if \$msg contains 'bgp' and \$msg contains 'transitioned to' then {
	  \$RepeatedMsgReduction on
       action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"devicelogbgp\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" name=\"support_lan_generic_bgp\" binary=\"/opt/ALE_Script/support_switch_bgp.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

#### DDM Threshold reached - LAN ####
if $msg contains 'cmmEsmCheckDDMThresholdViolations' then {
       action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"devicelogddm\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" name=\"support_lan_generic_ddm\" name=\"support_switch_queue_DDM\" binary=\"/opt/ALE_Script/support_switch_ddm.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

#### Additionnal rules - LAN ####

if \$msg contains 'failed handling msg from' then {
	  \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"failed handling msg from\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'TCAM_RET_NOT_FOUND' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"TCAM_RET_NOT_FOUND\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'Storm Threshold violation' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"Storm Threshold violation\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}


if \$msg contains 'operational state changed to UNPOWERED' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py aijaz2\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'Power supply is inoperable' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"Power supply is inoperable\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'Power Supply 1 Removed' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"Power Supply 1 Removed\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'The switch was restarted by a power cycle' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"The switch was restarted by a power cycle\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'CMM chassisTrapsAlert - CMM Down' then {
	  \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"CMM chassisTrapsAlert - CMM Down\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'FAULT State change 1b to 24' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"FAULT State change 1b to 24\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'FAULT State change 1b to 25' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"FAULT State change 1b to 25\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'FAULT State change 1b to 1e' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"FAULT State change 1b to 1e\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'FAULT State change 1b to 1c' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"FAULT State change 1b to 1c\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'lpStartNi' and \$msg contains 'Starting' then {
       \$RepeatedMsgReduction onaction(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"LANPOWER Starting\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'Unable to connect' and \$msg contains 'mqttd' then {
       \$RepeatedMsgReduction on
       action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"mqttd Unable to connect\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'openvpn' and \$msg contains 'Cannot resolve host address' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"cloud agent not able to resolve tenant address\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'ovcmm' and \$msg contains 'Invalid process status' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"cloud agent SN not created on Device Catalog\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'ospf' and \$msg contains 'oversized LSA' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"OSPF Oversized LSA received\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}


if \$msg contains 'alert' and \$msg contains 'The top 20' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"High memory issue\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

if \$msg contains 'RADIUS Primary Server' and \$msg contains 'DOWN' then {
       \$RepeatedMsgReduction on
	  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omfile\" DynaFile=\"deviceloggetlogswitch\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
       action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_get_log.py \\\"RADIUS Primary Server DOWN\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
       stop
}

####### TROUBLESHOOTING ########

:syslogtag, contains, \"montag\" /var/log/devices/script_execution.log
:hostname, isequal, \"haveged\" stop
:hostname, isequal, \"kernel\" stop
if \$msg contains 'rsyslogd' then /var/log/devices/omprog.log
if \$msg contains 'omprog' then /var/log/devices/omprog.log
:hostname, isequal, \"root\" stop

& stop " >  /etc/rsyslog.conf


systemctl restart rsyslog

echo
echo -e "\e[32mConfiguration of logrotate\e[39m"


echo "/var/log/devices/*.log /var/log/devices/*/*.log
{
        missingok
        notifempty
        dateformat .%Y-%m-%d
        compress
        copytruncate
        rotate 10
        daily
        dateext
        size 20M
        create 0644 admin-support admin-support
#        postrotate
#                sudo systemctl kill -s HUP rsyslog.service
#        endscript
}
/var/log/rsyslog-stats
{
        rotate 7
        daily
        maxsize 15M
        missingok
        notifempty
        dateext
        dateformat .%Y-%m-%d
        delaycompress
        compress
        create 0644 admin-support admin-support
        postrotate
                invoke-rc.d rsyslog rotate > /dev/null
        endscript
}
/var/log/devices/*.json /var/log/devices/*/*.json
{
        missingok
        notifempty
        dateformat .%Y-%m-%d
        compress
        copytruncate
        rotate 10
        daily
        dateext
        size 20M
        create 0644 admin-support admin-support
        postrotate
                sudo systemctl kill -s HUP rsyslog.service
        endscript
}
/var/log/syslog
{
        rotate 12
        daily
        maxsize 15M
        missingok
        notifempty
        dateext
        dateformat .%Y-%m-%d
        delaycompress
        compress
        postrotate
                invoke-rc.d rsyslog rotate > /dev/null
        endscript
}
/var/log/mail.info
/var/log/mail.warn
/var/log/mail.err
/var/log/mail.log
/var/log/daemon.log
/var/log/kern.log
/var/log/auth.log
/var/log/user.log
/var/log/lpr.log
/var/log/cron.log
/var/log/debug
/var/log/messages
{
        rotate 4
        weekly
        missingok
        notifempty
        compress
        delaycompress
        sharedscripts
        postrotate
                invoke-rc.d rsyslog rotate > /dev/null
        endscript
}
" > /etc/logrotate.d/rsyslog

echo
echo -e "\e[32mInstallation and configuration of services\e[39m"
echo
apt-get -qq -y  update >& /dev/null
apt-get -qq -y install sshpass >& /dev/null
sudo echo "[Unit]
Description=Python exporter

[Service]
ExecStart=/usr/bin/python /opt/ALE_Script/support_switch_usage.py
Restart=on-failure
User=admin-support
Group=admin-support
WorkingDirectory=/opt/ALE_Script/

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/python_exporter.service
sudo systemctl daemon-reload
sudo systemctl start python_exporter.service
sudo systemctl enable  python_exporter.service

#GOLANG
echo
echo -e "\e[32mGolang Installation\e[39m"
echo
wget  -q --inet4-only https://dl.google.com/go/go1.14.4.linux-amd64.tar.gz
tar -C /usr/local -xzf go1.14.4.linux-amd64.tar.gz >& /dev/null
mkdir $home/go && chown admin-support:admin-support go/
chown admin-support:admin-support /usr/local/go
echo 'PATH=$PATH:/usr/local/go/bin
GOPATH=$HOME/go' > ~/.profile
source ~/.profile

echo
echo -e "\e[32mGolang Installed\e[39m"
echo
#RSYSLOG EXPORTER
echo
if [[ $archi == *"arm"* ]]
then
     echo -e "\e[32mRsyslog Exporter Installation\e[39m"
     sudo echo "[Unit]
     Description=Rsyslog exporter

     [Service]
     ExecStart= ~/go/bin/rsyslog_exporter
     Restart=on-failure
     User=admin-support
     Group=admin-support

     [Install]
     WantedBy=multi-user.target" > /etc/systemd/system/rsyslog_exporter.service
     sudo systemctl daemon-reload
     sudo systemctl start rsyslog_exporter.service
     sudo systemctl enable  rsyslog_exporter.service
     echo
     go get -u github.com/chijiajian/rsyslog_exporter
     echo
     echo -e "\e[32mRsyslog Exporter Installed\e[39m"
fi
echo
echo
echo -e "\e[32mDocker Installation\e[39m"
echo
#DOCKER
apt-get -qq -y install ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get -qq -y install docker-ce docker-ce-cli containerd.io
echo
echo -e "\e[32mDocker Installed\e[39m"
echo

echo
echo -e "\e[32mDocker-compose installation\e[39m"
echo
#DOCKER COMPOSE
wget -q --inet4-only --output-document=/usr/local/bin/docker-compose "https://github.com/docker/compose/releases/download/v2.2.3/docker-compose-linux-x86_64";
chmod +x /usr/local/bin/docker-compose
echo
echo -e "\e[32mDocker-Compose Installed\e[39m"
echo



#OpenSSL
echo
echo -e "\e[32mOpenSSL Installation\e[39m"
echo
apt-get -qq -y install libssl-dev
apt-get -qq -y install libncurses5-dev
apt-get -qq -y install libsqlite3-dev
apt-get -qq -y install libreadline-dev
apt-get -qq -y install libtk8.6
apt-get -qq -y install libgdm-dev
apt-get -qq -y install libdb4o-cil-dev
apt-get -qq -y install libpcap-dev

wget -q --inet4-only https://www.openssl.org/source/openssl-1.1.1g.tar.gz 
tar zxvf openssl-1.1.1g.tar.gz >& /dev/null
cd openssl-1.1.1g
./config --prefix=/home/$USER/openssl --openssldir=/home/$USER/openssl no-ssl2 >& /dev/null
make -s >& /dev/null
make -s install >& /dev/null
echo 'export PATH=$HOME/openssl/bin:$PATH
export LD_LIBRARY_PATH=$HOME/openssl/lib
export LC_ALL="en_US.UTF-8"
export LDFLAGS="-L /home/username/openssl/lib -Wl,-rpath,/home/username/openssl/lib"' > ~/.bash_profile
source ~/.bash_profile

echo
echo -e "\e[32mOpenSSL Installed\e[39m"
echo

echo
echo -e "\e[32mPython 3.10 installation\e[39m"
echo
#Python 3.10
cd /home/admin-support/Script_Preventive_Maintenance/
apt-get -qq -y install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget -q --inet4-only https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz
tar -xf Python-3.10.*.tgz >& /dev/null
cd Python-3.10.*/
./configure --with-openssl=/home/$USER/openssl >& /dev/null
sudo make -s >& /dev/null
sudo make -s altinstall >& /dev/null
update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10 1 >& /dev/null
update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.10 1 >& /dev/null

echo
echo -e "\e[32mPython3.10 installed\e[39m"
echo


sudo -H pip3.10 install --quiet pysftp >& /dev/null
sudo -H pip3.10 install --quiet influx-client >& /dev/null
sudo -H pip3.10 install --quiet prometheus-client >& /dev/null
sudo -H pip3.10 install --quiet flask >& /dev/null
sudo -H pip3.10 install --quiet requests >& /dev/null
apt-get -qq -y install tftpd-hpa >& /dev/null
export PYTHONPATH=/usr/local/bin/python3.10
echo
echo -e "\e[32mPython3.10 dependences installed\e[39m"
echo

echo "Devices log directory /var/log/devices/ created"
mkdir /var/log/devices/ >& /dev/null
touch /var/log/devices/logtemp.json
sleep 2
echo "# /etc/default/tftpd-hpa

TFTP_USERNAME=\"tftp\"
TFTP_DIRECTORY=\"/tftpboot\"
TFTP_ADDRESS=\"0.0.0.0:69\"
TFTP_OPTIONS=\"-l -c -s\" " > /etc/default/tftpd-hpa

# Check of Rsyslog status and if parsing errors
status=`systemctl status rsyslog|grep active|awk '{print $3'}|sed -e "s/(/ /g"|sed -e "s/)/ /g"`
parsing=`systemctl status rsyslog|grep "CONFIG ERROR"`

if [ "$status" == "running" ]
then
    echo -e "\e[31mSomething went wrong\e[39m, syslog is not running. This must come from your configuration, Please fill in your information paying attention to the syntax"
else
    echo -e "Rsyslog service is \e[32m `systemctl status rsyslog|grep active|awk '{print $3'}|sed -e "s/(/ /g"|sed -e "s/)/ /g"` \e[39m"
fi

echo $parsing
if [[ $? != 0 ]];
then
    echo "Command failed."
elif [[ $parsing ]];
then
    echo -e "\e[31mParsing error found \e[39mon /etc/rsyslog.conf"
else
    echo "No parsing error on Configuration Files"
fi
echo -e "\e[32mWorking directory in /opt/ALE_Script\e[39m"

for rep in "${reponse_tab[@]}"
do
    sudo /opt/ALE_Script/opt_pattern.py "$rep"
done

for rep in "${reponse_tab_AP[@]}"
do
    sudo /opt/ALE_Script/opt_pattern_AP.py "$rep"
done

echo "Sending notification to ALE DevOPS team for setup VNA application"
while IFS="," read -r rec_column1 rec_column2 rec_column3 rec_column4 rec_remaining
do
  if [ "$rec_column4" != "" ]
  then
      echo -e "\e[31mVNA already setup"
  else
      sudo python /opt/ALE_Script/setup_called.py "$company"
      echo "Setup complete"
  fi
done < /opt/ALE_Script/ALE_script.conf

echo "Launching Docker-compose"
cd /opt/ALE_Script/Analytics
docker-compose up -d
echo "Docker-compose Ok"



