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

mkdir $dir >& /dev/null
mkdir /tftpboot/upgrades >& /dev/null
cp ./Setup.sh $dir/
cp ./*.py $dir/ #change in mv
cp ./*.csv $dir/ >& /dev/null
chmod 755 $dir/*
chown admin-support:admin-support $dir/*

while [[ "$notif" != 1  && "$notif" != 2 && "$notif" != 3 ]]
do

yn=0 #variable to validate informations
read -p "Do you want to be notified by email, Rainbow bot or both?
(1)==>email  (2)==>Rainbow  (3)==>both : " notif
if [[ "$notif" == 1 || "$notif" == 2 || "$notif" == 3 ]]
then

unset rainbow_jid
unset mails
unset allows_ip
unset login_switch,
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

  if [[ "$notif" == 3 || "$notif" == 1 ]]
  then

   #mail address that will send notifications :
    while [ -z "$mails" ]
    do
      echo
      #===> variable email_address = 'toto@gmail.com'; or 'patrice.paul@al-enterprise.com';, 'palani.srinivasan@al-enterprise.com';
      echo "Please provide the email address you want to be notified. If several emails addresses, please separate by a semicolon (;)"
      read -p "Enter address(es) : " mails
      if [ -z "$mails" ]
      then
        echo "Cannot be empty"
      elif !  [[ $mails =~ (([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5};))*(([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5}))$ ]]
      then
     echo "The emails list doesn't correspond with what was expected, retry."
     unset mails
      fi
    done
    gmail_user="data.emea@gmail.com"
    gmail_passwd="Geronim0*"

  fi

#If 2 or 3 is selected
#Please provide your Rainbow JID
  if [[ "$notif" == 3 || "$notif" == 2 ]]
  then
   echo
    while [ -z "$rainbow_jid" ]
    do
      echo -e "\e[32mTip:\e[39m to find your Rainbow JID, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
      read -p "Enter your Rainbow JID (ex :j_xxx@openrainbow.com) : " rainbow_jid
      if [ -z "$rainbow_jid" ]
      then
        echo "Cannot be empty"
      elif ! [[ $rainbow_jid =~ ^.*@openrainbow.com$ ]]
       then
         echo "The Rainbow JID doesn't correspond with what was expected, retry."
         unset rainbow_jid
      fi
    done
  fi

echo
echo "What are the string patterns you want to apply in the switch collection rules (we support up to 3 patterns)?
==> "Example: policy exception"
==> "Example: crash"
==> "Example: reboot""
echo

reponse_tab=()
reponse=""
read -p 'Entrer stop pour arreter la saisie des paterns : ' reponse
while [ -z "$reponse" ] || [ "$reponse" != 'stop' ]
do
        echo "$reponse"
        reponse_tab+=("$reponse")
        read -p 'Entrer stop pour arreter la saisie des paterns : ' reponse
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
                echo "What are the string patterns you want to apply in the Stellar Access Point collection rules (we support up to 3 patterns)?
                ==> "Example: policy exception"
                ==> "Example: crash"
                ==> "Example: reboot""
                echo

                same="1"
                while [ "$same" = "1" ]
                do
                  read -p "Enter your first pattern  : " pattern_1_AP
                  if [ -z  "$pattern_1_AP" ]
                  then 
                    same="0"
                  elif [[ "$pattern_1_AP" != "$pattern_1" && "$pattern_1_AP" != "$pattern_2" && "$pattern_1_AP" != "$pattern_1" ]]
                  then
                    same="0"
                  else
                    echo " AP patterns must be differents than Switches patterns"
                  fi
                done

                 same="1"
                 while [ "$same" = "1" ]
                 do
                   read -p "Enter your second pattern  : " pattern_2_AP
                   if [ -z  "$pattern_2_AP" ]
                   then
                     same="0"
                   elif [[ "$pattern_2_AP" != "$pattern_1" && "$pattern_2_AP" != "$pattern_2" && "$pattern_2_AP" != "$pattern_1" ]]
                   then
                     same="0"
                   else
                     echo " AP patterns must be differents than Switches patterns"
                   fi
                 done

                 same="1"
                 while [ "$same" = "1" ]
                 do
                   read -p "Enter your third pattern  : " pattern_3_AP
                   if [ -z  "$pattern_3_AP" ]
                    then
                      same="0"
                    elif [[ "$pattern_3_AP" != "$pattern_1" && "$pattern_3_AP" != "$pattern_2" && "$pattern_3_AP" != "$pattern_1" ]]
                    then
                      same="0"
                    else
                      echo " AP patterns must be differents than Switches patterns"
                    fi
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
echo "Your switch parttens :"

for rep in "${reponse_tab[@]}"
do
        echo "$rep \n"
done

echo "Networks allowed : $ip_allows"
echo
if [ "$ap" == "1" ]
then
echo "login of APs : $login_AP"
echo "password of APs : $pass_AP"
echo "support technical code of APs : $tech_pass"

echo "Your three AP parttens :"
echo "==> $pattern_1_AP"
echo "==> $pattern_2_AP"
echo "==> $pattern_3_AP"
fi
 
while [[ $yn != "Y" && $yn != "N" && $yn != "y" && $yn != "n" ]]
do
  read -p   "Do you want to confirm? (Y/N)" yn
    case $yn in
          [Nn]* ) notif=0 ;;
          [Yy]* ) echo "$login_switch,$pass_switch,$mails,$rainbow_jid,$gmail_user,$gmail_passwd,$ip_server_log,$login_AP,$pass_AP,$tech_pass,$((1000 + $RANDOM % 9999))$((1000 + $RANDOM % 9999))$((10 + $RANDOM % 99)),$pattern_1,$pattern_2,$pattern_3" > $dir/ALE_script.conf;;
          * ) echo "Please answer Y or N.";;
    esac

done

else
   echo -e "\e[91mWrong parameter\e[39m"
fi

done

default="ZzZNoneZzZNoneZzz"
pattern_1_AP=${pattern_1_AP:-$default}
pattern_2_AP=${pattern_2_AP:-$default}
pattern_3_AP=${pattern_3_AP:-$default}

test = "if \$msg contains '$rep' then {
      action(type=\'omfile\' DynaFile=\'deviceloghistory\' template=\'json_syslog\' DirCreateMode=\'0755\' FileCreateMode=\'0755\')
      action(type=\'omfile\' DynaFile=\'deviceloggetlogswitch\' template=\'json_syslog\' DirCreateMode=\'0755\' FileCreateMode=\'0755\')
      action(type=\'omprog\' binary=\'/opt/ALE_Script/support_switch_get_log.py $rep\' queue.type=\'LinkedList\' queue.size=\'1\' queue.workerThreads=\'1\')
 stop
}"

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
    constant(value=\"\\"\"}\\n\"")
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
*.=debug;\\
        auth,authpriv.none;\\
        news.none;mail.none     -/var/log/debug
*.=info;*.=notice;*.=warn;\\
        auth,authpriv.none;\\
        cron,daemon.none;\\
        mail,news.none          -/var/log/messages
#
# Emergencies are sent to everybody logged in.
#
*.emerg                         :omusrmsg:*
# if a syslog message contains \"error\" string, we redirect to a specific log
#:msg, contains, \"error\"         /var/log/syslog-error.log
*.* ?DynamicFile;json_syslog
# Rules
#

if \$msg contains 'Recv the  wam module  notify  data user' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py auth_step1\")
     stop
}

if \$msg contains ':authorize' or \$msg contains 'from MAC-Auth' or \$msg contains 'Access Role' then {
     \$RepeatedMsgReduction on
     if \$msg contains 'from STA' then {
     stop
     }
     if \$msg contains 'Access Role'  or \$msg contains 'Access Role' then {
     action(type=\"omfile\" DynaFile=\"devicelogmacauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py mac_auth\")
     stop
     }
     else if \$msg contains 'Get PolicyList' then {
     action(type=\"omfile\" DynaFile=\"devicelogpolicy\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py policy\")
     stop
     }
}

if \$msg contains '8021x-Auth' or \$msg contains 'RADIUS' or \$msg contains '8021x Authentication' then {
     \$RepeatedMsgReduction on
     if \$msg contains 'Retry attempts' or \$msg contains 'RADIUS Authentication server' then {
     action(type=\"omfile\" DynaFile=\"devicelog8021Xauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     stop
     }
     else if  \$msg contains '8021x-Auth' or \$msg contains '8021x Authentication' or \$msg contains 'RADIUS packet send to' then {
     action(type=\"omfile\" DynaFile=\"devicelog8021Xauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py 8021X\")
     stop
     }

     else if \$msg contains 'too many failed retransmit attempts' or \$msg contains 'No response' then {
     action(type=\"omfile\" DynaFile=\"devicelog8021Xauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py failover\")
     stop
     }
}

if \$msg contains 'Recv the  eag module  notify  data user' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py auth_step2\")
     stop
}

if \$msg contains 'Found DHCPACK for STA' or \$msg contains 'Found dhcp ack for STA' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdhcp\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py dhcp\")
     stop
}

if \$msg contains 'verdict:[NF_DROP]' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogwcf\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_authentication.py wcf_block\")
     stop
}

if \$msg contains 'TARGET ASSERTED' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_generic.py target_asserted\")
     stop
}

if \$msg contains 'Internal error' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_generic.py internal_error\")
     stop
}

if \$msg contains 'sysreboot' or \$msg contains 'sysupgrade' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_generic.py reboot\")
     stop
}

if \$msg contains 'Fatal exception' or \$msg contains 'Kernel panic' or \$msg contains 'Exception stack' or \$msg contains 'parse condition rule is error' or \$msg contains 'core-monitor reboot' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_generic.py exception\")
     stop
}

if \$msg contains 'Send deauth, reason 1' or \$msg contains 'deauth reason 1' then {
  \$RepeatedMsgReduction on
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_generic.py roaming\")
  stop
}

if \$msg contains 'Send deauth, reason' or \$msg contains 'Received disassoc' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_generic.py deauth\")
     stop
}

if \$msg contains 'Received deauth' then {
  \$RepeatedMsgReduction on
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  action(type=\"omprog\" binary=\"python3 /opt/ALE_Script/send_email_generic.py leaving\")
  stop
}

if \$msg contains 'intfNi Mka' or \$msg contains 'intfNi Drv' or \$msg contains 'intfNi Msec' then {
  action(type=\"omfile\" DynaFile=\"deviceloghistory\" dirCreateMode=\"0755\" FileCreateMode=\"0755\")
  if \$msg contains 'ieee802_1x_cp_connect_secure' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
 #   action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_macsec.py macsec\")
    stop
  }
  if \$msg contains 'Delete MKA' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_macsec.py delete_mka\")
    stop
  }
  if \$msg contains 'CP entering state' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
  }
  if \$msg contains 'CP entering state CHANGE' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_macsec.py change\")
    stop
  }
  if \$msg contains 'CP entering state RETIRE' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_macsec.py retire\")
    stop
  }
  if \$msg contains 'Delete transmit SA' then {
    action(type=\"omfile\" DynaFile=\"devicelogmacsec\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
    action(type=\"omprog\" binary=\"/opt/ALE_Script/send_email_macsec.py delete_sa\")
    stop
  }
}

if \$msg contains 'ALRM: Core dump' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpmd\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_pmd.py pmd\")
     stop
}

if \$msg contains 'PMD generated at' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpmd\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_pmd.py pmd_generated\")
     stop
}

if \$msg contains 'pmnHALLinkStatusCallback:206' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogflapping\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
#queue.size=\"1\" queue.discardmark=\"1\" queue.TimeoutActionCompletion=\"2000\")
     action(type=\"omprog\" binary=\"$dir/support_switch_port_flapping.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}
if \$msg contains 'Denial of Service attack detected: <port-scan>' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogddosdebug\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_debugging_ddos.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'ALV4 event: PSCAN' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogddosip\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/support_switch_enable_qos.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}
if \$msg contains '$pattern_1_AP' or \$msg contains '$pattern_2_AP' or \$msg contains '$pattern_3_AP' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"deviceloggetlogap\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/opt/ALE_Script/support_AP_get_log.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'duplicate IP address' or \$msg contains 'Duplicate IP address' then{
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogdupip\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/usr/bin/env python3 /opt/ALE_Script/support_switch_duplicate_ip.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'CMM Authentication failure detected' then{
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogauthfail\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/usr/bin/env python3 /opt/ALE_Script/support_switch_auth_fail.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}


if \$msg contains 'Buffer list is empty' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelog\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_debugging.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}


if \$msg contains 'Violation set' or \$msg contains 'in violation'  then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogviolation\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"/usr/bin/env python3 /opt/ALE_Script/support_switch_violation.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}


if \$msg contains 'bootMgrVCMTopoDataEventHandler' and \$msg contains 'no longer' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_vc_down.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'Power Supply' and \$msg contains 'Removed'  then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpowersupplydown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_power_supply.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'slnHwlrnCbkHandler' and \$msg contains 'port' and \$msg contains 'bcmd' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogloop\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_port_disable.py\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}
:syslogtag, contains, \"montag\" /var/log/devices/script_execution.log
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
echo -e "\e[32mConfiguration of services\e[39m"
echo
apt-get -qq -y  update >& /dev/null
apt-get -qq -y install sshpass
apt-get -qq -y install python3.7
apt-get -qq -y install python3-pip
pip3  install --quiet pysftp
pip3 install --quiet flask
apt-get -qq -y install tftpd-hpa
export PYTHONPATH=/usr/local/bin/python3.7

#echo "File created /var/log/devices/logtemp.json"
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
    sudo python3 opt_pattern.py "$rep"
done














