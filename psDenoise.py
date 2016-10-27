#!/usr/bin/env python


import sys, getopt,os

import numpy as np
import cv2

import time

from itertools import product


# parameters for despeckling
h=10
hColor=10
templateWindowSize = 7
searchWindowSize = 21


def despeckle(depth,inDir,outDir,txrange,tyrange,restart=False,inplace=False):

    for tx,ty in product(range(*txrange),range(*tyrange)):
        pth = '/' + str(depth) + '/' + str(ty) + '/' + str(ty) + '_' + str(tx) + '.png'

        # checking if the despeckled file already exists
        if not inplace:
            if os.path.isfile(outDir+pth):
                if restart: 
                    continue
                else:
                    os.remove(outDir+pth)

        # making sure the file to de-speckle exists
        if not os.path.isfile(inDir+pth): 
            continue

        origImg = cv2.imread(inDir + pth)
        
        try:
            cleanImg = cv2.fastNlMeansDenoisingColored(origImg,None,h,hColor,templateWindowSize,searchWindowSize)
        except:
            print("Problem smoothing " + pth)
            continue

        direc, _ = os.path.split(outDir+pth)
        if not os.path.exists(direc):
            os.makedirs(direc)

        if not(cv2.imwrite(outDir+pth,cleanImg)):
            print("Problem saving %s" % (outDir+pth))




def usage():
    print("psDenoise.py -i <input directory> -o <output directory> -d <depth> [-x <tile x range> -y <tile y range> -r -p]")

    
if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:o:d:x:y:rp",["help","inDir=","outDir","depth=","txrange=","tyrange=","restart","inplace"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

        
    inDir = ''
    outDir = ''
    depth = None
    txRange = None
    tyRange = None
    restart = False
    inPlace = False

    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        if opt in ('-i','--inDir'):
            inDir = arg
        if opt in ('-o','--outDir'):
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
        if opt in ('-p','--inplace'):
            inPlace = True
        

    if not (inDir):
        print("Directory containing images to be de-speckled must be supplied.")
        usage()
        sys.exit(2)

    if not (outDir):
        print("Directory for de-speckled images must be supplied.")
        usage()
        sys.exit(2)

    if not depth:
        print("Depth to be colorized must be supplied.")
        usage()
        sys.exit(2)        

        
    maxTileDim = 2**depth
    if not txRange:
        txRange = maxTileDim
    if not tyRange:
        tyRange = maxTileDim

    if (depth > 8) and  (txRange == maxTileDim) and (tyRange == maxTileDim):
        print("You have requested de-speckling of all tiles at depth %d." % depth)
        print("This may take a while, please be patient, or start with a smaller section.")

    start = time.time()
    despeckle(depth,inDir,outDir,txRange,tyRange,restart,inPlace)
    end = time.time()
    print(end-start)

