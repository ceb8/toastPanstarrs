#!/usr/bin/env python

#from __future__ import print_function
#from __future__ import division

import sys

import numpy as np

from astropy.io import fits, ascii
from astropy import wcs
from astropy.coordinates import SkyCoord
from astropy import units as u

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
        #else:
        #    print(len(self.cache))
        fitsfile = fits.open(filename)
        self.cache[filename] = Data(img=fitsfile[1].data,cnt=self.count)
        fitsfile.close()
        self.count += 1

    def get(self,filename):
        if filename not in self.cache:
            self.add(filename)
            #print(len(self.cache),filename)
        return self.cache[filename].img 
    
psCache = fitsCache(50)

def panstarrsSampler():
    
    psCells = ascii.read("filter_r_rings.rpt")
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
        
        raArr[raArr < 0] += 2 * np.pi # making all ras 0 - 2pi
        
        # Getting info about skycell and pixel location for given ra/decs
        pixelInfoArray = pssc.findskycell(np.rad2deg(raArr), np.rad2deg(decArr))
            
        # Getting the file paths and creating a unique list of them
        fileLocByPix = psSC2FileLoc[pixelInfoArray['projcell'],pixelInfoArray['subcell']]
        filePths = np.unique(fileLocByPix)
        
        # Getting the pixel indices
        pixIndX = np.rint(pixelInfoArray['x']).astype(int)
        pixIndY = np.rint(pixelInfoArray['y']).astype(int)
            
        tile = np.zeros(raArr.shape) # this should be filled with whatever we want to signal "no data" 
                                     # I am currently using zero
            
        for dataFle in filePths:
            if dataFle == '':
                #print("File not available")
                continue
            
            #print("File location:",dataFle)
            
            # getting the image data (will be rplaced by cache class)
            #fitsFile = fits.open(dataFle)
            #imgData = fitsFile[1].data
            #fitsFile.close() 
            imgData = psCache.get(dataFle)
                
            # getting the pixels we want out of this file
            pix2Fill = (fileLocByPix == dataFle)
            #print("Number of pixels to be filled:",np.sum(pix2Fill))
            tile[pix2Fill] = imgData[pixIndY[pix2Fill],pixIndX[pix2Fill]]   
            
        return tile

    return vec2Pix


def toast_panstarrs(depth, outputDir, raRange, decRange):
    sampler = normalizer(panstarrsSampler(),-3,12)
    toast(sampler, depth, outputDir, ra_range=raRange,dec_range=decRange)
    return


if __name__ == "__main__":

    if len(sys.argv) != 5:
        print(sys.argv[0],"depth outputDirectory raRange decRange")
        exit()
   
    depth = int(sys.argv[1])
    outputDir = sys.argv[2]
    raRange = [float(x) for x in sys.argv[3].split(',')]
    decRange = [float(x) for x in sys.argv[4].split(',')]
    start = time.time()
    toast_panstarrs(depth, outputDir, raRange, decRange)
    end = time.time()
    print(end - start)


           
