# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 12:56:38 2014

@author: max
"""
import ogr, osr, os, sys, glob, numpy, gdal, gdalconst, datetime, shutil, fnmatch, subprocess

def CreatePercentageMap(filelist, outfilepath):
    '''
    Creates map showing percentage ice coverage over a given period
    
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    print ", number of days:  ", NumberOfDays
    
    firstfilename = filelist[0]
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = outfilepath + 'icechart_precentagemap.tif'
    
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
        
        #Process the image

#       #Obsolete pixel-by-pixel version, takes very long
#        for i in range(rows):
#            for j in range(cols):
#                if iceraster[i,j] == 0:
#                    outarray[i,j] = outarray[i,j] + (  0.0 / NumberOfDays) 
#                elif iceraster[i,j] == 5:
#                    outarray[i,j] = outarray[i,j] + (  5.0 / NumberOfDays) 
#                elif iceraster[i,j] == 25:
#                    outarray[i,j] = outarray[i,j] + ( 25.0 / NumberOfDays)
#                elif iceraster[i,j] == 55:
#                    outarray[i,j] = outarray[i,j] + ( 55.0 / NumberOfDays)
#                elif iceraster[i,j] == 80:
#                    outarray[i,j] = outarray[i,j] + ( 80.0 / NumberOfDays)
#                elif iceraster[i,j] == 95:
#                    outarray[i,j] = outarray[i,j] + ( 95.0 / NumberOfDays)
#                elif iceraster[i,j] == 100:
#                    outarray[i,j] = outarray[i,j] + (100.0 / NumberOfDays)
#                
#                    
#                if iceraster[i,j] == 999:
#                    outarray[i,j] = 999.0
 
        #Array calculation with numpy -- much faster
        outarray = numpy.where( (iceraster ==   0.0), (outarray + (  0.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster ==   5.0), (outarray + (  5.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster ==  25.0), (outarray + ( 25.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster ==  55.0), (outarray + ( 55.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster ==  80.0), (outarray + ( 80.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster ==  95.0), (outarray + ( 95.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster == 100.0), (outarray + (100.0 / NumberOfDays)) , outarray)
        outarray = numpy.where( (iceraster == 999.0), 999.0 , outarray)
    
       
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


def CreateIceEdgeMap(inpath, outfilepath, percentagemap, percentage):
    ''' 
    Create Ice Edge Map
    
    Treshhold the percentage per day map to 30%
    
    '''
   
    outfile = inpath + 'iceedge_map.tif'
    outshape_poly = inpath + 'iceedge_map_poly.shp'
    outshape_line = inpath + 'iceedge_map_line.shp'
    iceedge_line = inpath + 'iceedge_line.shp'
    iceedge_temp = inpath + 'iceedge_temp.shp'
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(percentagemap, gdal.GA_Update)

    
    #Read input raster into array
    iceraster = ds.ReadAsArray()
    
    #get image max and min and calculate new range
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    
    #create output images
    driver = ds.GetDriver()
    outraster = driver.Create(outfile, cols, rows, 1, gdal.GDT_Float64 )
    if outraster is None: 
        print 'Could not create ', outfile
        return
    
    # Set Geotransform and projection for outraster
    outraster.SetGeoTransform(ds.GetGeoTransform())
    outraster.SetProjection(ds.GetProjection())
    
    rows = outraster.RasterYSize
    cols = outraster.RasterXSize
    raster = numpy.zeros((rows, cols), numpy.float) 
    outraster.GetRasterBand(1).WriteArray( raster )
    
    #Create output array and fill with zeros
    outarray = numpy.zeros((rows, cols), numpy.float)    
    print '\n Thresholding Map to ' + str(percentage) + '%.'
    #Process the image
    
    outarray = numpy.where( (iceraster >= percentage) & (iceraster <= 100), percentage, 0)
    outarray[iceraster == 999] = 999
    
    #for i in range(rows):
    #   for j in range(cols):
    #        if 30 <= iceraster[i,j] <= 100:
    #           outarray[i,j] = 30 
    #        elif iceraster[i,j] < 30:
    #            outarray[i,j] = 0
    #        elif iceraster[i,j] == 999:
    #            outarray[i,j] = 999
            

    
    outband = outraster.GetRasterBand(1)
    outband.WriteArray(outarray)
    outband.FlushCache()
    


    #Clear arrays and close files
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    
    print '\n Convert ', outfile, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfile + ' -f "ESRI Shapefile" ' + outshape_poly + ' iceedge')  
    
    ### Create polyline showing ice edge
    # Convert polygon to lines
    print 'Convert ice edge map to Linestring Map'
    os.system('ogr2ogr -progress -nlt LINESTRING ' + outshape_line + ' ' + outshape_poly)
    
    print 'Convert ice edge to Linestring -- Part 1'
    os.system('ogr2ogr -where DN=0  -progress -clipsrc I:\Icecharts\landmasks\iceshape_3575.shp '+  iceedge_temp + ' ' + outshape_line)
    print 'Convert ice edge to Linestring -- Part 2'
    os.system('ogr2ogr -progress -clipsrcwhere DN=30  -clipsrc ' + outshape_poly + ' ' + iceedge_line + ' ' + iceedge_temp )
    os.remove(iceedge_temp)
    
    print 'Done Creating Ice Edge Map'      
    
##############################################################################
#  Core of program follows here
##############################################################################

print
print "*"*31
print "Running IceChartProcessing"
print "*"*31
print

outfilepath= 'I:\\IceCharts\\isdata\\'

month = 02
year_1 = 1987
year_2 = 1988

inputfolder_1 = 'I:\\IceCharts\\isdata\\' + str(year_1) + '\\EPSG3575\\'


filelist = []
text = 'compiling '

for year in range(year_1, (year_2 + 1)):
    if month > 10:
        filenames_1 = 'I:\\IceCharts\\isdata\\' + str(year) + '\\EPSG3575\\' + 'ice' + str(year) + str(month) + '*.tif'
        
    else:
        filenames_1 = 'I:\\IceCharts\\isdata\\' + str(year) + '\\EPSG3575\\' + 'ice' + str(year) + '0' + str(month) + '*.tif'
      
        
    filelist.extend(glob.glob(filenames_1))
    text = text + ' ' + str(year)
    print text


outputfile = CreatePercentageMap(filelist, outfilepath)

percentage = 30
CreateIceEdgeMap(outfilepath, outfilepath, outputfile, percentage)
    
    