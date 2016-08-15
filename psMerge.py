#!/usr/bin/env python

import sys, getopt

import numpy as np

from toasty import toast

def weightedMerge(mosaic):
    subtile = (mosaic[::2, ::2] +
               mosaic[1::2, ::2] +
               mosaic[::2, 1::2] +
               mosaic[1::2, 1::2])
    extraBlack = (subtile < 1) # assumes that tile is greyscale and 0=black, 1=white
    subtile[extraBlack] = subtile[extraBlack]/3 # throw out one black pixel (weighting towards white)
    subtile[extraBlack] = subtile[extraBlack]/4

    return subtile


def usage():
    print("psMerge.py -b <base directory> -d <depth> [-l <top level> -t <tile>]")

def psMerge(baseDir,depth, topLevel, toastTile):
    toast(baseDir,depth,baseDir,top_layer=topLevel,toast_tile=toastTile) 


    
if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hb:d:l:t:",["help","basedir=","depth=","toplevel=","tile="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

        
    baseDir = ''
    depth = None
    topLevel = 4 # default is 4, since that works for AstroView
    toastTile = None

    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        if opt in ('-b','--basedir'):
            baseDir = arg
        if opt in ('-d','--depth'):
            try:
                depth = int(arg)
            except ValueError:
                print("Depth must be an integer (base 10 please)")
                sys.exit(2)
        if opt in ('-l','--toplevel'):
            try:
                topLevel = int(arg)
            except ValueError:
                print("Top level must be an integer (base 10 please)")
                sys.exit(2)
        if opt in ('-t','--tile'):
            try:
                toastTile = [int(x) for x in arg.split(',')]
            except ValueError:
                print("Toast tile must be of the form: depth,tx,ty")
                sys.exit(2)
            if len(toastTile) != 3:
                print("Toast tile must be of the form: depth,tx,ty")
                sys.exit(2)

    if not baseDir:
        print("Base directory containing base level of tile must be supplied for merge to run.")
        sys.exit(2)

    if not depth:
        print("Depth of base layer must be supplied.")
        sys.exit(2)        

    psMerge(baseDir,depth,topLevel,toastTile)
