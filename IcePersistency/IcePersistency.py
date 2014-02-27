# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 08:18:31 2014

@author: max
"""

import struct, numpy, gdal, gdalconst, glob, os

def Bin2GeoTiff(infile,outfilepath ):
    
    
    #Define file names 
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = outfilepath + infileshortname + '.tif'
    #Dimensions from https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    height = 448
    width = 304
    
    #for this code, inspiration found at https://stevendkay.wordpress.com/category/python/
    icefile = open(infile, "rb")
    contents = icefile.read()
    icefile.close()
    
    # unpack binary data into a flat tuple z
    s="%dB" % (int(width*height),)
    z=struct.unpack_from(s, contents, offset = 300)
    
    nsidc = numpy.array(z).reshape((448,304))
    nsidc = numpy.rot90(nsidc, 3)
    
    #write the data to a Geotiff
    
    driver = gdal.GetDriverByName("GTiff")
    outraster = driver.Create(outfile, height, width, 1, gdal.GDT_Int16 )
    if outraster is None: 
        print 'Could not create '
        return
    raster = numpy.zeros((width, height), numpy.float) 
    outraster.GetRasterBand(1).WriteArray( raster )
    
    outband = outraster.GetRasterBand(1)
    
    #Write to file     
    outband.WriteArray(nsidc)
    outband.FlushCache()
    
    #Clear arrays and close files
    outband = None
    raster = None
    outraster = None
    nsidc = None

def CreateIcePercistanceMap(inpath, outfilepath):
    '''
    Creates map showing percentage ice coverage over a given period
    
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    filelist = glob.glob(outfilepath + '*.tif')
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    print ", number of days:  ", NumberOfDays
    
    firstfilename = filelist[0]
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = inpath + 'icechart_persistencemap.tif'
    
    #open the IceChart
    icechart = gdal.Open(firstfilename, gdalconst.GA_ReadOnly)
    if firstfilename is None:
        print 'Could not open ', firstfilename
        return
    #get image size
    rows = icechart.RasterYSize
    cols = icechart.RasterXSize    
    #create output images
    driver = icechart.GetDriver()
    outraster = driver.Create(outfile, cols, rows, 1, gdal.GDT_Float64 )
    if outraster is None: 
        print 'Could not create ', outfile
        return
    
    # Set Geotransform and projection for outraster
    outraster.SetGeoTransform(icechart.GetGeoTransform())
    outraster.SetProjection(icechart.GetProjection())
    
    rows = outraster.RasterYSize
    cols = outraster.RasterXSize
    raster = numpy.zeros((rows, cols), numpy.float) 
    outraster.GetRasterBand(1).WriteArray( raster )
    
    #Create output array and fill with zeros
    outarray = numpy.zeros((rows, cols), numpy.float)    
    
    #Loop through all files to do calculation
    for infile in filelist:
        
        (infilepath, infilename) = os.path.split(infile)
        print 'Processing ', infilename
        
        #open the IceChart
        icechart = gdal.Open(infile, gdalconst.GA_ReadOnly)
        if infile is None:
            print 'Could not open ', infilename
            return
        
        #get image size
        rows = icechart.RasterYSize
        cols = icechart.RasterXSize
                
        #get the bands 
        outband = outraster.GetRasterBand(1)
        

        
        #Read input raster into array
        iceraster = icechart.ReadAsArray()
        
        #Array calculation with numpy -- much faster
        outarray = numpy.where( (iceraster >=  38), (outarray + ( 100.0 / NumberOfDays ) ) , outarray)
        outarray = numpy.where( (iceraster ==   251), 251 , outarray)
        outarray = numpy.where( (iceraster ==   252), 252 , outarray)
        outarray = numpy.where( (iceraster ==   253), 253 , outarray)
        outarray = numpy.where( (iceraster ==   254), 254 , outarray)
        outarray = numpy.where( (iceraster ==   255), 255 , outarray)
    
       
        #Clear iceraster for next loop -- just in case
        iceraster = None
        
    outband.WriteArray(outarray)
    outband.FlushCache()
       

    #Clear arrays and close files
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    
    return outfile
    print 'Done Creating Percentage Map'
    
    
##############################################################################

###   Core of Program follows here ###

##############################################################################


infilepath = 'U:\\SSMI\\IceConcentration\\NASATEAM\\final-gsfc\\north\\daily\\2012\\'
outfilepath = 'C:\\Users\\Max\\Desktop\\test\\'


filelist = glob.glob(infilepath + 'nt_201202*.bin')

for icechart in filelist:
    #Convert NSIDC files to GeoTiff
    print'convert ', icechart
    Bin2GeoTiff(icechart, outfilepath)

    
CreateIcePercistanceMap(outfilepath, outfilepath)
