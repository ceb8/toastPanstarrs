#!/bin/bash

# Usage: runPSTOAST.sh inputfile toast/path

# User must supply the file containing information about where to find
# image files (basically determining which band is being toasted)
# and the directory in which the toast tiles will be saved
# these are $1 and $2 respectively

# This script divides the sky into 64 sections and toasts them
for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        nohup psTOAST.py -i $1 -d 12 -o $2 -t 3,${TX},${TY} -r &
    done
done 
