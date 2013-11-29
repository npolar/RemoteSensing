# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 09:04:29 2013

@author: max

THIS VERSION GREW AND GREW AND NEED CLEAN UP IN MANY WAYS

Classification into Glacier Surface Types

    Steps:        
    #Make Raster from shapefile
    RasterizeMask(inshapefile)
    
    #Crop SAR file to extents of shapefile
    CropGlacier(inshapefile, inSARfile)

    #Masks Area outside glacier with no data value -999.0    
    MaskGlacier(inshapefile, inSARfile)
    
    #Convert image values to range 0 to 1 for Otsu input
    scaleimage(inSARcrop)
    
    #Call Otsu's method
    (thresh1, thresh2) = otsu3(inSARcrop)
    
    #Apply the thresholds gotten by Otsu
    classify_image(inSARcrop, thresh1, thresh2)
    
    #Apply Sieve filter to remove noise
    ApplySieve(inSARcrop)
    
    #Convert GST raster to GST shapefile
    PolygonizeGST(inSARcrop)

"""

#import modules

import ogr, os, gdal, numpy, glob, shutil, sys
import matplotlib.pyplot as plt


# Define Functions

def RasterizeMask(infile):
    '''
    Takes infile and creates raster from shapefile
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
    Crops SAR image to extent of Mask, i.e. glacier extent
    
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    outraster = inSARfilepath + '/' + inSARfileshortname + '_GST.tif'
    outraster2 = inSARfilepath + '/' + inSARfileshortname + '_SAR.tif'
    
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
    print '\n Subsetting maskfile ', inSARfilename, ' to glacier extent'
    os.system('gdal_translate -projwin ' + str(maskextent[0]) + ' ' + str(maskextent[3]) + ' ' + str(maskextent[1]) + ' ' + str(maskextent[2]) + ' ' + inSARfile + ' ' + outraster)
    
    # crop second image to keep with gdal_translate -- call gdal_rasterize commandline
    print '\n Subsetting SARfile ', inSARfilename, ' to glacier extent'
    os.system('gdal_translate -projwin ' + str(maskextent[0]) + ' ' + str(maskextent[3]) + ' ' + str(maskextent[1]) + ' ' + str(maskextent[2]) + ' ' + inSARfile + ' ' + outraster2)
    
    #Close files 
    maskshape = None
    
def MaskGlacier(inshapefile, inSARfile):
    '''
    Masks Cropped SARfile
    
    Sets all values outside mask to -999.0 no data value. The same file will receive classification
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '/' + inSARfileshortname + '_GST.tif'
    
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
                glacierraster[i,j] = -999.0
    
   
    
    # Set NoData Value
    dsband.SetNoDataValue(-999.0)
           
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()        
    
    #make a copy to keep the masked SAR
    maskedSAR = inSARfilepath + '/' + inSARfileshortname + '_SARmask.tif'
    shutil.copyfile(inSARcrop, maskedSAR)    
    
    #Close file
    mask = None
    ds = None

def scaleimage(infile):
    '''
    scale values from 0 to 1, needed by Otsu input requirement
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
            if glacierraster[i,j] == -999.0:
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
    return OldMin, OldMax
          
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
    
    CODE ORIGINATES FROM, adjusted to read gdal GeoTIFF:
    https://code.google.com/p/python-microscopy/source/browse/cpmath/otsu.py?spec=svn723c7e28f1385990003d5994605f5c096bdd2568&r=723c7e28f1385990003d5994605f5c096bdd2568
    """
    
    #Load infile in data array    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    
    #Read input raster into array
    data = ds.ReadAsArray()
    
    #replace no data value with numpy.nan
    data[data==-999.0]=numpy.nan
    
    print 'Apply Otsu\'s filter on ', infile     
    
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
    w = diff
    mean = (cs[j] - cs[i]) / diff
    mean2 = (cs2[j] - cs2[i]) / diff
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


def classify_image(infile, inshapefile, thresh1 = 0.0, thresh2 = 1.0):
    '''
    classify image with Otsu's thresholds
    '''
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, inextension) = os.path.splitext(infilename)
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    glaciername = inshapefileshortname[:-11] + infileshortname[6:10]
   
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
    
    #case1 = numpy.where( (glacierraster >= 0.0) & (glacierraster < thresh1), 1.0, 0.0)
    #case2 = numpy.where( (glacierraster >= thresh1) & (glacierraster < thresh2), 2.0, 0.0)
    #case3 = numpy.where( (glacierraster >= thresh2) & (glacierraster <= 1.0), 3.0, 0.0)
    #case4 = numpy.where( (glacierraster > 1.0), numpy.nan, 0.0)   
    #glacierraster = case1 + case2 + case3 + case4 
    
    for i in range(rows):
        for j in range(cols):
            if 0.0 <= glacierraster[i,j] < thresh1:
                glacierraster[i,j] = 1.0
            elif thresh1 <= glacierraster[i,j] < thresh2:
                glacierraster[i,j] = 2.0
            elif thresh2 <= glacierraster[i,j] <= 1.0:
                glacierraster[i,j] = 3.0
            else:
                glacierraster[i,j] = -999.0
    
   
    #Calculate numbers of each class
    ice =  (glacierraster == 1.0).sum()   
    si =  (glacierraster == 2.0).sum() 
    firn =  (glacierraster == 3.0).sum() 
    background = (glacierraster == -999.0).sum()
    total = glacierraster.size
    
    
    #write occurrences to file
    filename = infilepath + '\\' + 'class_count.txt'
    f = open(filename, 'a')
    f.write(glaciername + ' ' +  str(ice) + ' ' +  str(si) + ' ' +  str(firn) + ' ' +  str(background) +  ' ' + str(total) + "\n")
    f.close()    
    
    
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()
    dsband.GetStatistics(0,1)
    
    
    #Close file
    dsband = None
    glacierraster = None
    ds = None  
    
    #Load infile again and calculate new stats (not sure how to get from raster)    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    (newmin, newmax)= dsband.ComputeRasterMinMax(0)
    (newmean, newstdv) = dsband.ComputeBandStats(1)
    dsband.SetStatistics(newmin, newmax,newmean, newstdv)
    dsband.FlushCache()       
    dsband = None  
    ds = None


def ApplySieve(infile):
    '''
    applies gdal_sieve
        * 4-connectedness seemed best, 8 removes too muc
        * 60 filter seemed ok
    
    '''    
    
    print '\n Apply gdal_sieve'
    #os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -burn 2 -l ' + shapefileshortname +' -tr 1000 -1000 ' +  shapefile + ' ' + outraster)
    os.system('gdal_sieve.py -st 60 -4 -of GTiff ' + infile)
            
    

def PolygonizeGST(infile, inshapefile):
    '''
    creates shapefile out of GST raster
    '''
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    outfile = infilepath + '/' + infileshortname + '.shp'    
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    glaciername = inshapefileshortname[:-11]
    quality = 1 # Set 1 to 6 for quality
    
    print '\n Convert ', infile, ' to shapefile.'
    os.system('gdal_polygonize.py ' + infile + ' -f "ESRI Shapefile" ' + outfile + ' GST')    
    
    #Add glaciername
    driver = ogr.GetDriverByName('ESRI Shapefile')
    indataset = driver.Open(outfile, 1)
    if indataset is None:
        print ' Could not open file'
        sys.exit(1)
    inlayer = indataset.GetLayer()
    
    fieldDefn = ogr.FieldDefn( 'glacier', ogr.OFTString)
    fieldDefn.SetWidth(20)
    inlayer.CreateField(fieldDefn)
    
    fieldDefn2 = ogr.FieldDefn('quality', ogr.OFTInteger)
    inlayer.CreateField(fieldDefn2)
    
    feature = inlayer.GetNextFeature()
    while feature:
        feature.SetField('glacier', glaciername )
        feature.SetField('quality', quality )
        inlayer.SetFeature(feature)
        feature.Destroy
        feature = inlayer.GetNextFeature()
    
       
    #close the shapefiles
    indataset.Destroy()
    
def PlotHistogram(infile, thresh1, thresh2):
    ''' plots histogram '''
    
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '/' + inSARfileshortname + '_SARmask.tif'
    histfilename = inSARfilepath + '/' + inSARfileshortname + '_hist.jpg'
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(inSARcrop, gdal.GA_Update)
    raster = ds.ReadAsArray()
    
    plt.figure()
    plt.hist(raster.flatten(), 128, range = (-25.0, 10.0))
    plt.axvline(x=thresh1, ymin=0, ymax=6000, linewidth=1, color='r')
    plt.axvline(x=thresh2, ymin=0, ymax=6000, linewidth=1, color='r')
    plt.title(inSARfileshortname)
    
    plt.savefig(histfilename)

def RenameFiles(inshapefile):
    '''
    rename all files produced
    works for mosaicXXXX.tif in F:\SvalbardSARbyYear\*.tif
    very simple, no universal method -- dependent on file location as given
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
        
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    glaciername = inshapefileshortname[0:-11]
       
    print 'renaming files'
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.tif')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)        
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.tif'
        os.rename(oldname, newname )
        
    filelist = glob.glob('F:\SvalbardSARbyYear\*SAR.tif')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_SAR.tif'
        os.rename(oldname, newname )

    filelist = glob.glob('F:\SvalbardSARbyYear\*SARmask.tif')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_SARmask.tif'
        os.rename(oldname, newname )
        
    filelist = glob.glob('F:\SvalbardSARbyYear\*hist.jpg')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_hist.jpg'
        os.rename(oldname, newname )
    
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.dbf')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.dbf'
        os.rename(oldname, newname )   
        
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.prj')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.prj'
        os.rename(oldname, newname ) 
    
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.shx')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.shx'
        os.rename(oldname, newname ) 
     
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.shp')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.shp'
        os.rename(oldname, newname )
        
        
#Core of Program follows

#Define location and name of glaciermask
inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\KongsvegenBuffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Monacobreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Lilliehookbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Fjortendejulibreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\AustreBroggerbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Hansbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Hayesbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Ulvebreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Uversbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Comfortlessbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Etonbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Holtedalfonna2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Aavatsmarkbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Osbornebreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Wahlenbergbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Kuhrbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Negribreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Nordsysselbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Borebreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Edvardbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Nordsysselbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Nathorstbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Penckbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Veteranbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Hinlopenbreen2000_Buffer.shp'

# Define location and name of GeoTIFF containing SAR image
# Convert from BEAM-DIMAP with Nest>Graphs>Batch Processing 

filelist = glob.glob('F:\SvalbardSARbyYear\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\Kongsfjorden\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\SouthSpitsbergen\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\CentralSpitsbergen\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\Nordaustlandet\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')


#Iterate through filelist with SAR files
for inSARfile in filelist:
    
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '\\' + inSARfileshortname + '_GST.tif'
    
    #Make Raster from shapefile
    RasterizeMask(inshapefile)
    
    #Crop SAR file to extents of shapefile
    CropGlacier(inshapefile, inSARfile)

    #Masks Area outside glacier with no data value -999.0    
    MaskGlacier(inshapefile, inSARfile)
    
    #Convert image values to range 0 to 1 for Otsu input
    (oldmin, oldmax) = scaleimage(inSARcrop)
    print 'Minimum and Maximum are ', oldmin,' ',  oldmax
    
    #Call Otsu's method
    (thresh1, thresh2) = otsu3(inSARcrop)
    print 'Calculated thresholds are ', thresh1,' ',  thresh2
    print
    
    #Calculate back threshold in dB
    thresh1dB = (oldmax-oldmin) * thresh1 + oldmin
    thresh2dB = (oldmax-oldmin) * thresh2 + oldmin
    print 'Calculated thresholds in dB are ', thresh1dB,' ',  thresh2dB
     
    
    #write thresholds to file
    filename = inSARfilepath + '\\' + 'thresholds.txt'
    f = open(filename, 'a')
    f.write(inSARcrop + ' ' +  str(thresh1dB) + ' ' +  str(thresh2dB)+ "\n")
    f.close()
    #plot histogram
    PlotHistogram(inSARfile, thresh1dB, thresh2dB)
    
    #Apply the thresholds gotten by Otsu
    classify_image(inSARcrop, inshapefile, thresh1, thresh2)
    
    #Apply Sieve filter to remove noise
    ApplySieve(inSARcrop)
    
    #Convert GST raster to GST shapefile
    PolygonizeGST(inSARcrop, inshapefile)
    
#end for

#rename files
RenameFiles(inshapefile)


print
print "Done"


