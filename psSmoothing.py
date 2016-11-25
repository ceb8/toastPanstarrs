#!/usr/bin/env python


import sys, getopt,os

import numpy as np

import time
import cv2

from itertools import product

from PIL import Image, ImageEnhance, ImageFilter

thresh = 40


def despeckle(depth,inDir,outDir,txrange,tyrange,
              threshold=True,smooth=True,enhance=True,restart=False):

    for tx,ty in product(range(*txrange),range(*tyrange)):
        pth = '/' + str(depth) + '/' + str(ty) + '/' + str(ty) + '_' + str(tx) + '.png'

        # checking if the despeckled file already exists
        if os.path.isfile(outDir+pth) and restart:
            continue

        # making sure the file to de-speckle exists
        if not os.path.isfile(inDir+pth): 
            continue

        try:
            origImg = Image.open(inDir + pth)
        except:
            print("Problem with " + inDir + pth)
            continue
            
        if smooth == True:
            cleanImg = origImg.filter(ImageFilter.SMOOTH)
        else:
            cleanImg = origImg 


        if enhance == True:
            brightness = ImageEnhance.Brightness(cleanImg)
            cleanImg = brightness.enhance(1.1)
        
            contrast = ImageEnhance.Contrast(cleanImg)
	    cleanImg = contrast.enhance(1.1)

        if threshold == True:
            try:
                retval, cleanImg = cv2.threshold(np.array(cleanImg), thresh, 255, cv2.THRESH_TOZERO)
                cleanImg = Image.fromarray(cleanImg)
            except:
                print("Problem thresholding " + inDir + pth)

        direc, _ = os.path.split(outDir+pth)
        if not os.path.exists(direc):
            os.makedirs(direc)

        try:
            cleanImg.save(outDir+pth)
        except:
            print("Problem Saving " +outDir+pth)



def usage():
    print("psSmoothing.py -i <input directory> -o <output directory> -d <depth> [-x <tile x range> -y <tile y range> -t -s -e -r]")

    
if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:o:d:x:y:tser",["help","inDir=","outDir","depth=","txrange=","tyrange=","threshold","smooth","enhance","restart"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

        
    inDir = ''
    outDir = ''
    depth = None
    txRange = None
    tyRange = None
    threshold = False
    smooth = False
    enhance = False
    restart = False

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
        if opt in ('-t','--threshold'):
            threshold = True
        if opt in ('-s','--smooth'):
            smooth = True
        if opt in ('-e','--enhance'):
            enhance = True
        if opt in ('-r','--restart'):
            restart = True

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
    despeckle(depth,inDir,outDir,txRange,tyRange,threshold,smooth,enhance,restart)
    end = time.time()
    print(end-start)

