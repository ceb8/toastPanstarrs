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


def minmax(arr):
    return [min(arr),max(arr)]


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
        
        tile = np.zeros(raArr.shape) # this should be filled with whatever we want to signal "no data" 
                                     # I am currently using zero
        tileFill = np.full(raArr.shape,False,bool)

        #print(raArr[0,0], decArr[0,0])
        raArr[raArr < 0] += 2 * np.pi # making all ras 0 - 2pi
        
        minRa,maxRa = minmax(np.array([raArr[0][0],raArr[0][-1],raArr[-1][0],raArr[-1][-1]]))
        minDec,maxDec = minmax(np.array([decArr[0][0],decArr[0][-1],decArr[-1][0],decArr[-1][-1]]))

        while(False in tileFill):
            inds = np.where(tileFill == False) # is there a better way to do this?
            
            # These 2 lines will need to be generalized away eventually
            pc,sc = pssc.findskycell(np.rad2deg(raArr[inds[0][0],inds[1][0]]), 
                                     np.rad2deg(decArr[inds[0][0],inds[1][0]]))
            dataFle = psSC2FileLoc[pc[0],sc[0]]
            #print(raArr[inds[0][0],inds[1][0]], decArr[inds[0][0],inds[1][0]])
            #print(np.rad2deg(raArr[inds[0][0],inds[1][0]]), 
            #      np.rad2deg(decArr[inds[0][0],inds[1][0]]))
            
            if not dataFle:
                tileFill[inds[0][0],inds[1][0]] = True
                # Do I want to/ can I deal with the full footprint here?
                continue
            
            print("Skycell:",pc,",",sc)
            print("File location:",dataFle)
            
            # getting what we need out of the fits file
            fitsFile = fits.open(dataFle)
            dfWcs = wcs.WCS(fitsFile[1].header)
            fp = dfWcs.calc_footprint(fitsFile[1].header)
            footprint = np.array([SkyCoord(*x,frame='icrs',unit='deg') for x in  fp])
            #print(fp)
            #print(footprint)
            imgData = fitsFile[1].data
            fitsFile.close()
            
            # getting the edges, not the following code assumes the footprint is a rectangle aligned
            # alont ra/dec lines, this might need to be altered for the general case 
            # (galex can be the experiment for this) (might need to use the mask in the fits file?)
            imMinRa,imMaxRa = minmax([x.ra.rad for x in footprint])
            imMinDec,imMaxDec = minmax([x.dec.rad for x in footprint])

            # There are problems if the ra interval crosses the circle boundary (e.g. 359 - 1)
            # This should not happen with dec
            # Check and account for that here
            if (footprint[0].ra - footprint[3].ra) > 0:  
                # this is what would need to be altered to take into account different footprint shapes
                imMask = (raArr <= imMaxRa)  & (raArr >= imMinRa) 
                imMask &= (decArr <= imMaxDec) & (decArr >= imMinDec)
            else: # Crosses circle boundary
                imMask = (raArr >= imMaxRa)  & (raArr <= 2*np.pi)
                imMask |= ((raArr >= 0)  & (raArr <= imMinRa))
                imMask &= (decArr <= imMaxDec) & (decArr >= imMinDec)
        
            ny, nx = imgData.shape[0:2]    
            tile[imMask] = imgData[(ny*(decArr - imMinDec)/(imMaxDec - imMinDec)).astype(int)[imMask],
                                   (nx*(1-(raArr - imMinRa)/(imMaxRa - imMinRa))).astype(int)[imMask]]
            print("Number of pixels to be filled:",np.sum(imMask))
            tileFill |= imMask # adding true everywhere we just filled
            print()
                                
        return tile
    
    return vec2Pix


def toast_panstarrs(depth, outputDir, raRange, decRange):
    sampler = normalizer(panstarrsSampler(),-3,10)
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
    toast_panstarrs(depth, outputDir, raRange, decRange)

            
