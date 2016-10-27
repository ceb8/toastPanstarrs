#!/usr/bin/env python

import sys, getopt

import numpy as np

import time

from toasty import toast

from PIL import Image

def weightedMerge(mosaic):
    subtile = Image.fromarray(mosaic)
    subtile = subtile.resize((256,256),Image.BILINEAR)
    return np.asarray(subtile)


def psMerge(baseDir,depth, topLevel, toastTile):
    toast(baseDir,depth,baseDir,top_layer=topLevel,merge=weightedMerge,toast_tile=toastTile) 

    
def usage():
    print("psMerge.py -b <base directory> -d <depth> [-l <top level> -t <tile>]")

    
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
        usage()
        sys.exit(2)

    if not depth:
        print("Depth of base layer must be supplied.")
        usage()
        sys.exit(2)        

    start = time.time()
    psMerge(baseDir,depth,topLevel,toastTile)
    end = time.time()
    print(end-start)

