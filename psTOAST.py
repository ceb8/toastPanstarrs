#!/usr/bin/env python

import sys, getopt

import numpy as np

from astropy.io import fits, ascii


from toasty import toast
from toasty.norm import normalize
import ps1skycell_toast as pssc

from collections import namedtuple
import time

Data = namedtuple('Data','img cnt')

# can't figure out a better wat to deal with the problems getting array values gt or lt a scaler while ignoring the np.nans
import warnings
warnings.filterwarnings("ignore",category=RuntimeWarning,message="invalid value encountered in greater_equal")
warnings.filterwarnings("ignore",category=RuntimeWarning,message="invalid value encountered in less_equal")

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
        try:
            fitsfile = fits.open(filename)
            imgData = fitsfile[1].data
            fitsfile.close()
            
            # doing image processing here
            imean = np.nanmean(imgData)
            vmax = (np.percentile(imgData[imgData >= imean],99.5) + 4.3) / 2  # produces warning cause nan, deal with later
            vmin = (np.percentile(imgData[imgData <= imean],0.5) - 1.3) / 2 # produces warning cause nan, deal with later
            #print(vmin,vmax)
            imgData[np.isnan(imgData)] = vmax#np.max(imgData) 
            imgData = normalize(imgData,vmin,vmax,stretch='sinh')
            
            self.cache[filename] = Data(img=imgData,cnt=self.count)
            
        except: # Any problem with opening or reading results in a null image
            self.cache[filename] = Data(img=None,cnt=self.count)
        self.count += 1

    def get(self,filename):
        if filename not in self.cache:
            self.add(filename)
        return self.cache[filename].img 
    
psCache = fitsCache(10)

def panstarrsSampler(filelocFile):
    
    psCells = ascii.read(filelocFile)
    psSC2FileLoc = np.full((max(psCells['SCn']) + 1,max(psCells['SCm']) + 1),"",dtype='<U168')
    psSC2FileLoc[psCells['SCn'],psCells['SCm']] = psCells['fileNPath']
    
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
        
            
        tile = np.zeros(raArr.shape, dtype=np.uint8) # this should be filled with whatever we want to signal "no data" 
                                     # I am currently using zero

        if (len(filePths) == 1) and (not filePths[0]):
            return None
            
        for dataFle in filePths:
            if dataFle == '':
                continue
            
            # getting the image data 
            imgData = psCache.get(dataFle)

            # file did not have any associated image data, probably the file was not found on disc
            if imgData is None: 
                continue
                
            # getting the pixels we want out of this file
            pix2Fill = (fileLocByPix == dataFle)
            try:
                ylen,xlen = imgData.shape
                pix2Fill[pixelInfoArray['y'] > ylen] = False 
                pix2Fill[pixelInfoArray['y'] < 0] = False 
                pix2Fill[pixelInfoArray['x'] > xlen] = False
                pix2Fill[pixelInfoArray['x'] < 0] = False
                tile[pix2Fill] = imgData[pixelInfoArray['y'][pix2Fill],pixelInfoArray['x'][pix2Fill]]
            except IndexError:
                print("Index Error!")
                print(dataFle)
                
            tile[np.isnan(tile)] = 10 # making nan values appear as white
            
        return tile

    return vec2Pix


def toast_panstarrs(inputFile, depth, outputDir, skyRegion=None, tile=None, restart=False):
    #sampler = normalizer(panstarrsSampler(inputFile),-2.267,9.001,scaling='sinh',bias=.22, contrast=3.723)
    sampler = panstarrsSampler(inputFile)
    if skyRegion:
        toast(sampler, depth, outputDir, base_level_only=True, ra_range=skyRegion[0],dec_range=skyRegion[1],restart=restart)
    elif tile:
        toast(sampler, depth, outputDir, base_level_only=True, toast_tile=tile, restart=restart)
    else:
        toast(sampler, depth, outputDir, base_level_only=True, restart=restart)
    return


def usage():
    print("toastPanstarrs.py -i <inputfile> -d <depth> -o <outputdirectory> [-l <rarange> -b <decrange>] [-t <tile>] [-r]")


if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:d:o:l:b:t:r",["help","inputfile","depth=","outdir=","rarange=","decrange=","tile=","restart"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)


    inputFile = ''
    depth = None
    outputDir = ''
    raRange = None
    decRange = None
    toastTile = None
    restart = False
    
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
            if len(toastTile) != 3:
                print("Toast tile must be of the form: depth,tx,ty")
                sys.exit(2)
        if opt in ('-r','--restart'):
            restart = True


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
        toast_panstarrs(inputFile, depth, outputDir, skyRegion=(raRange,decRange),restart=restart)
    elif toastTile:
        toast_panstarrs(inputFile, depth, outputDir, tile=toastTile,restart=restart)
    else:
        toast_panstarrs(inputFile, depth, outputDir,restart=restart)
    end = time.time()
    print(end - start)


           
