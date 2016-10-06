#!/bin/bash

# Usage: runPSMerge.sh toast/path

# User must supply the directory in which the bottom layer 
# of toast tiles reside (this is $1)

# This script divides the sky into 64 sections and merges them up to level 4
for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        nohup psMerge.py -b $1 -d 12 -l 4 -t 3,${TX},${TY} &
    done
done 
