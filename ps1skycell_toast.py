"""ps1skycell_toast.py  Locate PanSTARRS skycell for a given RA/Dec

R. White, 2015 November 25
C. Brasseur, took out database queries 2016 July 1
             altered to take RA/DEC in radians 2016 July
"""

import sys, subprocess, os
import numexpr as ne
import numpy as np
try:
        import astropy.io.fits as pyfits
except ImportError:
        import pyfits

# pixel scale is 0.25 arcsec
pixscale = 0.25

# read table of rings info from table in first extension of FITS file
gridfits = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'ps1grid.fits')
rings = pyfits.open(gridfits)[1].data

# Turning degrees into radians as needed
dec_min = np.deg2rad(rings.field('dec_min'))
dec_max = np.deg2rad(rings.field('dec_max'))
dec_centers = np.deg2rad(rings.field('dec'))
dec_limit = dec_min.min()

def findskycell(ra, dec):

        """Given input arrays RA, DEC (radians), returns a dictionary with the skycell info

        RA and Dec can be scalars or arrays.
        This returns just the best sky cell for each ra/dec(the one where the position is closest to the center).
        This uses the ps1grid.fits file for info on the tessellation.
        The return dictionary is indexed by column name, with each column being an array of values:
        Column          Value
        ra                      Input position
        dec                     
        projcell        Projection cell (0 if outside coverage)
        subcell         Subcell (0..99)
        crval1          Sky position of reference pixel for projection cell
        crval2          
        crpix1          Reference pixel in this skycell
        crpix2          
        x                       Source pixel position in this skycell
        y                       
        """

        if np.isscalar(ra) and np.isscalar(dec):
                return _findskycell_array(np.array([ra]),np.array([dec]))
        if len(ra) == len(dec):
                return _findskycell_array(np.asarray(ra),np.asarray(dec))
        else:
                raise ValueError("ra and dec must both be scalars or be matching length arrays")


def _findskycell_array(ra, dec):

        """Internal function: ra and dec are known to be arrays"""
        
        # find dec zone where rings.dec_min <= dec < rings.dec_max
        idec = np.searchsorted(dec_max, dec)

        # special handling at pole where overlap is complicated
	# do extra checks for top 2 rings
	# always start with the ring just below the pole
        nearpole = np.where(idec >= len(rings)-2)
        idec[nearpole] = len(rings)-2
        
        getfield = rings[idec].field
        nband = getfield('nband')

        
        # get normalized RA in range 0..2pi
        # NOTE: RA is normalized in place,
        #       input RA angles are assumed to be in the range -2pi:4pi
        nra = ra
        nra[nra < 0] += 2*np.pi
        nra[nra > 2*np.pi] -= 2*np.pi
        
        ira = (nra*nband/(2*np.pi) + 0.5).astype(int) % nband

        projcell = getfield('projcell') + ira
        dec_cen = dec_centers[idec] 
        ra_cen = ira*2*np.pi/nband      

        # locate subcell within the projection cell

        # use tangent project to get pixel offsets
        x, y = sky2xy_tan(nra, dec, ra_cen, dec_cen)
         
        pad = 480

        if len(nearpole[0]) > 0:
                # handle the points near the pole (if any)
                # we know that this "ring" has only a single field
                getfield2 = rings[-1].field
                projcell2 = getfield2('projcell')
                dec_cen2 = np.deg2rad(getfield2('dec'))
                ra_cen2 = 0.0
                x2, y2 = sky2xy_tan(nra[nearpole], dec[nearpole], ra_cen2, dec_cen2)
                # compare x,y and x2,y2 to image sizes to select best image
                # returns a Boolean array with true for values where 2nd image is better
                use2 = poleselect(x[nearpole], y[nearpole], x2, y2, rings[-2], rings[-1], pad)
                if use2.any():
                        # slightly obscure syntax here makes this work even if ra, dec are multi-dimensional
                        wuse2 = np.where(use2)[0]
                        w2 = list(map(lambda x: x[wuse2], nearpole))
                        idec[w2] = len(rings)-1
                        getfield = rings[idec].field
                        nband[w2] = 1
                        ira[w2] = 0
                        projcell[w2] = projcell2
                        dec_cen[w2] = dec_cen2
                        ra_cen[w2] = ra_cen2
                        x[w2] = x2[wuse2]
                        y[w2] = y2[wuse2]

        # compute the subcell from the pixel location
        px = getfield('xcell')-pad
        py = getfield('ycell')-pad
        k = (4.5+x/px + 0.5).astype(int).clip(0,9)
        j = (4.5+y/py + 0.5).astype(int).clip(0,9)
        subcell = 10*j + k

        # get pixel coordinates within the skycell image
        crpix1 = getfield('crpix1') + px*(5-k)
        crpix2 = getfield('crpix2') + py*(5-j)
        ximage = (x + crpix1 + 0.5).astype(int)
        yimage = (y + crpix2 + 0.5).astype(int)
  
        # insert zeros where we are below lowest dec_min
        w = np.where(dec < dec_limit)
        projcell[w] = 0
        subcell[w] = 0
        crpix1[w] = 0
        crpix2[w] = 0
        ximage[w] = 0
        yimage[w] = 0

        # return a dictionary
        return {'ra': ra, 'dec': dec, 'projcell': projcell, 'subcell': subcell,
                'crval1': ra_cen, 'crval2': dec_cen, 'crpix1': crpix1, 'crpix2': crpix2,
                'x': ximage, 'y': yimage}



def poleselect(x1, y1, x2, y2, rings1, rings2, pad):

        """Compares x,y values from 2 images to determine which is best

        Returns boolean array with True where x2,y2 is best
        """

        nx1 = 10*(rings1['xcell']-pad)+pad
        ny1 = 10*(rings1['ycell']-pad)+pad
        nx2 = 10*(rings2['xcell']-pad)+pad
        ny2 = 10*(rings2['ycell']-pad)+pad
        # compute minimum distances to image edges
        # note negative values are off edge
        d1 = np.minimum(np.minimum(x1+nx1/2,nx1/2-1-x1),
                        np.minimum(y1+ny1/2,ny1/2-1-y1))
        d2 = np.minimum(np.minimum(x2+nx2/2,nx2/2-1-x2),
                        np.minimum(y2+ny2/2,ny2/2-1-y2))
        return (d1 < d2)


def getskycell_center(projcell, subcell):

        """Return position of the center (RA, DEC) of a skycell or list of skycells

        projcell and subcell can be scalars or arrays.
        This uses the ps1grid.fits file for info on the tessellation.
        The return dictionary is indexed by column name, with each column being an array of values:
        Column          Value
        projcell        Input parameters
        subcell         
        ra                      Central position (degrees)
        dec                     
        crval1          Sky position of reference pixel for projection cell
        crval2          
        crpix1          Reference pixel in this skycell
        crpix2          
        x                       Center pixel position in this skycell
        y                       
        """

        if np.isscalar(projcell) and np.isscalar(subcell):
                return _getskycell_center_array(np.array([projcell]),np.array([subcell]))
        if len(projcell) == len(subcell):
                return _getskycell_center_array(np.asarray(projcell),np.asarray(subcell))
        else:
                raise ValueError("projcell and subcell must both be scalars or be matching length arrays")


def _getskycell_center_array(projcell, subcell):

        """Internal function: projcell and subcell are known to be arrays
        
        This just clips to the nearest cell in the grid for values outside the bounds
        """

        # find dec zone where rings.projcell <= projcell
        idec = (np.searchsorted(rings.field('projcell'), projcell+1)-1).clip(0)
        getfield = rings[idec].field
        nband = getfield('nband')
        ira = (projcell - getfield('projcell')).clip(0,nband)
        dec_cen = getfield('dec')
        ra_cen = ira*360.0/nband

        # locate subcell within the projection cell
        k = subcell % 10
        j = (subcell//10) % 10

        pad = 480
        px = getfield('xcell')-pad
        py = getfield('ycell')-pad
        ximage = 0.5*(px+pad-1)
        yimage = 0.5*(py+pad-1)

        # get pixel coordinates within the skycell image
        crpix1 = getfield('crpix1') + px*(5-k)
        crpix2 = getfield('crpix2') + py*(5-j)
        # position in projection cell
        x = ximage - crpix1
        y = yimage - crpix2

        ra, dec = xy2sky_tan(x, y, ra_cen, dec_cen)

        # return a dictionary
        return {'ra': ra, 'dec': dec, 'projcell': projcell, 'subcell': subcell,
                'crval1': ra_cen, 'crval2': dec_cen, 'crpix1': crpix1, 'crpix2': crpix2,
                'x': ximage, 'y': yimage}


def sky2xy_tan(ra, dec, ra_cen, dec_cen, crpix=(0.0,0.0)):

        """Convert RA,Dec sky position (radians) to X,Y pixel position

        ra[n], dec[n] are input arrays in radians
        ra_cen[n], dec_cen[n] are image centers in radians
        crpix is the reference pixel position (x,y)
        Returns tuple (x,y) where x and y are arrays with pixel position for each RA,Dec
        """

        cd00 = -pixscale*np.pi/(180*3600)
        cd01 = 0.0
        cd10 = 0.0
        cd11 = -cd00
        determ = cd00*cd11-cd01*cd10
        cdinv00 =  cd11/determ
        cdinv01 = -cd01/determ
        cdinv10 = -cd10/determ
        cdinv11 =  cd00/determ

        cos_crval1 = ne.evaluate('cos(dec_cen)')
        sin_crval1 = ne.evaluate('sin(dec_cen)')
        
        radif = (ra - ra_cen)
        radif[radif > np.pi] -= 2*np.pi
        radif[radif < -np.pi] += 2*np.pi

        cos_dec = ne.evaluate('cos(dec)')
        sin_dec = ne.evaluate('sin(dec)')
        cos_radif = ne.evaluate('cos(radif)')
        sin_radif = ne.evaluate('sin(radif)')
        
        h = sin_dec*sin_crval1 + cos_dec*cos_crval1*cos_radif
        xsi = cos_dec*sin_radif/h
        eta = (sin_dec*cos_crval1 - cos_dec*sin_crval1*cos_radif)/h
        xdif = cdinv00*xsi + cdinv01*eta
        ydif = cdinv10*xsi + cdinv11*eta
        return (xdif+crpix[0], ydif+crpix[1])


def xy2sky_tan(x, y, ra_cen, dec_cen, crpix=(0.0,0.0)):

        """Convert X,Y pixel position to RA,Dec sky position (degrees)

        x[n], y[n] are input arrays in pixels
        ra_cen[n], dec_cen[n] are image centers in degrees
        crpix is the reference pixel position (x,y)
        Returns tuple (ra,dec) where ra and dec are arrays with pixel position for each x,y
        """

        dtor = np.pi/180
        cd00 = -pixscale*dtor/3600
        cd01 = 0.0
        cd10 = 0.0
        cd11 = -cd00

        cos_crval1 = np.cos(dtor*dec_cen)
        sin_crval1 = np.sin(dtor*dec_cen)

        xdif = x - crpix[0]
        ydif = y - crpix[1]
        xsi = cd00*xdif + cd01*ydif
        eta = cd10*xdif + cd11*ydif
        beta = cos_crval1 - eta*sin_crval1
        ra = np.arctan2(xsi, beta) + dtor*ra_cen
        gamma = np.sqrt(xsi**2 + beta**2)
        dec = np.arctan2(eta*cos_crval1+sin_crval1, gamma)
        return (ra/dtor, dec/dtor)

