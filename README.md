# toastPanstarrs
Making TOAST tiles from panstarrs data

Tessellated Octahedral Adaptive Subdivision Transform ([TOAST](http://www.worldwidetelescope.org/Developers/ProjectionReference#TOASTProjection)), created by Microsoft, is a way to represent a sphere as a ["hierarchical triangular mesh."](https://arxiv.org/ftp/cs/papers/0701/0701164.pdf) The TOAST method starts by modeling the sphere as an octahedron, then recursively subdivides each triangular face until the sphere is approximated to arbitrary accuracy.  The triangles are all the same size in terms of image-pixels, however the sizes of represented sections of sphere vary. This representation of the sphere is used in the [World Wide Telescope](http://www.worldwidetelescope.org/) visualization environment, as well as the [Astroview](https://mast.stsci.edu/portal/Mashup/Clients/AstroView/AstroView.html) all-sky visualization (our use case).

The goal of this project is to use the [PANSTARRS all-sky survey](http://pan-starrs.ifa.hawaii.edu) to create a set of TOAST tiles at depths 4-12 for use in Astroview. To that end Chris Beaumont's [toasty library](https://github.com/ChrisBeaumont/toasty) was modified to allow for toasting sections of the sky independently, and to separate the creation of the bottom layer (highest resolution) TOAST tiles, from  the resampling of that layer to produce each successive (lower resolution) layer of TOAST tiles.

### Requirements 
 * Python (TOASTING and colorizing have only been tested with Python 3.5)
 * Our [Toasty](https://github.com/ceb8/toasty)
 * Access to panstarrs servers
 * Numpy
 * Astropy
 * Pillow/PIL
 * Numexpr
 * scikit-image
 * OpenCV

### Assumptions
 * To create the TOASTed PANSTARRS visualization we used a 32 core VM with 140 GB of RAM and 12TB of disk space.
 * The panstarrs server mount points were /data/ps1/node[01-20], this is assumed in the code.

### TOASTing PANSTARRS (*psTOAST.py*)

In a python interpreter:
```python
from psTOAST import toast_panstarrs

toast_panstarrs(inputFile, depth, outputDir, skyRegion, tile, restart)
```

where
 * **inputFile** (string) is a file containing skycell, projection cell, and file location (one of the filter_*_rings.rpt files)
 * **depth** (int) is the bottom-most layer to be created (i.e. the number of recursive subdivisions, where 0 is the original octahedron)
 * **outputDir** (string) is the directory in which the TOAST tiles will be saved
 * **skyRegion** (optional tuple) is the region of the sky to be toasted in the form `([raMin,raMax],[decMin,decMax])` (degrees). This option cannot be used with the tile option.
 * **tile** (optional array) is the TOAST tile to be toasted in the form `[depth,x,y]`. This option cannot be used with the skyRegion option.
 * **restart** (optional boolean) `True` signals a restart job, where any tiles already existing in the outPut directory should not be recalculated.


From the command line:
```
toastPanstarrs.py -i <inputfile> -d <depth> -o <outputdirectory> [-l <rarange> -b <decrange>] [-t <tile>] [-r]
```

where
 * **inputfile**, **depth**, **outputdirectory**, and **tile** are as described above.
 * **rarange** and **decrange** are of the form `raMin,raMax` and `decMin,decMax`, and together define a skyRegion as above.
 * **-r** is equivalent to setting restart to `True`.

Toasting the entire sky (64 processes, approximate memory requirement of 136GB, approximate space requirement of 900GB) using the helper shell script:
```
runPSTOAST.sh inputfile outputDir
```

where **inputfile** and **outputDir** as as defined above.
A depth 12 bottom layer only TOAST tile-set is created.

Rick White's findskycell code is used to relate ra/dec to panstarrs image pixel.
Hyperbolic sine image normalization is applied with the following limits:
```
    min = ((99.5th percentile) + 4.3)/2
    max = ((0.5th percentile) - 1.3)/2
    bias = 0.5
    contrast = 1
```

### Colorizing PANSTARRS (*psColorize.py*)

Four bands, g,r,i, and z, are required for PANSTARRS colorization.

In a python interpreter:
```python
from psColorize import colorize

colorize(depth,dirBase,outDir,txrange,tyrange,restart)
```
where
 * **depth** (int) is the TOAST layer that is being colorized
 * **dirBase** (string) is the path plus directory prefix containing the four band-pass TOASTs (all that should be needed to complete the band pass directories are the letters g,r,i, or z)
 * **outDir** (string) is the directory where the colorized TOAST will go
 * **txrange** and **tyrange** (array) are the tile x and y ranges to be colorized in the form `[min,max]`
 * **restart**  (optional boolean) indicates a restart job, if `True` already existing images in the colorized directory will not be recreated

On the command-line:

```
psColorize.py -b <base directory> -o <output directory> -d <depth> [-x <tile x range> -y <tile y range> -r]
```

where all the arguments are as above, but **base directory** and **depth** are the only required ones.  If **output directory** is not supplied, the output directory is the base directory + "color."  If tx and ty ranges are not supplied, the entire range at that depth is used.

Colorizing the entire sky (64 processes) using the helper shell script:
```
runPSColor.sh dirBase
```

where **dirBase** is as defined above.
A depth 12 bottom layer only colorized TOAST tile-set is created.

The colorizing algorithm used is:
```
    B = (2g+r)/3
    G = (2r+i)/3
    R = (i+z)/2
```

### Merging PANSTARRS into a full TOAST tile set and smoothing images (*psMergeBC.py*, *psMergeNN.py* and *psSmoothing.py*)

This functionality was designed for merging and smoothing colorized TOAST tiles.

Various algorithms for mergine and smoothing were tested and the following was determined to be the best:
* Layers 11-10  
  Bicubic resampling from the previous layer,  
  Application of a threshold of 40 (on values 0-255).  
* Layers 9-7  
  Bicubic resampling from the previous layer,  
  Smooth image (PIL SMOOTH image filter),  
  Increase brighness and contrast by 10%,  
  Application of a threshold of 40 (on values 0-255).  
* Layer 6  
  Nearest neighbor resampling from the previous layer,  
  Smooth image (PIL SMOOTH image filter),  
  Increase brighness and contrast by 10%,  
  Application of a threshold of 40 (on values 0-255).  
* Layers 5-4  
  Nearest neighbor resampling from the previous layer,  
  Increase brighness and contrast by 10%,  
  Application of a threshold of 40 (on values 0-255).   


In a python interpreter:

Merging,
```python
from psMerge import psMerge 

psMerge(baseDir,depth, topLevel, toastTile,bicubicMerge)
```

where
 * **baseDir** (string) is the directory that contains the TOASTed tiles (not the numbered TOAST directory the one above that)
 * **depth** (int) is the depth of the bottommost layer you want to merge from
 * **topLevel** (int) is the topmost layer you want to merge to
 * **toastTile** (array) is the tile to merge in the form [depth,tx,ty]
 * **bicubicMerge** (boolean) `True` indicated that bicubic merge will be used, otherwise nearest neighbor will be used

and smoothing
```python
from psSmoothing import despeckle

despeckle(depth,inDir,outDir,txrange,tyrange,threshold,smooth,enhance,restart)
```
where
 * **depth** (int) is the TOAST layer that is have noise removed
 * **inDir** (string) is the directory containing the original (noisy) tiles
 * **outDir** (string) is the directory where the de-speckled TOAST tiles will go (can be the same as inDir)
 * **txrange** and **tyrange** (array) are the tile x and y ranges to be de-speckled in the form `[min,max]`
 * **threshold**  (optional boolean) `True` indicates that a threshold of 40 will be applied to each image (default is True)
 * **smooth**  (optional boolean) `True` indicatez that PIL's ImageFilter.SMOOTH will be applied to each image (default is True)
 * **enhance**  (optional boolean) `True` indicates that the brightness and contrast of each image will be increased by 10% (default is True)
 * **restart**  (optional boolean) `True` indicates a restart job, where already existing images in outDir will not be recreated


On the commendline:

```
psMerge.py -b <base directory> -d <depth> [-l <top level> -t <tile> -c]

psSmoothing.py -i <input directory> -o <output directory> -d <depth> [-x <tile x range> -y <tile y range> -s -e -t -r]
```

where the arguments are as above, except **top level** and **tile** are optional in the psMerge commands, and tile ranges (and flags) are optional in the smoothing command.

Because each level must be smoothed before the next level is created from it, each layer must be individually merged, then smoothed, before the next layer can be begun.  This is less efficient than running the toast merge all at once, and then smoothing th images after, however it makes for a better final product.  

The shell script `runPSMergeAndSmooth.sh TOASTdir` contains all of the commands necessary to merge and smooth the TOAST tile set, however each section (separated by a wait command) depends on completion of the previous sections, so it may be preferable to split out the sections individually.

