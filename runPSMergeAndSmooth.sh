#!/bin/bash

# Usage: runPSMergeAndSmooth.sh TOASTDir

# Adding the paths to access conda python and toasty
export PATH="/usr/local/anaconda3/bin:$PATH"

source activate py2
export PYTHONPATH="/home/cbrasseur/toasty/bin/lib/python2.7/site-packages/:$PATH"

# This script divides the sky into 64 sections and de-speckles them them for layers 4-11

# 11
echo "Layer 11"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeBC.py -b $1 -d 12 -l 11 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 2048; TX+=32))
do
    TY=$((TX+32))
    psSmoothing.py -i $1 -o $1 -d 11 -x 0,2048 -y $TX,$TY -t & 
done 

wait

# 10
echo "Layer 10"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeBC.py -b $1 -d 11 -l 10 -t 3,${TX},${TY} &
    done
done

wait 

for ((TX=0; TX < 1024; TX+=16))
do
    TY=$((TX+16))
    psSmoothing.py -i $1 -o $1 -d 10 -x 0,1024 -y $TX,$TY -t & 
done

wait

# 9
echo "Layer 9"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeBC.py -b $1 -d 10 -l 9 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 512; TX+=16))
do
    TY=$((TX+16))
    psSmoothing.py -i $1 -o $1 -d 9 -x 0,512 -y $TX,$TY -s -t -e & 
done

wait

# 8
echo "Layer 8"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeBC.py -b $1 -d 9 -l 8 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 256; TX+=8))
do
    TY=$((TX+8))
    psSmoothing.py -i $1 -o $1 -d 8 -x 0,256 -y $TX,$TY -s -t -e & 
done

wait

# 7
echo "Layer 7"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeBC.py -b $1 -d 8 -l 7 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 128; TX+=4))
do
    TY=$((TX+4))
    psSmoothing.py -i $1 -o $1 -d 7 -x 0,128 -y $TX,$TY -s -t -e & 
done

wait

# 6
echo "Layer 6"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeNN.py -b $1 -d 7 -l 6 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 64; TX+=4))
do
    TY=$((TX+4))
    psSmoothing.py -i $1 -o $1 -d 6 -x 0,64 -y $TX,$TY -s -t -e & 
done

wait

# 5
echo "Layer 5"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeNN.py -b $1 -d 6 -l 5 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 32; TX+=8))
do
    TY=$((TX+8))
    psSmoothing.py -i $1 -o $1 -d 5 -x 0,32 -y $TX,$TY -e -t & 
done

wait

# 4
echo "Layer 4"

for ((TX=0; TX < 8; TX++))
do
    for((TY=0; TY < 8; TY++))
    do
        psMergeNN.py -b $1 -d 5 -l 4 -t 3,${TX},${TY} &
    done
done

wait

for ((TX=0; TX < 16; TX+=8))
do
    TY=$((TX+8))
    psSmoothing.py -i $1 -o $1 -d 4 -x 0,16 -y $TX,$TY  -e -t & 
done
