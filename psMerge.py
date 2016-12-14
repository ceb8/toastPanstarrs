#!/usr/bin/env python

import sys, getopt

import numpy as np

import time

from toasty import toast

from PIL import Image

def mergeBicubic(mosaic):
    """Bicubic merge function for toasty merging."""
    subtile = Image.fromarray(mosaic)
    subtile = subtile.resize((256,256),Image.BICUBIC)
    return np.asarray(subtile)

def mergeNearsetNeighbor(mosaic):
    """Nearest neighbor merge function for toasty merging."""
    subtile = Image.fromarray(mosaic)
    subtile = subtile.resize((256,256))
    return np.asarray(subtile)


def psMerge(baseDir,depth, topLevel, toastTile, bicubicMerge):
    """Create a full hierarchical TOAST tileset up to topLevel from a baseLayer of TOAST tiles.

    Parameters
    ---------- 
    baseDir: string
      The upper level directory that contains the TOASTed tiles by layer.
    depth: int
      The depth of the bottommost layer you want to merge from (these tiles should already exist).
    topLevel: int
      The topmost layer you want to merge to.
    toastTile: array 
      Only tiles that overlap with this TOAST tile will be merged. Form [depth,tx,ty].
    bicubicMerge: boolean 
      If True, bicubic merge will be used, otherwise nearest neighbor will be used.

    """

    if bicubicMerge == True:
        imgMerge = mergeBicubic
    else:
        imgMerge = mergeNearsetNeighbor
    toast(baseDir,depth,baseDir,top_layer=topLevel,merge=imgMerge,toast_tile=toastTile) 

    
def usage():
    print("psMerge.py -b <base directory> -d <depth> [-l <top level> -t <tile> -c]")
    print(
    """Create a full hierarchical TOAST tileset up to topLevel from a baseLayer of TOAST tiles.

    Parameters
    ---------- 
    baseDir (-b): string
      The upper level directory that contains the TOASTed tiles by layer.
    depth (-d): int
      The depth of the bottommost layer you want to merge from (these tiles should already exist).
    topLevel (-l): int (optional)
      The topmost layer you want to merge to.
    toastTile (-t): array (optional)
      Only tiles that overlap with this TOAST tile will be merged. Form depth,tx,ty.
    bicubicMerge (c): boolean (optional)
      If True, bicubic merge will be used, otherwise nearest neighbor will be used.
    """)
    

    
if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hb:d:l:t:c",["help","basedir=","depth=","toplevel=","tile=","bicubic"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

        
    baseDir = ''
    depth = None
    topLevel = 4 # default is 4, since that works for AstroView
    toastTile = None
    bicubic=False

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
        if opt in ('-c','--bicubic'):
            bicubic = True
            

    if not baseDir:
        print("Base directory containing base level of tile must be supplied for merge to run.")
        usage()
        sys.exit(2)

    if not depth:
        print("Depth of base layer must be supplied.")
        usage()
        sys.exit(2)        

    start = time.time()
    psMerge(baseDir,depth,topLevel,toastTile,bicubic)
    end = time.time()
    print(end-start)

