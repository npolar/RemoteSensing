# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 09:04:29 2013

@author: max

Classification into Glacier Surface Types

"""

#import modules

import ogr, os, gdal, numpy


# Define Functions

def RasterizeMask(infile):
    '''
    Takes infile and creates raster with extension of shapefil
    '''
    
    # Define filenames
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    outraster = infilepath + '/' + infileshortname + '.tif'    
        
    # Rasterize mask and at same time create file -- call gdal_rasterize commandline
    print '\n Rasterize ', infilename
    os.system('gdal_rasterize -burn 2 -l ' + infileshortname +' -tr 20.0 -20.0 ' +  infile + ' ' + outraster)
    



def CropGlacier(inshapefile, inSARfile):
    '''
    Crops SAR image to extent of Mask and Remove all Values outside Mask
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    outraster = inSARfilepath + '/' + inSARfileshortname + '_crop.tif'
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    #Register driver and open file
    shapedriver = ogr.GetDriverByName('ESRI Shapefile')   
    maskshape = shapedriver.Open(inshapefile, 0)
    if maskshape is None:
        print 'Could not open ', inshapefilename
        return
        
    #Get Extension of Layer
    masklayer = maskshape.GetLayer()
    maskextent = masklayer.GetExtent()
    print 'Extent of ', inshapefilename, ': '
    print maskextent
    print 'UL: ', maskextent[0], maskextent[3]
    print 'LR: ', maskextent[1], maskextent[2]

    # crop image with gdal_translate -- call gdal_rasterize commandline
    print '\n Subsetting ', inSARfilename, ' to glacier extent'
    os.system('gdal_translate -projwin ' + str(maskextent[0]) + ' ' + str(maskextent[3]) + ' ' + str(maskextent[1]) + ' ' + str(maskextent[2]) + ' ' + inSARfile + ' ' + outraster)
    
    #Close files 
    maskshape = None
    
def MaskGlacier(inshapefile, inSARfile):
    '''
    Masks Cropped SARfile
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '/' + inSARfileshortname + '_crop.tif'
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    inshapeasraster = inshapefilepath + '/' + inshapefileshortname + '.tif'
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(inSARcrop, gdal.GA_Update)
    mask = gdal.Open(inshapeasraster, gdal.GA_ReadOnly)
    dsband = ds.GetRasterBand(1)
  
    #Read input raster into array
    glacierraster = ds.ReadAsArray()
    maskraster = mask.ReadAsArray()
        
    #get image size
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    
    #Process the image
    print 'Masking ', inSARcrop
    for i in range(rows):
        for j in range(cols):
            if maskraster[i,j] == 2.0:
                glacierraster[i,j] = glacierraster[i,j]
            else:
                glacierraster[i,j] = 999
    
    # Set NoData Value
    dsband.SetNoDataValue(999)
           
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()        
    
    #Close file
    mask = None
    ds = None

def scaleimage(infile):
    '''
    scale values from 0 to 1
    '''
      
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    
    #Read input raster into array
    glacierraster = ds.ReadAsArray()
    
    #get image max and min and calculate new range
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    stats = dsband.GetStatistics(0,1)
    
    OldMin = stats[0]
    OldMax = stats[1]
    NewMin = 0.0
    NewMax = 1.0
    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)
    
    #Process the image
    print 'Converting Range to 0-1 for ', infile
    for i in range(rows):
        for j in range(cols):
            if glacierraster[i,j] == 999:
                pass
            else:
                glacierraster[i,j] = (((glacierraster[i,j] - OldMin) * NewRange) / OldRange) + NewMin
    
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()        
    
    #Close file
    dsband = None
    glacierraster = None
    ds = None  

    #Load infile again and calculate new stats (not sure how to get from raster)    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    stats = dsband.GetStatistics(0,1)
    (newmin, newmax)= dsband.ComputeRasterMinMax(0)
    (newmean, newstdv) = dsband.ComputeBandStats(1)
    dsband.SetStatistics(newmin, newmax,newmean, newstdv)
    dsband.FlushCache()       
    dsband = None  
    ds = None

          
def otsu3(infile, min_threshold=None, max_threshold=None,bins=128):    
    """Compute a threshold using a 3-category Otsu-like method
    
    data           - an array of intensity values between zero and one
    min_threshold  - only consider thresholds above this minimum value
    max_threshold  - only consider thresholds below this maximum value
    bins           - we bin the data into this many equally-spaced bins, then pick
                     the bin index that optimizes the metric
    
    We find the maximum weighted variance, breaking the histogram into
    three pieces.
    Returns the lower and upper thresholds
    
    CODE ORIGINATES FROM:
    https://code.google.com/p/python-microscopy/source/browse/cpmath/otsu.py?spec=svn723c7e28f1385990003d5994605f5c096bdd2568&r=723c7e28f1385990003d5994605f5c096bdd2568
    """
    
    #Load infile in data array    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    
    #Read input raster into array
    data = ds.ReadAsArray()
    
    #replace no data value with numpy.nan
    data[data==999.0]=numpy.nan
          
    
    assert min_threshold==None or min_threshold >=0
    assert min_threshold==None or min_threshold <=1
    assert max_threshold==None or max_threshold >=0
    assert max_threshold==None or max_threshold <=1
    assert min_threshold==None or max_threshold==None or min_threshold < max_threshold
    
    #
    # Compute the running variance and reverse running variance.
    # 
    data = data[~numpy.isnan(data)]
    data.sort() 
    if len(data) == 0:
        return 0
    var = running_variance(data)
    rvar = numpy.flipud(running_variance(numpy.flipud(data)))
    if bins > len(data):
        bins = len(data)
    bin_len = int(len(data)/bins) 
    thresholds = data[0:len(data):bin_len]
    score_low = (var[0:len(data):bin_len] * 
                 numpy.arange(0,len(data),bin_len))
    score_high = (rvar[0:len(data):bin_len] *
                  (len(data) - numpy.arange(0,len(data),bin_len)))
    #
    # Compute the middles
    #
    cs = data.cumsum()
    cs2 = (data**2).cumsum()
    i,j = numpy.mgrid[0:score_low.shape[0],0:score_high.shape[0]]*bin_len
    diff = (j-i).astype(float)
    print cs[j], cs[i], diff
    w = diff
    mean = (cs[j] - cs[i]) / diff
    mean2 = (cs2[j] - cs2[i]) / diff
    print diff, mean
    score_middle = w * (mean2 - mean**2)
    score_middle[i >= j] = numpy.Inf
    score = score_low[i*bins/len(data)] + score_middle + score_high[j*bins/len(data)]
    best_score = numpy.min(score)
    best_i_j = numpy.argwhere(score==best_score)
    return (thresholds[best_i_j[0,0]],thresholds[best_i_j[0,1]])    

def running_variance(x):
    '''Given a vector x, compute the variance for x[0:i]
    
    Thank you http://www.johndcook.com/standard_deviation.html
    S[i] = S[i-1]+(x[i]-mean[i-1])*(x[i]-mean[i])
    var(i) = S[i] / (i-1)
    
    CODE ORIGINATES FROM:
    https://code.google.com/p/python-microscopy/source/browse/cpmath/otsu.py?spec=svn723c7e28f1385990003d5994605f5c096bdd2568&r=723c7e28f1385990003d5994605f5c096bdd2568
   
    '''
    n = len(x)
    # The mean of x[0:i]
    m = x.cumsum() / numpy.arange(1,n+1)
    # x[i]-mean[i-1] for i=1...
    x_minus_mprev = x[1:]-m[:-1]
    # x[i]-mean[i] for i=1...
    x_minus_m = x[1:]-m[1:]
    # s for i=1...
    s = (x_minus_mprev*x_minus_m).cumsum()
    var = s / numpy.arange(2,n+1)
    # Prepend Inf so we have a variance for x[0]
    return numpy.hstack(([0],var))


def classify_image(infile, thresh1 = 0.0, thresh2 = 1.0):
    '''
    classify image with Otsu's thresholds
    '''
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    
    #Read input raster into array
    glacierraster = ds.ReadAsArray()
    
    #get image max and min and calculate new range
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    
    #Process the image
    print 'Classifying ', infile
    for i in range(rows):
        for j in range(cols):
            if 0.0 < glacierraster[i,j] < thresh1:
                glacierraster[i,j] = 1.0
            elif thresh1 < glacierraster[i,j] < thresh2:
                glacierraster[i,j] = 2.0
            elif thresh2 < glacierraster[i,j] < 1.0:
                glacierraster[i,j] = 3.0
            else:
                glacierraster[i,j] = 999.0
    
    
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()
    dsband.GetStatistics(0,1)
    
    
    #Close file
    dsband = None
    glacierraster = None
    ds = None  
        
#Core of Program follows

inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Kongsvegen2000.shp'
inSARfile = 'C:\Users\max\Documents\Svalbard\KongsvegenOtsuTest1992.tif'


RasterizeMask(inshapefile)
CropGlacier(inshapefile, inSARfile)
MaskGlacier(inshapefile, inSARfile)


# Define filenames
(inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
(inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
inSARcrop = inSARfilepath + '\\' + inSARfileshortname + '_crop.tif'


scaleimage(inSARcrop)

(thresh1, thresh2) = otsu3(inSARcrop)

print 'Calculated thresholds are ', thresh1,' ',  thresh2
print

classify_image(inSARcrop, thresh1, thresh2)

print
print "Done"


