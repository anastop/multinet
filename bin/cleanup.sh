#!/usr/bin/env bash


pid_worker_arr=`sudo ps aux | grep python | grep worker`

if [ ${#pid_worker_arr[@]} -eq 0 ]; then
	for wpid in pid_worker_arr; do
	#	sudo kill -9 wpid
	done
fi


pid_master=`ps aux | grep python | grep master`

#kill -9 pid_master

sudo mn -c
#rm -rf /tmp/transfered_files
