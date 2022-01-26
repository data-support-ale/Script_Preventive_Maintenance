#! /bin/bash


while IFS="," read -r rec_column1 rec_column2 rec_column3 rec_column4 rec_remaining
do
  if [ "$rec_column4" != "" ]
  then
      echo -e "\e[31mVNA already setup"
  else
      echo -e "\e[31mVNA setting up"
  fi
done < /opt/ALE_Script/ALE_script.conf