# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 08:18:31 2014

@author: max
"""

import struct, numpy, gdal, gdalconst, glob, os, osr

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
    #nsidc = numpy.rot90(nsidc, 3)
    
    #write the data to a Geotiff
    
    driver = gdal.GetDriverByName("GTiff")
    outraster = driver.Create(outfile,  width, height,1, gdal.GDT_Int16 )
    if outraster is None: 
        print 'Could not create '
        return
    
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromEPSG(3411)
    outraster.SetProjection(spatialRef.ExportToWkt() )
    
    geotransform = (-3850000, 25000 ,0 ,5850000, 0, -25000)
    outraster.SetGeoTransform(geotransform)
    
    raster = numpy.zeros((height, width ), numpy.float) 
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
    
def CreateMaxMinIce(inpath, outfilepath):   
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
    
    outfile =  inpath + 'icechart_NumberOfDays.tif'   
    outfilemax = inpath + 'icechart_maximum.tif'
    outfilemin = inpath + 'icechart_minimum.tif'
    outshape_polymax = inpath + 'icechart_poly_maximum.shp'
    outshape_polymin = inpath + 'icechart_poly_minimum.shp'
    outshape_linemax = inpath + 'icechart_line_maximum.shp'
    outshape_linemin = inpath + 'icechart_line_minimum.shp'
    iceedge_linemax = inpath + 'iceedge_linemax.shp'
    iceedge_tempmax = inpath + 'iceedge_tempmax.shp'
    iceedge_linemin = inpath + 'iceedge_linemin.shp'
    iceedge_tempmin = inpath + 'iceedge_tempmin.shp'
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
    outrastermax = driver.Create(outfilemax, cols, rows, 1, gdal.GDT_Float64 )
    if outrastermax is None: 
        print 'Could not create ', outfilemax
        return
    outrastermin = driver.Create(outfilemin, cols, rows, 1, gdal.GDT_Float64 )
    if outrastermin is None: 
        print 'Could not create ', outfilemin
        return
   
   # Set Geotransform and projection for outraster
    outraster.SetGeoTransform(icechart.GetGeoTransform())
    outraster.SetProjection(icechart.GetProjection())
    outrastermax.SetGeoTransform(icechart.GetGeoTransform())
    outrastermax.SetProjection(icechart.GetProjection())
    
    outrastermin.SetGeoTransform(icechart.GetGeoTransform())
    outrastermin.SetProjection(icechart.GetProjection())
    
    rows = outrastermax.RasterYSize
    cols = outrastermax.RasterXSize
    raster = numpy.zeros((rows, cols), numpy.float) 
    outraster.GetRasterBand(1).WriteArray( raster )    
    outrastermax.GetRasterBand(1).WriteArray( raster )
    outrastermin.GetRasterBand(1).WriteArray( raster )
    #Create output array and fill with zeros
    outarray = numpy.zeros((rows, cols), numpy.float)    
    outarraymax = numpy.zeros((rows, cols), numpy.float)
    outarraymin = numpy.zeros((rows, cols), numpy.float)
    
    
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
        outarray = numpy.where( (iceraster >=  38), outarray + 1 , outarray)
        outarray = numpy.where( (iceraster ==   251), 251 , outarray)
        outarray = numpy.where( (iceraster ==   252), 252 , outarray)
        outarray = numpy.where( (iceraster ==   253), 253 , outarray)
        outarray = numpy.where( (iceraster ==   254), 254 , outarray)
        outarray = numpy.where( (iceraster ==   255), 255 , outarray)
        

       
        #Clear iceraster for next loop -- just in case
        iceraster = None
    
     #get the bands 
    outbandmax = outrastermax.GetRasterBand(1)
    outbandmin = outrastermin.GetRasterBand(1)

    outarraymax = numpy.where( (outarray == 0), 0, 1 )
    outarraymax = numpy.where( (outarray ==   251), 251 , outarraymax)
    outarraymax = numpy.where( (outarray ==   252), 252 , outarraymax)
    outarraymax = numpy.where( (outarray ==   253), 253 , outarraymax)
    outarraymax = numpy.where( (outarray ==   254), 254 , outarraymax)
    outarraymax = numpy.where( (outarray ==   255), 255 , outarraymax)
    
    outarraymin = numpy.where( (outarray == NumberOfDays), 1, 0 )
    outarraymin = numpy.where( (outarray ==   251), 251 , outarraymin)
    outarraymin = numpy.where( (outarray ==   252), 252 , outarraymin)
    outarraymin = numpy.where( (outarray ==   253), 253 , outarraymin)
    outarraymin = numpy.where( (outarray ==   254), 254 , outarraymin)
    outarraymin = numpy.where( (outarray ==   255), 255 , outarraymin)
    
    outband.WriteArray(outarray)
    outband.FlushCache()    
    
    outbandmax.WriteArray(outarraymax)
    outbandmax.FlushCache()
    
    outbandmin.WriteArray(outarraymin)
    outbandmin.FlushCache()
    #Clear arrays and close files
    outband = None
    outbandmax = None
    outbandmin = None
    iceraster = None
    outraster = None    
    outrastermax = None
    outrastermin = None
    outarray = None
    outarraymax = None
    outarraymin = None     
    print '\n Convert ', outfilemax, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfilemax + ' -f "ESRI Shapefile" ' + outshape_polymax )  
    
    print '\n Convert ', outfilemin, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfilemin + ' -f "ESRI Shapefile" ' + outshape_polymin ) 
    ### Create polyline showing ice edge
    # Convert polygon to lines
    print 'Convert ice edge map to Linestring Map'
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_linemax + ' ' + outshape_polymax)
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_linemin + ' ' + outshape_polymin)
    
    print 'Convert ice edge to Linestring -- Part 1'
    os.system('ogr2ogr -where DN=0  -progress -clipsrc C:\Users\max\Documents\Icecharts\landmasks\iceshape_3575.shp '+  iceedge_tempmax + ' ' + outshape_linemax)
    os.system('ogr2ogr -where DN=0  -progress -clipsrc C:\Users\max\Documents\Icecharts\landmasks\iceshape_3575.shp '+  iceedge_tempmin + ' ' + outshape_linemin)
        
    print 'Convert ice edge to Linestring -- Part 2'
    os.system('ogr2ogr -progress -clipsrcwhere DN=1  -clipsrc ' + outshape_polymax + ' ' + iceedge_linemax + ' ' + iceedge_tempmax )
    os.remove(iceedge_tempmax)
    os.system('ogr2ogr -progress -clipsrcwhere DN=1  -clipsrc ' + outshape_polymin + ' ' + iceedge_linemin + ' ' + iceedge_tempmin )
    os.remove(iceedge_tempmin)
            
    print 'Done Creating Percentage Map'        
    return outfilemax, outfilemin
    
     
     
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

max_ice, min_ice = CreateMaxMinIce(outfilepath, outfilepath)