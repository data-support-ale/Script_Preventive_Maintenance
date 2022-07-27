#!/bin/bash

# Source progress bar for showing the progess using status bar when downloading softwares
source ./progress_bar.sh

echo "##############################################################################"
echo "#                                                                            #"
echo "###################### Preventive Maintenance ################################"
echo "#                                                                            #"
echo "##############################################################################"
echo "      "
echo "This setup will collect your network environment settings for LAN and WLAN"
echo "The Email address(es) are mandatory and Rainbow JID's are optional for automating the Workflow and Rainbow bubble creation"
echo "      "

# folder paths : 
# -> dir - path to the ale_scripts folder 
# -> APP_DIR - path to the base folder (preventive-maintenance)
# -> ALE_conf - path to ALE_script.conf file in ale_scripts folder
dir=$PWD"/ALE_v2/ale_scripts"
APP_DIR=$PWD
ALE_conf=$dir"/ALE_script.conf"

if [ "$EUID" -ne 0 ]
  then echo "Please execute with root privileges or use sudo"
  exit
fi

if ! [ "`ls  |grep ${0##*/}`" == "${0##*/}" ]
  then echo "Please execute the script Setup.sh when you are in the same directory."
  exit
fi

if ! [ "`ls  |grep Devices.csv`" == "Devices.csv" ]
  then echo "Please make sure the file Devices.csv file is in the same directory as Setup.sh before executing the program. This file contains the list of OmniSwitches IP Addresses you want to monitor"
  exit
fi

# echo
# echo -e "\e[32mUpdating sources..\e[39m"
# echo

sudo apt-get -qq -y update
sudo apt-get -qq -y install curl
sudo apt-get -qq -y install sshpass

# echo
# echo -e "\e[32mUpdating sources is done.\e[39m"
# echo

sudo useradd -U admin-support >& /dev/null
sudo groupadd -g 1500 admin-support >& /dev/null
sudo usermod -a -G admin-support admin-support >& /dev/null

mkdir /tftpboot/ >& /dev/null

chmod 755 $dir/*
chown admin-support:admin-support $dir/*


# start of crontab creation for copying logs to external device #
sudo crontab -l > cronjobentry
filepath="0 3 * * * python3 $dir/file_move_external.py"
echo "$filepath">> cronjobentry
sudo crontab cronjobentry
rm cronjobentry
# end of crontab creation


unset company
unset rainbow_jid
unset rainbow_jid2
unset rainbow_jid3
unset mails
unset allows_ip
unset login_switch
unset pass_switch
unset ip_server_log
unset login_AP
unset pass_AP
unset tech_pass
unset ap
unset random_id

random_id=((1000 + $RANDOM % 9999))$((1000 + $RANDOM % 9999))$((10 + $RANDOM % 99))
#If 1 or 3 is selected
#===> variable gmail_user = 'data.emea@gmail.com';
#===> variable gmail_password = 'Geronim0*'

email_validation_check="^(([a-zA-Z0-9_\.\-]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)(\s*;\s*|\s*$))+\$"
company_validation_check="^[a-zA-Z0-9_-]*$"

configuration () {
     while [ -z "$mails" ]
     do
     echo
     #===> variable email_address = 'toto@gmail.com'; or 'patrice.paul@al-enterprise.com';, 'palani.srinivasan@al-enterprise.com';
     echo "Please provide the email address you want to be notified. If several email addresses, please separate by a semicolon (;). This field is mandatory"
     read -p "Enter address(es) : " mails
     if [ -z "$mails" ]
     then
          echo "Email cannot be empty"
          unset mails
     elif ! [[ $mails =~ $email_validation_check ]]
     then
          echo "The provided email address(es) is invalid. Please enter a valid email address(es)"
          unset mails
     fi
     done
 
     echo
     echo "Rainbow JID's are optional and we can skip by taping ENTER"
     echo
     
     rainbow_jid=""
     echo
     echo -e "\e[32mTip:\e[39m How to find your Rainbow JID, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
     read -p "Enter your Rainbow JID (ex :j_xxx@openrainbow.com) : " rainbow_jid
     while [ -n "$rainbow_jid" ]
     do
     if ! [[ "$rainbow_jid" =~ ^.+@openrainbow.com$ ]]
     then
          echo "The Rainbow JID doesn't correspond with what was expected, please retry."
          unset rainbow_jid
     else
          break
     fi
     echo
     echo -e "\e[32mTip:\e[39m How to find your Rainbow JID, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
     read -p "Enter your Rainbow JID (ex :j_xxx@openrainbow.com) : " rainbow_jid
     done

     rainbow_jid2=""
     echo
     echo -e "\e[32mTip:\e[39m How to find your Rainbow JID2, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
     read -p "Enter your Rainbow JID2 (ex :j_xxx@openrainbow.com) : " rainbow_jid2
     while [ -n "$rainbow_jid2" ]
     do
     if ! [[ "$rainbow_jid2" =~ ^.+@openrainbow.com$ ]]
     then
          echo "The Rainbow JID2 doesn't correspond with what was expected, please retry."
          unset rainbow_jid2
     else
          break
     fi
     echo
     echo -e "\e[32mTip:\e[39m How to find your Rainbow JID2, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
     read -p "Enter your Rainbow JID2 (ex :j_xxx@openrainbow.com) : " rainbow_jid2
     done
	 
     rainbow_jid3=""
     echo
     echo -e "\e[32mTip:\e[39m How to find your Rainbow JID3, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
     read -p "Enter your Rainbow JID3 (ex :j_xxx@openrainbow.com) : " rainbow_jid3
     while [ -n "$rainbow_jid3" ]
     do
     if ! [[ "$rainbow_jid3" =~ ^.+@openrainbow.com$ ]]
     then
          echo "The Rainbow JID3 doesn't correspond with what was expected, please retry."
          unset rainbow_jid3
     else
          break
     fi
     echo
     echo -e "\e[32mTip:\e[39m How to find your Rainbow JID3, search for the Rainbow bubble \"Am I Who\" and tape \"bonjour\"."
     read -p "Enter your Rainbow JID3 (ex :j_xxx@openrainbow.com) : " rainbow_jid3
     done
	 
     #===> variable company used when calling setup_called.py script
     while [ -z "$company" ]
     do
          #===> variable company used when calling setup_called.py script
          echo
          echo "What is your Company Name? No spaces, no special characters. This field will be used for Rainbow bubble creation and Notification workflow/APIs"
          read -p "Company Name : " company
          if [ -z "$company" ]
          then
               echo "Company Name cannot be empty"
               unset company
          elif ! [[ $company =~ $company_validation_check ]]
          then
               echo "The Company Name list doesn't correspond with what was expected (it should contain characters, digits, '-', '_' only), retry."
               unset company
          fi
     done

     echo
     echo "If you want to monitor specific patterns generated by OmniSwitches, please enter the list here.
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
          elif [ ! -z "$reponse" ]
          then
               reponse_tab+=("$reponse")
          fi
     done

     #===> variable login='admin', prefilled with value "admin", means if the user press enters we use the default value
     echo
     echo "What are the OmniSwitches credentials?"
     default="admin"
     read -p "Login [default="$default"] : " login_switch 
     login_switch=${login_switch:-$default}

     #===> variable password='switch', prefilled with value "admin", means if the user press enters we use the default value

     default="switch"
     read -p "Password [default="$default"] : " pass_switch
     pass_switch=${pass_switch:-$default}

     while [[ $yn != "Y" && $yn != "N" && $yn != "y" && $yn != "n" ]]
     do
     read -p "Do you want to add monitoring for Stellar WLAN APs ? (Y/N) " yn
     case $yn in
               [Nn]* ) ap="0" ;;
               [Yy]* ) ap="1"
                    echo "What are the Stellar AP credentials for SSH?"
                    login_AP="support"
                    read -p "Password : " pass_AP
                    read -p "Technical Support code : " tech_pass
                    echo
                    echo "If you want to monitor specific patterns generated by Stellar APs, please enter the list here.
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
                         if [ "$reponse_AP" == "stop" ]
                         then
                              echo 
                              break
                         fi
                         if [ ! -z "$reponse_AP" ] && [[ ! " ${reponse_tab[*]} " =~ " ${reponse_AP} " ]]
                         then
                              reponse_tab_AP+=("$reponse_AP")
                         fi
                    done  ;;


               * ) echo "Please answer Y or N.";;
     esac

     done
     unset yn


     # Please provide the Server log ip address on which you want receive logs.

     while [ -z "$ip_server_log" ]
     do
     read -p "# Please provide the Server log's IP Address on which you want to receive syslogs. :  " ip_server_log
     if [ -z "$ip_server_log" ]
     then
          echo "Server log IP Address cannot be empty"
     elif ! [[ $ip_server_log =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]
     then
          echo "The IP Address doesn't correspond with what was expected, please retry."
          unset ip_server_log

     fi
     done

     # Please provide the Networks allow to send logs with the format subnet/netmask
     echo
     while [ -z "$ip_allows" ]
     do
     echo  "Please provide the network subnets you want to allow for sending syslogs with the format subnet/netmask if you have more than 1, separate with a comma (,). " 
     read -p "(ex : 10.0.0.0/16, 192.168.1.1/24, 172.16.20.0/16) :  " ip_allows
     if [ -z "$ip_allows" ]
     then
          echo "This field cannot be empty"

     elif ! [[ $ip_allows =~ (([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2}, ?)*(([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2})$ ]]
     then
          echo "The IP Address list doesn't correspond with what was expected, please retry."
          unset ip_allows
     fi
     done
}



if [ -f $ALE_conf ]; then
     yz=""
     while [[ $yz != "Y" && $yz != "N" && $yz != "y" && $yz != "n" ]]
     do
          read -p "Configuration file already exists, do you want to keep the same configuration (user, password, emails...) (Y/N) :" yz
          case $yz in
                    [Nn]* ) configuration ;;
                    [Yy]* )
                         echo
                         while [ -z "$ip_allows" ]
                         do
                         echo  "Please provide the network subnets you want to allow for sending syslogs with the format subnet/netmask if you have more than 1, separate with a comma (,). " 
                         read -p "(ex : 10.0.0.0/16, 192.168.1.1/24, 172.16.20.0/16) :  " ip_allows
                         if [ -z "$ip_allows" ]
                         then
                              echo "This field cannot be empty"

                         elif ! [[ $ip_allows =~ (([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2}, ?)*(([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2})$ ]]
                         then
                              echo "The IP Address list doesn't correspond with what was expected, please retry."
                              unset ip_allows
                         fi
                         done
                         echo "If you want to monitor specific patterns generated by OmniSwitches, please enter the list here:
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
                              elif [ ! -z "$reponse" ]
                              then
                                   reponse_tab+=("$reponse")
                              fi
                         done
                         echo
                         echo "If you want to monitor specific patterns generated by Stellar APs, please enter the list here:
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
                              if [ -z "$reponse_AP" ] || [ "$reponse_AP" == "stop" ]
                              then
                                   echo 
                                   break
                              fi
                              if [ ! -z "$reponse_AP" ] && [[ ! " ${reponse_tab[*]} " =~ " ${reponse_AP} " ]]
                              then
                                   reponse_tab_AP+=("$reponse_AP")
                              fi
                         done
                         while IFS="," read -r rec_column1 rec_column2 rec_column3 rec_column4 rec_column5 rec_column6 rec_column7 rec_column8 rec_column9 rec_column10 rec_column11 rec_column12 rec_remaining
                         do
                              login_switch=$rec_column1
                              pass_switch=$rec_column2
                              mails=$rec_column3
                              rainbow_jid=$rec_column4
                              rainbow_jid2=$rec_column5
                              rainbow_jid3=$rec_column6
                              ip_server_log=$rec_column7
                              login_AP=$rec_column8
                              pass_AP=$rec_column9
                              tech_pass=$rec_column10
                              # random id - rec_column11
                              company=$rec_column12
                         done < $ALE_conf
                         if [ "$login_AP" != "" ]
                         then
                              ap=1
                         fi
                         ;;
                    * ) echo "Please answer Y or N.";;
          esac
     done
else
     configuration
fi

if [ -z "$rainbow_jid" ]
then
     echo ""
     rainbow_jid="default@openrainbow.com"
     echo "Creating a mock Rainbow JID for Rainbow JID 1 == $rainbow_jid, as it can't be empty."
fi

echo
echo -e "\e[32mSummary of your informations:\e[39m"
echo "   "
echo "OmniSwitches Login: $login_switch"
echo "OmniSwitches Password: $pass_switch"
echo "Your Rainbow JID 1:  $rainbow_jid"
echo "Your Rainbow JID 2:  $rainbow_jid2"
echo "Your Rainbow JID 3:  $rainbow_jid3"
echo
echo "Your Emails addresses: $mails"
echo "Your company name: $company"
echo "Your OmniSwitches patterns: "

for rep in "${reponse_tab[@]}"
do
        echo "- $rep"
done
echo
echo "Networks allowed: $ip_allows"
echo
if [ "$ap" == "1" ]
then
echo "Stellar APs Login: support"
echo "Stellar APs Password: $pass_AP"
echo "Stellar APs technical support code: $tech_pass"
echo "Your Stellar APs patterns: "
echo
for rep in "${reponse_tab_AP[@]}"
do
        echo "- $rep"
done
fi

while [[ $yn != "Y" && $yn != "N" && $yn != "y" && $yn != "n" ]]
do
  read -p   "Do you want to confirm and proceed for installation? (Y/N):" yn
    case $yn in
          [Nn]* ) exit 1 ;;
          [Yy]* ) echo "$login_switch,$pass_switch,$mails,$rainbow_jid,$rainbow_jid2,$rainbow_jid3,$ip_server_log,$login_AP,$pass_AP,$tech_pass,$random_id,$company," > $ALE_conf;;
          * ) echo "Please answer Y or N.";;
    esac
done

#Then script will do:
#- installation/configuration of rsyslog.conf
#- installation/configuration of logrotate
#- installation/configuration of iptables
#- installation/configuration of sshpass, python others


echo
echo -e "\e[32mConfiguration of Rsyslog..\e[39m"
echo

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

template (name=\"devicelogradius\" type=\"string\"
     string=\"/var/log/devices/lastlog_radius_down.json\")

template (name=\"devicelogstorm\" type=\"string\"
     string=\"/var/log/devices/lastlog_storm.json\")

template (name=\"devicelogfan\" type=\"string\"
     string=\"/var/log/devices/lastlog_fan.json\")

template (name=\"devicelogstp\" type=\"string\"
     string=\"/var/log/devices/lastlog_stp.json\")

template (name=\"deviceloghighcpu\" type=\"string\"
     string=\"/var/log/devices/lastlog_high_cpu.json\")

template (name=\"deviceloghighmemory\" type=\"string\"
     string=\"/var/log/devices/lastlog_high_memory.json\")

template (name=\"deviceloglanpower\" type=\"string\"
     string=\"/var/log/devices/lastlog_lanpower.json\")

template (name=\"devicelogiot\" type=\"string\"
     string=\"/var/log/devices/lastlog_iot.json\")

template (name=\"deviceloglinkagg\" type=\"string\"
     string=\"/var/log/devices/lastlog_linkagg.json\")
     
template (name=\"customlog\" type=\"string\"
     string=\"/var/log/devices/lastlog_custom.json\")


template(name=\"json_syslog\"
  type=\"list\") {
    constant(value=\"{\")
    constant(value=\"\\"\"@timestamp\\"\":\\"\""\")       property(name=\"timereported\" dateFormat=\"rfc3339\")
      constant(value=\"\\\",\\"\""type\\\":\\"\""syslog_json\")
      constant(value=\"\\\",\\"\"""relayip\\\":\\"\""\"")       property(name=\"fromhost-ip\")
      constant(value=\"\\\",\\"\"""hostname\\\":\\"\""\"")      property(name=\"hostname\")
      constant(value=\"\\\",\\"\"""message\\\":\\"\""\"")       property(name=\"rawmsg\" format=\"json\")
      constant(value=\"\\\",\\"\"""end_msg\\\":\\"\""\"") 
    constant(value=\"\\"\"}\\\n\"")
}

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
# Emergencies are sent to everybody logged in.
#
*.emerg                         :omusrmsg:*
#############
## GARBAGE ##
#############
:msg, contains, \"FIPS\" stop
:msg, contains, \"integrity test passed\" stop
:msg, contains, \"DBG3\" stop

if \$msg contains 'ConsLog' then {
     action(type=\"omfile\" File=\"/var/log/devices/Console_Logs.log\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     stop
}

# if a syslog message contains \"error\" string, we redirect to a specific log
#:msg, contains, \"error\"         /var/log/syslog-error.log
*.* ?DynamicFile;json_syslog

############### Preventive Maintenance Rules ###############


#### LAN - Core DUMP rule #########
#### This rule is missing "ALRT:" in the rule ####
if \$msg contains 'PMD generated at' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpmd\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_pmd\" binary=\"$dir/support_switch_pmd.py \\\"PMD generated at\\\"\")
     stop
}

#### LAN - Rules Port Flapping ######
#### This rule is missing or part of "niEsmSendLinkStatusChgMsg" ####
if \$msg contains 'pmnHALLinkStatusCallback:' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogflapping\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_flapping\" binary=\"$dir/support_switch_port_flapping.py \\\"pmnHALLinkStatusCallback:\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### LAN - Rules DDOS #####
if \$msg contains 'Denial of Service attack detected:' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogddosdebug\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ddos\" binary=\"$dir/support_switch_debugging_ddos.py \\\"Denial of Service attack detected:\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'ALV4 event: PSCAN' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogddosip\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ddos\" binary=\"$dir/support_switch_enable_qos.py \\\"ALV4 event: PSCAN\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}


#### Rule Authentication Failure - LAN ####
if \$msg contains 'SES AAA' and \$msg contains 'Failed' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogauthfail\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_auth_failure\" binary=\"$dir/support_switch_auth_fail.py \\\"SES AAA;and;Failed\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rule Network Loop - LAN ####
if \$msg contains 'Buffer list is empty' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelog\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_loop\" binary=\"$dir/support_switch_debugging.py \\\"Buffer list is empty\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'slnHwlrnCbkHandler' and \$msg contains 'port' and \$msg contains 'bcmd' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogloop\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_loop\" binary=\"$dir/support_switch_port_disable.py \\\"slnHwlrnCbkHandler;and;port;and;bcmd\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Rule Port Violation - LAN ####
if \$msg contains 'Violation set' or \$msg contains 'in violation' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogviolation\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_violation\" binary=\"$dir/support_switch_violation.py \\\"Violation set;or;in violation\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### VC Unit DOWN - LAN ####
if \$msg contains 'bootMgrVCMTopoDataEventHandler' and \$msg contains 'no longer' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py \\\"bootMgrVCMTopoDataEventHandler;and;no longer\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'cmmEsmHandleNIDown' and \$msg contains 'chassis' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py \\\"cmmEsmHandleNIDown;and;chassis\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'Sending VC Takeover to NIs and applications' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py \\\"Sending VC Takeover to NIs and applications\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

if \$msg contains 'The switch was restarted by' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogvcdown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_vc_cmm\" binary=\"$dir/support_switch_vc_down.py \\\"The switch was restarted by\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### SPB Adjacency DOWN - LAN ####
if \$msg contains 'ADJACENCY INFO: Lost L1 adjacency' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogspb\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_spb\" binary=\"$dir/support_switch_spb.py \\\"ADJACENCY INFO: Lost L1 adjacency\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### OSPF Neighbor DOWN - LAN ####
if \$msg contains 'OSPF neighbor state change' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogospf\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ospf\" binary=\"$dir/support_switch_ospf.py \\\"OSPF neighbor state change\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### BGP Neighbor DOWN - LAN ####
if \$msg contains 'bgp' and \$msg contains 'transitioned to' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogbgp\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_bgp\" binary=\"$dir/support_switch_bgp.py \\\"bgp;and;transitioned to\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### DDM Threshold reached - LAN ####
if \$msg contains 'cmmEsmCheckDDMThresholdViolations' then {
	action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
	action(type=\"omfile\" DynaFile=\"devicelogddm\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
	action(type=\"omprog\" name=\"support_lan_generic_ddm\" binary=\"$dir/support_switch_ddm.py \\\"cmmEsmCheckDDMThresholdViolations\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
stop
}

#### Storm Threshold Violation - LAN ####
if \$msg contains 'Storm Threshold violation' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogstorm\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_storm.py \\\"Storm Threshold violation\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### Radius Server status - LAN ####
if \$msg contains 'radCli' and \$msg contains 'RADIUS' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogradius\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_radius.py \\\"radCli;and;RADIUS\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

##### WLAN Rules for handling all abnormal operations #####
if \$msg contains 'TARGET ASSERTED' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_target_asserted\" binary=\"$dir/support_wlan_generic.py \\\"target_asserted\\\" \\\"TARGET ASSERTED\\\"\")
     stop
}

if \$msg contains 'Internal error' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_internal_error\" binary=\"$dir/support_wlan_generic.py \\\"internal_error\\\" \\\"Internal error\\\"\")
     stop
}

##### WLAN Rules for Stellar AP upgrade or reboot #####
if \$msg contains 'sysreboot' then {
     \$RepeatedMsgReduction on
     if \$msg contains 'Power Off' then {
          action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
          action(type=\"omprog\"  binary=\"$dir/support_wlan_generic.py \\\"unexpected_reboot\\\" \\\"sysreboot;and;Power Off\\\"\")
          stop
     }
     else {
          action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
          action(type=\"omprog\" name=\"support_wlan_generic_reboot\" binary=\"$dir/support_wlan_generic.py \\\"reboot\\\" \\\"sysreboot\\\"\")
          stop
     }
}

if \$msg contains 'enter in sysupgrade' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_upgrade\" binary=\"$dir/support_wlan_generic.py \\\"upgrade\\\" \\\"enter in sysupgrade\\\"\")
     stop
}

##### WLAN Rules for handling all abnormal operations #####
if \$msg contains 'Fatal exception' or \$msg contains 'Kernel panic' or \$msg contains 'KERNEL PANIC' or \$msg contains 'Exception stack' or \$msg contains 'parse condition rule is error' or \$msg contains 'core-monitor reboot' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_exception\" binary=\"$dir/support_wlan_generic.py \\\"exception\\\" \\\"Fatal exception;or;Kernel panic;or;KERNEL PANIC;or;Exception stack;or;parse condition rule is error;or;core-monitor reboot\\\"\")
     stop
}

if \$msg contains 'Unable to handle kernel' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"devicelogdeauth\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_wlan_generic_kernel_panic\" binary=\"$dir/support_wlan_generic.py \\\"kernel_panic\\\" \\\"Unable to handle kernel\\\"\")
     stop
}

#### PS Unit DOWN - LAN ####
if \$msg contains 'Power Supply' and \$msg contains 'Removed' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpowersupplydown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_ps\" binary=\"$dir/support_switch_power_supply.py \\\"Power Supply;and;Removed\\\"\")
     stop
}

if \$msg contains 'Power supply' and \$msg contains 'inoperable' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpowersupplydown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_switch_queue_ps\" binary=\"$dir/support_switch_power_supply.py \\\"Power Supply;and;inoperable\\\"\")
     stop
}

if \$msg contains 'operational state changed to UNPOWERED' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogpowersupplydown\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_switch_queue_ps\" binary=\"$dir/support_switch_power_supply.py \\\"operational state changed to UNPOWERED\\\"\")
     stop
}

#### LANPOWER - LAN ####
if \$msg contains 'FAULT State change' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"deviceloglanpower\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_lanpower.py \\\"FAULT State change\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### LINKAGG DOWN - LAN ####
if \$msg contains 'Receive agg port leave request' and not (\$msg contains 'Port Leave') then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"deviceloglinkagg\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_linkagg\" binary=\"$dir/support_switch_linkagg.py \\\"Receive agg port leave request;and;Port Leave\\\"\")
     stop
}

#### Rule Duplicate IP Address - LAN ####
if \$msg contains 'duplicate IP address' or \$msg contains 'Duplicate IP address' or \$msg contains 'arp info overwritten' then {
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogdupip\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" name=\"support_lan_generic_dupip\" binary=\"$dir/support_switch_duplicate_ip.py \\\"duplicate IP address;or;Duplicate IP address;or;arp info overwritten\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
     stop
}

#### IoT Profiling - LAN ####
if \$msg contains 'Unable to connect' and \$msg contains 'mqttd' then {
     \$RepeatedMsgReduction on
     action(type=\"omfile\" DynaFile=\"deviceloghistory\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omfile\" DynaFile=\"devicelogiot\" template=\"json_syslog\" DirCreateMode=\"0755\" FileCreateMode=\"0755\")
     action(type=\"omprog\" binary=\"$dir/support_switch_iot.py \\\"Unable to connect;and;mqttd\\\"\" queue.type=\"LinkedList\" queue.size=\"1\" queue.workerThreads=\"1\")
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
    echo "No parsing error found on Configuration Files"
fi

echo
echo -e "\e[32mRsyslog configuration completed.\e[39m"
echo

echo
echo -e "\e[32mConfiguration of logrotate..\e[39m"
echo

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
#    postrotate
#         sudo systemctl kill -s HUP rsyslog.service
#    endscript
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
echo -e "\e[32mLogrotate configuration completed.\e[39m"
echo


ver=$(python3 -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
if [ "$ver" -lt "38" ]
then
    echo
    echo -e "\e[32mThis script requires python 3.8 or greater version..\e[39m"
    echo
    
    echo
    echo -e "\e[32mPython 3.8 installation started..\e[39m"
    echo
    echo "Current user: `whoami`"
    echo "Python 3.8 package is downloaded on current user Home directory"
    
    sudo apt-get -qq -y update
    sudo apt-get -qq -y install build-essential openssl openssl-dev*
    sudo apt-get -qq -y install checkinstall libreadline-gplv2-dev libncursesw5-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
    sudo apt-get -qq -y install libssl-dev*
    
    cd /usr/src
    curl https://www.openssl.org/source/openssl-1.1.1c.tar.gz | tar xz
    cd openssl-1.1.1c/
    ./config shared --prefix=/usr/local/
    make
    sudo make install
    
    export LDFLAGS="-L/usr/local/lib/"
    export LD_LIBRARY_PATH="/usr/local/lib/"
    export CPPFLAGS="-I/usr/local/include -I/usr/local/include/openssl"
    
    wget --inet4-only https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz
    tar -xvf Python-3.8.0.tgz
    cd Python-3.8.0
    ./configure --with-openssl=/usr/src/openssl-1.1.1c --enable-shared
    make 
    make test

    export LDFLAGS="-L/usr/local/lib/"
    export LD_LIBRARY_PATH="/usr/local/lib/"
    export CPPFLAGS="-I/usr/local/include -I/usr/local/include/openssl"
    
    make install
    
    # Steps from here are to enable other libraries in linux to 
    # access the shared python libraries.
    
    cd /usr/local/lib/
    sudo cp libpython3.so /usr/lib64/
    sudo cp libpython3.so /usr/lib
    sudo cp libpython3.8m.so.1.0 /usr/lib64/
    sudo cp libpython3.8m.so.1.0 /usr/lib/
    cd /usr/lib64
    ln -s libpython3.8m.so.1.0 libpython3.8m.so
    cd /usr/lib
    ln -s libpython3.8m.so.1.0 libpython3.8m.so
    
    sudo python3 -m pip install --upgrade pip
    
    echo
    echo -e "\e[32mPython3.8 Installation Completed.\e[39m"
    echo

else
    echo
    echo -e "\e[32mPython 3.8 or above detected, installation is not required.\e[39m"
    echo
fi

sudo apt-get -qq -y install python3-pip
sudo apt-get -qq -y install python3 --upgrade pip
sudo python3 -m pip install -q pysftp 
sudo apt-get -qq -y install tftpd-hpa 


echo
echo -e "\e[32mInstallation and configuration of service for OmniSwitches monitoring..\e[39m"
echo

sudo echo "[Unit]
Description=Python exporter

[Service]
ExecStart=python3 $dir/support_switch_usage.py
Restart=on-failure
User=admin-support
Group=admin-support
WorkingDirectory=$dir/

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/python_exporter.service
sudo systemctl daemon-reload
sudo systemctl start python_exporter.service
sudo systemctl enable  python_exporter.service

echo
echo -e "\e[32mPython exporter service started to monitor OmniSwitches completed.\e[39m"
echo

echo
echo -e "\e[32mCreating syslog directory..\e[39m"
echo

sudo mkdir /var/log/devices/ >& /dev/null
sudo touch /var/log/devices/logtemp.json
sudo chmod 755 /var/log/devices/
sudo chown admin-support:admin-support /var/log/devices/

echo
echo -e "\e[32mDevices syslog directory /var/log/devices/ created.\e[39m"
echo

echo
sleep 2
echo -e "\e[32mTFTP Server installation..\e[39m"
echo

echo "# /etc/default/tftpd-hpa

TFTP_USERNAME=\"tftp\"
TFTP_DIRECTORY=\"/tftpboot\"
TFTP_ADDRESS=\"0.0.0.0:69\"
TFTP_OPTIONS=\"-l -c -s\" " > /etc/default/tftpd-hpa

sudo mkdir /tftp
sudo chown tftp:tftp /tftp
sudo chmod 777 -R /tftpboot

sudo systemctl restart tftpd-hpa
STATUS="$(sudo systemctl is-active tftpd-hpa.service)"
if [ "${STATUS}" = "active" ]; then
    echo -e "\e[32mtftpd-hpa.service is active\e[39m"
else 
    echo -e "\e[31mtftpd-hpa.service is not active\e[39m"
fi

echo
echo -e "\e[32mTFTP Server Installation Completed.\e[39m"
echo

echo
echo -e "\e[32mConfiguring SSH Port 22 to 2222..\e[39m"
echo

sudo apt-get -qq -y install openssh-server
sudo apt-get -qq -y install ufw
sudo sed -i 's/#Port 22/Port 2222/g' /etc/ssh/sshd_config
sudo systemctl restart ssh
sudo ufw enable
sudo ufw allow 2222/tcp

echo
echo -e "\e[32mConfiguring SSH Port 22 to 2222 is done.\e[39m"
echo

echo
echo -e "\e[32mInstalling MySQL..\e[39m"
echo

sudo apt-get -qq -y install default-mysql-server

echo
echo -e "\e[32mInstallation of MYSQL is done.\e[39m"
echo

echo
echo -e "\e[32mConfiguring MYSQL..\e[39m"
echo
# Added to check, existing database and user - for deletion
if mysql -u root -e 'use aledb'; then
  echo "ale database found, to continue installation, you need to delete database"
  echo "Do you want to delete ? (Y/N)"
  read dec
  if [ $dec == "Y" ]; then
  	mysql -u root<<EOF
  	DROP DATABASE aledb;
	DROP USER IF EXISTS 'aletest'@'localhost';

EOF
        echo "Existing ale database deleted"
  else
  	echo "Installation stopped"
  	exit 1

  fi
fi
#end of deletion of database and user
sudo mysql -u root<<EOF
CREATE DATABASE aledb;
CREATE USER 'aletest'@'localhost' IDENTIFIED BY 'welcome@123456';
GRANT ALL PRIVILEGES ON aledb.* TO 'aletest'@'localhost';
EOF

echo
echo -e "\e[32mConfiguring MYSQL is done.\e[39m"
echo

echo
echo -e "\e[32mInstalling required packages..\e[39m"
echo

echo
echo "This will take a while to install the required packages and you can ignore the depricate warnings."
echo

# sudo pip install -q asgiref==3.4.1
# sudo pip install -q certifi==2021.10.8
# sudo pip install -q cffi==1.15.0
# sudo pip install -q charset-normalizer==2.0.11
# sudo pip install -q cryptography==36.0.1
# sudo pip install -q Django==4.0.1
# sudo pip install -q django-auto-logout==0.5.0
# sudo pip install -q django-cors-headers==3.11.0
# sudo pip install -q django-filter==21.1
# sudo pip install -q django-jsonfield==1.4.1
# sudo pip install -q django-rest-knox==4.1.0
# sudo pip install -q djangorestframework==3.13.1
# sudo pip install -q django-request-id==1.0.0
# sudo pip install -q idna==3.3
# sudo pip install -q Markdown==3.3.6
# sudo apt-get -qq -y install python3-dev
# sudo pip install -q lxml==4.8.0
# sudo apt-get -qq -y install default-libmysqlclient-dev
# sudo pip install -q mysqlclient==2.1.0
# sudo pip install -q pycparser==2.21
# sudo pip install -q pytz==2021.3
# sudo pip install -q requests==2.27.1
# sudo pip install -q launchpadlib==1.10.13
# sudo pip install -q six==1.16.0
# sudo pip install -q sqlparse==0.4.2
# sudo pip install -q tzdata==2021.5
# sudo pip install -q urllib3==1.26.8
# sudo pip install -q pyufw==0.0.3
# sudo pip install -q openpyxl==3.0.9
# sudo pip install -q pandas==1.4.1
# sudo pip install -q psutil==5.9.0
# sudo pip install -q mysql-connector-python==8.0.28
# sudo apt-get -qq -y install sshpass
# sudo apt-get -qq -y install gnome-keyring
# sudo apt-get -qq -y install gnupg

error_exit() {
    echo -e "\e[31mError: $1.\e[39m"
    echo -e "\e[31mError occurred while installing the required packages. So terminating the installation process. Please re-run the setup once the issue is resolved.\e[39m"
    
    # Destroy progress bar
     destroy_scroll_area
    
    exit 1
}

main() {
     # Make sure that the progress bar is cleaned up when user presses ctrl+c
     enable_trapping

     # Create progress bar
     setup_scroll_area

     # Downloading the softwares
     softwares=( 
          "python3-dev" "default-libmysqlclient-dev" "sshpass" "gnome-keyring" "gnupg"
     )
     length=${#softwares[@]}

     for ((i = 0 ; i <= $length - 1 ; i++))
     do
        percentage_covered=$(( (i+1)*100/length ))
        # echo "percentage covered: $percentage_covered"

        draw_progress_bar $percentage_covered
        echo "Downloading Software: ${softwares[i]}"
        sudo apt-get -qq -y install ${softwares[i]} || error_exit "Unable to Download the Software: ${softwares[i]}"
        sleep 0.5

        echo " "
     done
    
     softwares=( 
          "asgiref==3.4.1" "certifi==2021.10.8" "cffi==1.15.0" "charset-normalizer==2.0.11" "cryptography==36.0.1" 
          "Django==4.0.1" "django-auto-logout==0.5.0" "django-cors-headers==3.11.0" "django-filter==21.1" "django-jsonfield==1.4.1" 
          "django-rest-knox==4.1.0" "djangorestframework==3.13.1" "django-request-id==1.0.0" "idna==3.3" "Markdown==3.3.6" 
          "lxml==4.8.0" "mysqlclient==2.1.0" "pycparser==2.21" "pytz==2021.3" "requests==2.27.1" "launchpadlib==1.10.13" "six==1.16.0" 
          "sqlparse==0.4.2" "tzdata==2021.5" "urllib3==1.26.8" "pyufw==0.0.3" "openpyxl==3.0.9" "pandas==1.4.1" "psutil==5.9.0" 
          "mysql-connector-python==8.0.28" 
     )
     length=${#softwares[@]}

     for ((i = 0 ; i <= $length - 1 ; i++))
     do
        percentage_covered=$(( (i+1)*100/length ))
        # echo "percentage covered: $percentage_covered"

        draw_progress_bar $percentage_covered
        echo "Downloading Software: ${softwares[i]}"
        sudo pip install -q ${softwares[i]}  || error_exit "Unable to Download the Software: ${softwares[i]}"
        sleep 0.5

        echo " "
     done

     # Destroy progress bar
     destroy_scroll_area
}

main

echo
echo -e "\e[32mInstallation of required packages is done.\e[39m"
echo

echo
echo -e "\e[32mInstalling GUI Applications required..\e[39m"
echo

cd $APP_DIR
sudo apt-get update
sudo apt-get install curl
curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get -qq -y install nodejs
sudo npm install -g @angular/cli
sudo npm install --legacy-peer-deps
sudo npm config set legacy-peer-deps true
sudo npm i
# ng add @angular/material
sudo npm install --save @angular/material @angular/cdk @angular/animations

echo
echo -e "\e[32mInstallation of GUI Apllications is done.\e[39m"
echo

echo
echo -e "\e[32mConfiguring IP Tables..\e[39m"
echo

sleep 30s

echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections

sudo apt-get -qq -y install iptables-persistent

sudo iptables -I INPUT -p udp --dport 10514 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 2222 -j ACCEPT
sudo iptables -I INPUT -p udp --dport 69 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 3000 -j ACCEPT
# for django port : 8000
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
# for angular port : 4200
sudo iptables -I INPUT -p tcp --dport 4200 -j ACCEPT

sudo ip6tables -I INPUT -p udp --dport 10514 -j ACCEPT
sudo ip6tables -I INPUT -p tcp --dport 2222 -j ACCEPT
sudo ip6tables -I INPUT -p udp --dport 69 -j ACCEPT
sudo ip6tables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo ip6tables -I INPUT -p tcp --dport 3000 -j ACCEPT
# for django port : 8000
sudo ip6tables -I INPUT -p tcp --dport 8000 -j ACCEPT
# for angular port : 4200
sudo ip6tables -I INPUT -p tcp --dport 4200 -j ACCEPT

sudo /sbin/iptables-save | sudo tee /etc/iptables/rules.v4
sudo /sbin/ip6tables-save | sudo tee /etc/iptables/rules.v6

sudo /sbin/iptables-save
sudo /sbin/ip6tables-save

echo
echo -e "\e[32mIP Tables configuration is done.\e[39m"
echo

echo
echo -e "\e[32mStarting the Front-end services..\e[39m"
echo

cd $APP_DIR
chmod 755 $APP_DIR ale_angular_app_service.sh

sudo echo "[Unit]
Description=ALE Angular Application Service

[Service]
ExecStart=/bin/bash $APP_DIR/ale_angular_app_service.sh
Restart=on-failure
User=root
WorkingDirectory=$APP_DIR/

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/ale_angular_app_service.service
sudo systemctl daemon-reload
sudo systemctl start ale_angular_app_service.service
sudo systemctl enable ale_angular_app_service.service

echo
echo -e "\e[32mFront-end services started.\e[39m"
echo


echo
echo -e "\e[32mStarting the Back-end services..\e[39m"
echo

echo "During this process we need to create a superuser and need to remember the details. You can note it down the details"
sleep 5s

cd $APP_DIR/ALE_v2
chmod 755 $APP_DIR/ALE_v2/ale_python_app_service.sh
chmod 755 $APP_DIR/ALE_v2/sql_stmts.sql
chmod 755 $APP_DIR/ALE_v2/rules_sql_stmts.sql

sudo python3 manage.py makemigrations
sudo python3 manage.py migrate
sudo python3 manage.py createsuperuser
#sudo mysql -u aletest -pwelcome@123456 aledb <sql_stmts.sql
sudo mysql -u aletest -pwelcome@123456 aledb -e "set @companyname=\"$company\"; set @inputed_jid=\"$rainbow_jid\"; source sql_stmts.sql;"

sudo echo "[Unit]
Description=ALE Python Application Service

[Service]
ExecStart=/bin/bash $APP_DIR/ALE_v2/ale_python_app_service.sh
Restart=on-failure
User=root
WorkingDirectory=$APP_DIR/ALE_v2

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/ale_python_app_service.service
sudo systemctl daemon-reload
sudo systemctl start ale_python_app_service.service
sudo systemctl enable ale_python_app_service.service

echo
echo -e "\e[32mBack-end services started.\e[39m"
echo


counter=33
for rep in "${reponse_tab[@]}"
do
     rule="if \$msg contains '"$rep"'"
     sudo mysql -u aletest -pwelcome@123456 aledb -e "set @rule_name=\"$rep\"; set @counter=\"$counter\"; source rules_sql_stmts.sql;"
     sudo python3 $dir/opt_pattern.py "$rep"
     counter=$((counter+1))
done


for rep in "${reponse_tab_AP[@]}"
do
     rule="if \$msg contains '"$rep"'"
     sudo mysql -u aletest -pwelcome@123456 aledb -e "set @rule_name=\"$rep\"; set @counter=\"$counter\"; source rules_sql_stmts.sql;"
     sudo python3 $dir/opt_pattern_AP.py "$rep"
     counter=$((counter+1))
done
echo "Sending notification to ALE DevOPS team for setup VNA application"
sudo python3 $dir/setup_called.py "$login_switch" "$pass_switch" "$mails" "$rainbow_jid" "$rainbow_jid2" "$rainbow_jid3" "$ip_server_log" "$login_AP" "$pass_AP" "$tech_pass" "$random_id" "$company"

sudo systemctl daemon-reload
sudo systemctl restart python_exporter.service
sudo systemctl restart ale_angular_app_service.service
sudo systemctl restart ale_python_app_service.service


echo
echo -e "\e[32mConfiguring the ALE Cloud.\e[39m"
echo

sudo apt-get -qq -y update
sudo apt-key add $APP_DIR/public.gpg_ALE_Preventive_Maintenance.key

filename='/etc/apt/sources.list'
echo "deb https://preventive_maintenance:xfZY2kzU@repo.myovcloud.com/repository/apt-hosted xenial main" >> $filename

filename='/etc/apt/apt.conf.d/apt-nexus-repo-cert'
echo "Acquire::https::repo.myovcloud.com::Verify-Peer \"false\";" >> $filename

sudo apt-get update
sudo apt-get install preventivemaintenance

# sudo chmod 755 $APP_DIR ale_cloud_integration.py
chmod 755 $APP_DIR/ALE_v2/ale_cloud_integration.py

# start of crontab creation for ale cloud integration #
sudo crontab -l > cronjobentry
filepath="0 1 * * * sudo python3 $APP_DIR/ALE_v2/ale_cloud_integration.py > $APP_DIR/ALE_v2/ale_cloud_integration.log 2>&1"
echo "$filepath">> cronjobentry
sudo crontab cronjobentry
rm cronjobentry
# end of crontab creation

echo
echo -e "\e[32mConfiguring the ALE Cloud Completed.\e[39m"
echo

echo
echo -e "\e[32mConfiguring for enabling the syslogs on OmniSwitches Started.\e[39m"
echo

echo "Please wait while enabling of syslogs on OmniSwitches is going."
sudo python3 $dir/enable_syslogs.py

echo
echo -e "\e[32mConfiguring for enabling the syslogs on OmniSwitches Completed.\e[39m"
echo

echo
echo -e "\e[32mTFTP Server Status..\e[39m"
echo

echo "Press 'q' key to exit from Status window of tftpd-hpa service"
echo
sudo systemctl status tftpd-hpa.service
echo


echo -e "\e[32mSyslogs received from allowed networks are redirected to /var/log/devices/<device_hostname>/ directories\e[39m"
echo "     "
echo -e "\e[32mWhen a syslog matches with application rule a JSON file is created in /var/log/devices for post processing by application\e[39m"
echo "     "
echo -e "\e[32mScripts and configuration files are stored in $dir/\e[39m"
echo "     "
echo -e "\e[32mPlease ensure the OmniSwitches as well as Stellar APs are sending syslog messages to UDP Port 10514\e[39m"
echo "     "
echo -e "\e[32mOmniSwitches CLI command: swlog output socket $ip_server_log:10514 <vrf_name> is pushed on OmniSwitches listed into the Devices.csv file\e[39m"
echo "     "
echo -e "\e[32mThe SSH Port is modified to 2222. Please disconnect the connection and try to connect using Port 2222 for SSH\e[39m"
echo "     "
echo -e "\e[32mOn OmniVista 2500, go to Network -> AP Registration -> AP Group, select the AP Group and configure the Syslog Server IP: $ip_server_log and Port: 10514\e[39m"
echo "     "
echo -e "\e[32mTo connect with the UI, launch http://localhost:4200. To login please use the email and password, that you have entered when creating the superuser.\e[39m" 



echo
echo
echo "##############################################################################"
echo "#                                                                            #"
echo "####################   The installation is complete   ########################"
echo "#                                                                            #"
echo "##############################################################################"
echo
echo
