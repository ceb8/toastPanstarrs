#!/usr/bin/env python

import sys, getopt,os

import numpy as np

from itertools import product
from subprocess import run
from skimage.io import imread,imsave

import warnings
warnings.filterwarnings("ignore", ".* is a low contrast image")

def colorize(depth,rDir,gDir,bDir,outDir,txrange,tyrange):
    for tx,ty in product(range(*txrange),range(*tyrange)):
        pth = '/' + str(depth) + '/' + str(ty) + '/' + str(ty) + '_' + str(tx) + '.png'
        if not (os.path.isfile(rDir + pth) and os.path.isfile(gDir + pth) and os.path.isfile(bDir + pth)):
            continue
        
        r = imread(rDir+pth)
        g = imread(gDir+pth)
        b = imread(bDir+pth)
        rgb = np.dstack((r,g,b))

        direc, _ = os.path.split(outDir+pth)
        if not os.path.exists(direc):
            os.makedirs(direc)
        imsave(outDir+pth, rgb)
        


def usage():
    print("psColorize.py -r <red directory> -g <green directory> -b <blue directory> -o <output directory> -d <depth> [-x <tile x range> -y <tile y range>]")

    
if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hr:g:b:o:d:x:y:",["help","reddir=","greendir=","bluedir=","depth=","txrange=","tyrange="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

        
    rDir = ''
    gDir = ''
    bDir = ''
    outDir = '.'
    depth = None
    txRange = None
    tyRange = None

    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        if opt in ('-r','--reddir'):
            rDir = arg
        if opt in ('-g','--greendir'):
            gDir = arg
        if opt in ('-b','--bluedir'):
            bDir = arg
        if opt in ('-o','--outdir'):
            outDir = arg
        if opt in ('-d','--depth'):
            try:
                depth = int(arg)
            except ValueError:
                print("Depth must be an integer (base 10 please)")
                sys.exit(2)
        if opt in ('-x','--txrange'):
            try:
                txRange = [int(x) for x in arg.split(',')]
            except ValueError:
                print("Range must be of the form: min,max")
                sys.exit(2)
            if len(txRange) != 2:
                print("Range must be of the form: min,max")
                sys.exit(2)            
        if opt in ('-y','--tyrange'):
            try:
                tyRange = [int(x) for x in arg.split(',')]
            except ValueError:
                print("Range must be of the form: min,max")
                sys.exit(2)
            if len(tyRange) != 2:
                print("Range must be of the form: min,max")
                sys.exit(2)

    if not (rDir and gDir and bDir):
        print("Directories containing greyscale images in the red, green, and blue bands must be supplied.")
        sys.exit(2)

    if not depth:
        print("Depth to be colorized must be supplied.")
        sys.exit(2)        

    maxTileDim = 2**depth
    if not txRange:
        txRange = maxTileDim
    if not tyRange:
        tyRange = maxTileDim

    if (depth > 8) and  (txRange == maxTileDim) and (tyRange == maxTileDim):
        print("You have requested colorization of all tiles at depth %d." % depth)
        print("This may take a while, please be patient, or start with a smaller section.")

    colorize(depth,rDir,gDir,bDir,outDir,txRange,tyRange)
