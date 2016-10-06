#!/usr/bin/env python


##########################
## Colorizing algorithm ##
##     B = (2g+r)/3     ## 
##     G = (2r+i)/3     ##
##     R = (i+z)/2      ##
##########################


import sys, getopt,os

import numpy as np

from itertools import product
from subprocess import run
from skimage.io import imread,imsave

import time

import warnings
warnings.filterwarnings("ignore", ".* is a low contrast image")

def colorize(depth,dirBase,outDir,txrange,tyrange,restart):
    for tx,ty in product(range(*txrange),range(*tyrange)):
        pth = '/' + str(depth) + '/' + str(ty) + '/' + str(ty) + '_' + str(tx) + '.png'

        # checking if the color file already exists
        if os.path.isfile(outDir+pth):
            if restart: 
                continue
            else:
                os.remove(outDir+pth)

        
        # check we have all the files we need
        if not (os.path.isfile(dirBase+'g'+pth) and os.path.isfile(dirBase+'r'+pth) 
                and os.path.isfile(dirBase+'i'+pth) and os.path.isfile(dirBase+'z'+pth)):
                #and os.path.isfile(dirBase+'y'+pth)):
            continue
        
        
        g = imread(dirBase+'g'+pth)
        r = imread(dirBase+'r'+pth)
        i = imread(dirBase+'i'+pth)
        z = imread(dirBase+'z'+pth)
        #y = imread(dirBase+'y'+pth) (final colorizing does not use y)
         
        G = g.astype(np.float64)
        R = r.astype(np.float64)
        I = i.astype(np.float64)
        Z = z.astype(np.float64)
        #Y = y.astype(np.float64)
        
        # bad pixels will be sturated in only one band (hopefully)
        # hopefully mor efficient ellimination of bad pixels for 5 bands
        maxDif = 175
        PM = np.median(np.array([G,R,I,Z]), axis=0)
        g[((G - PM) > maxDif) & (g == 255)] = 0
        r[((R - PM) > maxDif) & (r == 255)] = 0
        i[((I - PM) > maxDif) & (i == 255)] = 0
        z[((Z - PM) > maxDif) & (z == 255)] = 0
        #y[((Y - PM) > maxDif) & (y == 255)] = 0
        
        rgb = np.dstack((np.mean(np.array([i,z]),axis=0).astype(np.uint8),
                         np.mean(np.array([r,r,i]),axis=0).astype(np.uint8),
                         np.mean(np.array([g,g,r]),axis=0).astype(np.uint8)))

        direc, _ = os.path.split(outDir+pth)
        if not os.path.exists(direc):
            os.makedirs(direc)

        try:
            imsave(outDir+pth, rgb)
        except:
            print("Problem saving %s" % (outDir+pth))
        


def usage():
    print("psColorize.py -b <base directory> -o <output directory> -d <depth> [-x <tile x range> -y <tile y range> -r]")

    
if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hb:o:d:x:y:r",["help","baseDir=","depth=","txrange=","tyrange=","restart"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

        
    dirBase = ''
    outDir = '.'
    depth = None
    txRange = None
    tyRange = None
    restart = False

    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        if opt in ('-b','--baseDir'):
            dirBase = arg
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
        if opt in ('-r','--restart'):
            restart = True

    if not (dirBase):
        print("Directory containing grizy greyscale directories must be supplied.")
        usage()
        sys.exit(2)

    if not depth:
        print("Depth to be colorized must be supplied.")
        usage()
        sys.exit(2)        

    if not outDir:
        outDir = dirBase + "color"
        
    maxTileDim = 2**depth
    if not txRange:
        txRange = maxTileDim
    if not tyRange:
        tyRange = maxTileDim

    if (depth > 8) and  (txRange == maxTileDim) and (tyRange == maxTileDim):
        print("You have requested colorization of all tiles at depth %d." % depth)
        print("This may take a while, please be patient, or start with a smaller section.")

    start = time.time()
    colorize(depth,dirBase,outDir,txRange,tyRange,restart)
    end = time.time()
    print(end-start)
