#!/usr/bin/env python

import sys, getopt

import numpy as np

from astropy.io import fits, ascii
#from astropy.coordinates import SkyCoord
#from astropy import units as u

from toasty import toast, normalizer
import ps1skycell_toast as pssc

from collections import namedtuple
import time

Data = namedtuple('Data','img cnt')

class fitsCache:
    """"Caching for fitfile image data"""
    def __init__(self,maxItems):
        self.cache = {}
        self.count = 0
        self.maxItms = maxItems
        
    def remove(self,filename):
        if filename not in self.cache:
            return
        del(self.cache[filename])
    
    def oldest(self):
        return sorted([(y.cnt,x) for x,y in self.cache.items()])[0][1]
    
    def add(self,filename):
        if len(self.cache) == self.maxItms:
            self.remove(self.oldest())
        fitsfile = fits.open(filename)
        self.cache[filename] = Data(img=fitsfile[1].data,cnt=self.count)
        fitsfile.close()
        self.count += 1

    def get(self,filename):
        if filename not in self.cache:
            self.add(filename)
        return self.cache[filename].img 
    
psCache = fitsCache(10)

def panstarrsSampler(filelocFile):
    
    psCells = ascii.read(filelocFile)
    psSC2FileLoc = np.full((max(psCells['SCn']) + 1,max(psCells['SCm']) + 1),"",dtype='<U168')
    #psSC2FileLoc[psCells['SCn'],psCells['SCm']] = psCells['fileNPath']
    psSC2FileLoc[2404][5]  = "RINGS.V3.skycell.2404.005.stk.4032678.unconv.fits"
    psSC2FileLoc[2381][62] = "RINGS.V3.skycell.2381.062.stk.3906396.unconv.fits"
    psSC2FileLoc[2381][63] = "RINGS.V3.skycell.2381.063.stk.3906397.unconv.fits"
    psSC2FileLoc[2381][64] = "RINGS.V3.skycell.2381.064.stk.3906398.unconv.fits"
    psSC2FileLoc[2381][52] = "RINGS.V3.skycell.2381.052.stk.3906388.unconv.fits"
    psSC2FileLoc[2381][53] = "rings.v3.skycell.2381.053.stk.r.unconv.fits" # M101
    psSC2FileLoc[2381][54] = "RINGS.V3.skycell.2381.054.stk.3906390.unconv.fits"
    psSC2FileLoc[2381][42] = "RINGS.V3.skycell.2381.042.stk.3906380.unconv.fits"
    psSC2FileLoc[2381][43] = "RINGS.V3.skycell.2381.043.stk.3906381.unconv.fits"
    psSC2FileLoc[2381][44] = "RINGS.V3.skycell.2381.044.stk.3906382.unconv.fits"
    
    def vec2Pix(raArr,decArr):

        global psCache
        
        # Getting info about skycell and pixel location for given ra/decs
        pixelInfoArray = pssc.findskycell(raArr, decArr)
            
        # Getting the file paths and creating a unique list of them
        fileLocByPix = psSC2FileLoc[pixelInfoArray['projcell'],pixelInfoArray['subcell']]
        filePths = {}
        for line in fileLocByPix:
            for filename in line:
                filePths[filename] = filename
        filePths = list(filePths.keys())
        
            
        tile = np.zeros(raArr.shape) # this should be filled with whatever we want to signal "no data" 
                                     # I am currently using zero
            
        for dataFle in filePths:
            if dataFle == '':
                continue
            
            # getting the image data 
            imgData = psCache.get(dataFle)
                
            # getting the pixels we want out of this file
            pix2Fill = (fileLocByPix == dataFle)
            tile[pix2Fill] = imgData[pixelInfoArray['y'][pix2Fill],pixelInfoArray['x'][pix2Fill]]   
            
        return tile

    return vec2Pix


def toast_panstarrs(inputFile, depth, outputDir, skyRegion=None, tile=None):
    sampler = normalizer(panstarrsSampler(inputFile),-2.267,9.001,scaling='sinh',bias=.193, contrast=3.723)
    if skyRegion:
        toast(sampler, depth, outputDir, ra_range=skyRegion[0],dec_range=skyRegion[1])
    elif tile:
        toast(sampler, depth, outputDir, toast_tile=tile)
    else:
        toast(sampler, depth, outputDir)
    return


def usage():
    print("toastPanstarrs.py -i <inputfile> -d <depth> -o <outputdirectory> [-l <rarange> -b <decrange>] [-t <tile>]")


if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:d:o:l:b:t:",["help","inputfile","depth=","outdir=","rarange=","decrange=","tile="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)


    inputFile = ''
    depth = None
    outputDir = ''
    raRange = None
    decRange = None
    toastTile = None
    
    for opt, arg in opts:
        if opt in ('-h','--help'):
            usage()
            sys.exit()
        if opt in ('-i','--inputfile'):
            inputFile = arg
        if opt in ('-d','--depth'):
            try:
                depth = int(arg)
            except ValueError:
                print("Depth must be an integer (base 10 please)")
                sys.exit()
        if opt in ('-o','--outdir'):
            outputDir = arg
        if opt in ('-l','--rarange'):
            try:
                raRange = [float(x) for x in arg.split(',')]
            except ValueError:
                print("RA range must be of the form: 210.5,215.8")
                sys.exit(2)
            if len(raRange) != 2:
                print("RA range must be of the form: 210.5,215.8")
                sys.exit(2)
        if opt in ('-b','--decrange'):
            try:
                decRange = [float(x) for x in arg.split(',')]
            except ValueError:
                print("Dec range must be of the form: 54.1,54.3")
                sys.exit(2)
            if len(decRange) != 2:
                print("Dec range must be of the form: 54.1,54.3")
                sys.exit(2)
        if opt in ('-t','--tile'):
            try:
                toastTile = [int(x) for x in arg.split(',')]
            except ValueError:
                print("Toast tile must be of the form: depth,tx,ty")
                sys.exit(2)
            if len(decRange) != 3:
                print("Toast tile must be of the form: depth,tx,ty")
                sys.exit(2)


    if not (depth and outputDir and inputFile):
        print("Inputfile, depth, and outdir are required arguments.")
        usage()
        sys.exit(2)
                
    # user has specifis both ra/dec and tile options
    if (raRange or decRange) and toastTile:
        print("You may specify either (raRage AND decRange) OR toastTile, but not both.")
        sys.exit(2)

    # the user has specified exactly one of raRange or decRange
    if (bool(raRange) ^ bool(decRange)):
        print("You must specify both raRage AND decRange to use those options.")
        sys.exit(2)

    # the user specifies no options for breaking up the sky
    if not (bool(raRange) + bool(decRange) + bool(toastTile)):
        print("WARNING: You have not specified a section of the sky.")
        print("         The entire sky will be toasted.")
        print("         This is likely to take a very long time.")
                
    start = time.time()
    if (raRange and decRange):
        toast_panstarrs(inputFile, depth, outputDir, skyRegion=(raRange,decRange))
    elif toastTile:
        toast_panstarrs(inputFile, depth, outputDir, tile=toastTile)
    else:
        toast_panstarrs(inputFile, depth, outputDir)
    end = time.time()
    print(end - start)


           
