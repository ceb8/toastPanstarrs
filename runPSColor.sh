#!/bin/bash

# Usage: runPSCOLOR.sh path/directoryPrefix

# Adding the paths to access conda python and toasty
export PATH="/usr/local/anaconda3/bin:$PATH"
export PYTHONPATH="/home/cbrasseur/toasty/bin/lib/python3.5/site-packages:$PATH"

# User must supply the path+directory prefix for the g,r,i,z
# band TOAST tiles (this is $1) (ex:/internal/data1/surveys/ps_)
# The colored tiles will be placed in {$1}color

# This script divides the sky into 64 sections and colorizes them
for ((TX=0; TX < 4096; TX+=64))
do
    TY=$((TX+64))
    OUT="color"
    nohup psColorize.py -b $1 -o $1$OUT -d 12 -x 0,4096 -y $TX,$TY  & 
done 
