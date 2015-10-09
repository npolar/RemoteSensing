# -*- coding: utf-8 -*-
"""
Created on Tue Dec 03 13:31:59 2013

Processing met.no ice charts

Parameters are set in Core of the Program, see below all functions


 * ReprojectShapefile -- reprojects the shapefile
 * Shape2Raster -- converts shapefile to GeoTIFF raster
 * AddMissingDays -- a missing file is replaced with the next available previous day.
 * CreateMapFastIceDays -- a map whose values indicated (non-consecutive) days of fast ice
 * CreateConsecFastIceDays -- map showing consecutive days of fast ice (wanted minimum number as input)
 * CreatePercentageMap -- map showing percentage sea ice cover over a given period
 * CreateIceEdgeMap -- map showing ice egde, percentage defining edge given as input, also creating shapefile only containing actual ice edge
 
 TO COME
 
 * CreateDecadalAverage -- map showing decadal percentage coverage (10/20/30 year chosen as input)
 * CreateDecadalIceEdge -- creating ice edge map from decadal average map (percentage defining edge given as input)
 
@author: max
"""
# Import Modules
import ogr, osr, os, sys, glob, numpy, gdal, gdalconst, datetime, shutil, fnmatch, subprocess



##############################################################################
#  Defining Functions
##############################################################################

def CreateFilelistSHP(startyear, startday, startmonth, endyear, endday, endmonth, infilepath):
    '''
        Creates filelist for icechartnames including date
    '''
    
    
    #http://pymotw.com/2/datetime/
    #http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    d1 =  datetime.date(startyear, startmonth, startday)
    d2 =  datetime.date(endyear, endmonth, endday)
    diff = datetime.timedelta(days=1)
    
    #date3 is working date to be looped through  -- set to start date   
    d3 = d1

    print 'Create Filelist in ', infilepath
    
    
    filelist = []
    
    while d3 != (d2 + diff):
        checkfile = infilepath + "ice" + d3.strftime('%Y%m%d') +  '.shp'
        print checkfile        
        #If file exists add to list (weekends do not exist)        
        if os.path.isfile(checkfile): 
            filelist.append(checkfile)
            
            
        d3 = (d3 + diff)    
    
    return filelist

def CreateFilelistTIFF(startyear, startday, startmonth, endyear, endday, endmonth, infilepath):
    '''
        Creates filelist for icechartnames including date
    '''
    
    
    #http://pymotw.com/2/datetime/
    #http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    d1 =  datetime.date(startyear, startmonth, startday)
    d2 =  datetime.date(endyear, endmonth, endday)
    diff = datetime.timedelta(days=1)
    
    #date3 is working date to be looped through  -- set to start date   
    d3 = d1
    
    print 'Create Filelist in ', infilepath
    
    
    filelist = []
    
    while d3 != (d2 + diff):
        checkfile = infilepath + "ice" + d3.strftime('%Y%m%d') +  '_EPSG3575.tif'
        print checkfile        
        #If file exists add to list (weekends do not exist)        
        if os.path.isfile(checkfile): 
            filelist.append(checkfile)
            print 'appending ', checkfile
        d3 = (d3 + diff)    
    print filelist
    return filelist
def ReprojectShapefile(infile, outfilepath, inproj, outproj):
    '''
    Reprojects the shapefile given in infile
    
    inproj and outproj in format "EPSG:3575", for the filename the ":" is 
    removed in the function
    
    Assumes existence of folder as "EPSG3575" or "EPSG32633" or...
    '''
    
    #Define outputfile name
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    
    
    reprshapeshortname = infileshortname + '_' + outproj[0:4] + outproj[5:10]
    reprshapefile = outfilepath + '\\'+ reprshapeshortname + extension
    
    #Reproject using ogr commandline
    print 'Reproject Shapefile'    
    print 'ogr2ogr -s_srs ' + inproj + ' -t_srs ' + outproj + ' '  + reprshapefile + ' ' + infile 
    os.system('ogr2ogr -s_srs ' + inproj + ' -t_srs ' + outproj + ' '  + reprshapefile + ' ' + infile )
    print 'Done Reproject'

    return reprshapefile


def Shape2Raster(shapefile, rasterresolution, location):
    '''
    Take the input shapefile and create a raster from it
    Subsets to location  if wanted
    Same name and location as input but GeoTIFF
    '''
    
    #check if shapefile exists, may not if failed in reprojection
    if shapefile==None:
        return

    #Get Path and Name of Inputfile
    (shapefilefilepath, shapefilename) = os.path.split(shapefile)             #get path and filename seperately
    (shapefileshortname, extension) = os.path.splitext(shapefilename)           #get file name without extension
    
    # The land area to be masked out, also being a shapefile to be rasterized
    SvalbardCoast = 'I:\Icecharts\landmasks\s100-landp_3575.shp'
    #MainlandCoast = 'I:\Icecharts\landmasks\ArcticSeaNoSval_3575.shp'
    
    #SvalbardCoast = 'I:\Icecharts\landmasks\s100-landp_32633.shp'
    
    print "\n \n Rasterizing", shapefilename, '\n'
    
    # The raster file to be created and receive the rasterized shapefile
    outrastername = shapefileshortname + '.tif'
    outraster = shapefilefilepath + '\\' + outrastername
    
    #Raster Dimensions of Raster to be created
    #For dimensions look at example file in EPSG 3575
    x_resolution = rasterresolution
    y_resolution = -rasterresolution  #VALUE MUST BE MINUS SINCE DOWNWARD !! 
    
    #Individual Corner Coordinates
    upperleft_x = location[0]        
    upperleft_y = location[1]     
    lowerright_x =location[2]    
    lowerright_y =location[3]  

    #Calculate columns and rows of raster based on corners and resolution    
    x_cols = int((lowerright_x - upperleft_x) / x_resolution )
    y_rows = int((lowerright_y - upperleft_y) / y_resolution)

    #Create raster with values defined above
    driver = gdal.GetDriverByName('GTiff')
    outfile = driver.Create(outraster, x_cols, y_rows, 1, gdal.GDT_Float64)    
    
    #Get Projection from reprshapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')    
    temp = driver.Open( reprshapefile, 0)
    layer = temp.GetLayer()
    reference = layer.GetSpatialRef()
    projection = reference.ExportToWkt()
    
    #Set Projection of raster file
    outfile.SetGeoTransform([upperleft_x, x_resolution, 0.0, upperleft_y, 0.0, y_resolution])
    outfile.SetProjection(projection)
    
    #Close reprshapefile
    temp.Destroy
    
    #Fill raster with zeros
    rows = outfile.RasterYSize
    cols = outfile.RasterXSize
    raster = numpy.zeros((rows, cols), numpy.float) 
    outfile.GetRasterBand(1).WriteArray( raster )
    outfile = None
    
    
    # Rasterize first Ice Type and at same time create file -- call gdal_rasterize commandline
    # Check if gdal_rasterize has crashed, which it does if there is a corrupt shapefile
    print '\n Open Water'
    command_run = subprocess.call('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -b 1 -burn 5 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)    
    #THIS WAS MEANT TO CATCH CRASH OF gdal_rasterize, but when no Open Water, all the rest is skipped!    
    #if command_run != 0:            
    #    print 'corrupt shapefile skipped'
    #    return
    
    # Rasterize the other Ice types, adding them to the already created file
    print '\nVery Open Drift Ice'
    subprocess.call('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Very Open Drift Ice\'\" -b 1 -burn 25 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Open Drift Ice'
    subprocess.call('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Drift Ice\'\" -b 1 -burn 55 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Close Drift Ice'
    subprocess.call('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Close Drift Ice\'\" -b 1 -burn 80 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Very Close Drift Ice'
    subprocess.call('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Very Close Drift Ice\'\" -b 1 -burn 95 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Fast Ice'
    subprocess.call('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Fast Ice\'\" -b 1 -burn 100 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)

    
    # Rasterize Spitsbergen land area on top
    print '\n SvalbardRaster'
    subprocess.call('gdal_rasterize  -b 1 -burn 999 -l s100-landp_3575 '  +  SvalbardCoast + ' ' + outraster)
    
     # Rasterize Greenland and other land area on top
    print '\n MainlandRaster'
    #subprocess.call('gdal_rasterize  -b 1 -burn 999 -l ArcticSeaNoSval_3575 '  +  MainlandCoast + ' ' + outraster)
    
    
    print "\n \n Done rasterizing", shapefilename, '\n'
    

def AddMissingDays(outfilepath, filelist):
    '''
    if file is missing, replace by previous one
    
    look through all files located at outfilepath
    '''
    #register all gdal drivers
    gdal.AllRegister()    
    
    # Create a list of all available raster icechart files
    #filelist = sorted(glob.glob(outfilepath + "\\*.tif"))
    
    #Get first dates filename -- backwards works when name ice20120131_EPSG3575.tif
    date1 = int(filelist[0][-21:-13])
    year1 = int(filelist[0][-21:-17])
    month1 = int(filelist[0][-17:-15])   
    day1 = int(filelist[0][-15:-13])
    
    #Get last dates from filesname
    date2 = int(filelist[-1][-21:-13])
    year2 = int(filelist[-1][-21:-17])
    month2 = int(filelist[-1][-17:-15])   
    day2 = int(filelist[-1][-15:-13])
    
        
    #Get first dates filename -- backwards works when name ice20120131_EPSG3575.tif
    #date1 = int(filelist[0][-22:-14])
    #year1 = int(filelist[0][-22:-18])
    #month1 = int(filelist[0][-18:-16])   
    #day1 = int(filelist[0][-16:-14])
    
    #Get last dates from filesname
    #date2 = int(filelist[-1][-22:-14])
    #year2 = int(filelist[-1][-22:-18])
    #month2 = int(filelist[-1][-18:-16])   
    #day2 = int(filelist[-1][-16:-14])
    
    #http://pymotw.com/2/datetime/
    #http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    d1 =  datetime.date(year1, month1, day1)
    d2 =  datetime.date(year2, month2, day2)
    diff = datetime.timedelta(days=1)
    
    #date3 is working date to be looped through  -- set to start date   
    date3 = date1
    d3 = d1

    print 'Search for missing files and replace with precious ones'
    
    while d3 != (d2 + diff):
        
        #Create filename whose existence is to be checked
        checkfilename = outfilepath + "ice" + d3.strftime('%Y%m%d') +  filelist[1][-13:]
        print 'checking ', checkfilename, d3, (d2 + diff)       
        if (checkfilename in filelist) is False:
            
            #Create filename previous day
            previousday = d3 - diff
            replacingfile = outfilepath + "ice" + previousday.strftime('%Y%m%d') +  filelist[1][-13:]
            
            
            #Replace by previous day         
            print  os.path.split(checkfilename)[1] + " is missing!"
            print "Replacing " + os.path.split(checkfilename)[1] + " with " + os.path.split(replacingfile)[1]
            
            src_ds = gdal.Open( replacingfile )
            if src_ds is None:
                print 'Could not open ', replacingfile
            driver = src_ds.GetDriver()
            driver.Register()
            dst_ds = driver.CreateCopy(checkfilename, src_ds , 0 )
    
            # close properly the dataset
            dst_ds = None
            src_ds = None
            
            
            #Replace missing shapefile by previous one            
            checkshapefilename = outfilepath + "ice" + d3.strftime('%Y%m%d') +  filelist[1][-13:-4]
            replacingshapefile =  outfilepath + "ice" + previousday.strftime('%Y%m%d') +  filelist[1][-13:-4]
            print "Replacing " + os.path.split(checkshapefilename)[1] +".shp" + " with " + os.path.split(replacingshapefile)[1] + ".shp"
            print
            shutil.copy((replacingshapefile +".shp"), (checkshapefilename + ".shp"))
            shutil.copy((replacingshapefile +".shx"), (checkshapefilename + ".shx"))
            shutil.copy((replacingshapefile +".dbf"), (checkshapefilename + ".dbf"))
            shutil.copy((replacingshapefile +".prj"), (checkshapefilename + ".prj"))
            
        #Increase working date for next loop
        date3 = int((d3 + diff).strftime('%Y%m%d'))         
        d3 = (d3 + diff)

                
  
    print "Done replacing missing dates"    
    
    
def CreateMapFastIceDays(inpath, outfilepath, filelist):
    '''
    Creates Map where number indicates days with fast ice, 999 is land
    not considering if days are consecutive
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    #filelist = glob.glob(outfilepath + '*.tif')
    
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    firstfilename = outfilepath + infileshortname + '.tif'
        
    outfile = outfilepath[0:-9] + 'icechart_fasticedays_' + filelist[0][-21:-15]  + '_' + filelist[-1][-21:-15]  + '.tif'
    
    ##### Create copy of original Tiff which then receives the processed map #####    
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
        (infileshortname, extension) = os.path.splitext(infilename)
        infile = outfilepath+ infileshortname + '.tif'
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
        
        #Count pixel, if fastice add one, of not keep value -- add land mask
        outarray = numpy.where( (iceraster == 100), outarray + 1 , outarray)
        #outarray = numpy.where( (iceraster >= 80), outarray + 1 , outarray)
        outarray = numpy.where( (iceraster == 999), 999 , outarray)

    #Write to file     
    outband.WriteArray(outarray)
    outband.FlushCache()
       

    #Clear arrays and close files
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    print 'Done creating map of fastice-days'
        

def CreatePercentageMap(inpath, outfilepath, filelist):
    '''
    Creates map showing percentage ice coverage over a given period
    
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    #filelist = glob.glob(outfilepath + '*.tif')
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    print ", number of days:  ", NumberOfDays
    
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    firstfilename = outfilepath + infileshortname + '.tif'   
    outfile = outfilepath[0:-9] + 'icechart_precentagemap' + filelist[0][-21:-15]  + '_' + filelist[-1][-21:-15]  + '.tif'
    
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
        (infileshortname, extension) = os.path.splitext(infilename)
        infile = outfilepath + infileshortname + '.tif'
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
   
    outfile = outfilepath[0:-9] + 'iceedge_map.tif'
    outshape_poly = outfilepath[0:-9] + 'iceedge_map_poly.shp'
    outshape_line = outfilepath[0:-9] + 'iceedge_map_line.shp'
    iceedge_line = outfilepath[0:-9] + 'iceedge_line.shp'
    iceedge_temp = outfilepath[0:-9] + 'iceedge_temp.shp'
    
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
    os.system('ogr2ogr -where DN=0  -progress -clipsrc I:\Icecharts\landmasks\iceshape_32633.shp '+  iceedge_temp + ' ' + outshape_line)
    print 'Convert ice edge to Linestring -- Part 2'
    os.system('ogr2ogr -progress -clipsrcwhere DN=30  -clipsrc ' + outshape_poly + ' ' + iceedge_line + ' ' + iceedge_temp )
    os.remove(iceedge_temp)
    
    print 'Done Creating Ice Edge Map'      


def CreateMapConsecutiveFastIceDays(inpath, outfilepath, consecutivenumber, filelist):
    '''
    Creates Map where number indicates days with fast ice, 999 is land
    considering if days are consecutive
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    #filelist = glob.glob(outfilepath + '*.tif')
    
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    firstfilename = outfilepath + infileshortname + '.tif'    
    outfile = outfilepath[0:-9] + 'icechart_consecutive_fasticedays' + filelist[0][-21:-15] + '_' + filelist[-1][-21:-15] + '.tif'
    
    ##### Create copy of original Tiff which then receives the processed map #####    
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
    #fill previousraster with ones
    previousraster = outarray + 1
    countingraster = outarray
    
    #Loop through all files to do calculation
    for infile in filelist:
        
        (infilepath, infilename) = os.path.split(infile)
        (infileshortname, extension) = os.path.splitext(infilename)
        infile = outfilepath + infileshortname + '.tif'
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
        

        ###CALCULATE CONSECUTIVE DAYS###
        #Read input raster into array
        iceraster = icechart.ReadAsArray()
        
        #Add one where fast ice otherwise keep number, count in countingraster
        outarray = numpy.where( (iceraster == 100), outarray + 1 , outarray)
        #outarray = numpy.where( (iceraster >=80), outarray + 1 , outarray)
        countingraster = numpy.where( (iceraster == 100), countingraster + 1 , countingraster)
        #countingraster = numpy.where( (iceraster >=80), countingraster + 1 , countingraster)
        
        #Reset pixel to zero when previous day was not fast ice AND if less than wanted number (otherwise pixel is valid)
        outarray = numpy.where( (numpy.logical_and((previousraster == 0) , (countingraster < consecutivenumber))), 0 , outarray)
        #NUMBER IS NOT CONSECUTIVE BUT SEVERAL PERIODS OF CONSECUTIVE ADDED!!
        #reset counting raster to 0 where outarray was set to 0 in line above
        countingraster = numpy.where( (outarray == 0), 0 , countingraster)
        #add landmask
        outarray = numpy.where( (iceraster == 999), 999 , outarray)
               
        #New previousraster
        previousraster = numpy.where( (iceraster == 100), 1 , 0)
        #previousraster = numpy.where( (iceraster >= 80), 1 , 0)
        
    
    #Has to finish after last run checking last image
    outarray = numpy.where((countingraster < consecutivenumber), 0 , outarray)
    outarray = numpy.where( (iceraster == 999), 999 , outarray)

    
    #Write to file     
    outband.WriteArray(outarray)
    outband.FlushCache()
       

    #Clear arrays and close files
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    print 'Done creating map of consecutive fastice-days'    
    
    
def MaskArea(shapefile):
    
    #
    #Get Path and Name of Inputfile
    (shapefilefilepath, shapefilename) = os.path.split(shapefile)             #get path and filename seperately
    (shapefileshortname, extension) = os.path.splitext(shapefilename) 
    # The raster file to be created and receive the rasterized shapefile
    inputrastername = shapefileshortname + '.tif'
    inputraster = shapefilefilepath + '\\' + inputrastername
    print inputraster
    #maskfile = 'I:\\IceCharts\\Kit\\VestSpitsbergen\\masklayer.tif'
    maskfile = 'I:\\IceCharts\\Isfjorden\\isfjordenmask.tif'
    
    # register all of the GDAL drivers
    gdal.AllRegister()
    
    # open the image
    icechart = gdal.Open(inputraster, gdalconst.GA_Update)
    if icechart is None:
        print 'Could not open ', infileshortname
        sys.exit(1)
    
    #Read input raster into array
    iceraster = icechart.ReadAsArray()
    
    # open the image
    mask = gdal.Open(maskfile, gdalconst.GA_ReadOnly)
    if mask is None:
        print 'Could not open ', maskfile
        sys.exit(1)
    
    #Read input raster into array
    maskraster = mask.ReadAsArray()
    
    iceraster = numpy.where( (maskraster == 0) , iceraster, 999)
    
    iceband = icechart.GetRasterBand(1)
    iceband.WriteArray(iceraster)
    iceband.FlushCache()
    
    iceband = None
    iceraster = None
    icechart = None
    mask = None
    maskraster = None
    
    
##############################################################################
#  Core of program follows here
##############################################################################

print
print "*"*31
print "Running IceChartProcessing"
print "*"*31
print
startyear = 2015
endyear = 2015

#FOR EVERY YEAR ONLY THE FOLLOWING MONTH
startday = 1
startmonth = 5

endday = 31
endmonth = 5

year = startyear
while year <= endyear:
    # Path where shapefiles are located and output files to be stored
    
    infilepath = 'I:\\IceCharts\\isdata\\' + str(year) + '\\Barents_shp\\'
    #outfilepath = 'I:\\IceCharts\\isdata\\' + str(year) + '\\EPSG3575\\'
    #infilepath = 'G:\\IceCharts\\Data\\'
    #outfilepath = 'G:\\Icecharts\\Data\\EPSG3575\\'
    outfilepath = 'I:\\IceCharts\\Isfjorden\\' + str(year) + '\\EPSG3575\\'
    #outfilepath = 'I:\\IceCharts\\Glen\\' + str(year) + '\\EPSG32633\\'
    #outfilepath = 'I:\\IceCharts\\Kit\\'
    
    
    
    #################### ADJUST ALL PARAMETERS HERE ##############################  
    #Define parameters
    inproj = "EPSG:4326"  #EPSG:4326 is map projection of met.no shapefiles
    #outproj = "EPSG:32633" #EPSG:3575 for Arctic Ocean, EPSG:32633 for Svalbard
    outproj = "EPSG:3575" #EPSG:3575 for Arctic Ocean, EPSG:32633 for Svalbard
    
    rasterresolution = 100.0   #Svalbard
    #rasterresolution = 1000.0   #All Arctic
    
    ### SUBSET COORDINATES IN EPSG3575
    #All the Arctic Ocean
    #x_origin = -3121844.7112938007
    #y_origin = 482494.5951363358
    #x_lowright = 2361155.2887061993
    #y_lowright = -3396505.404863664
    
    #Glen
    #x_origin = 381990.0
    #y_origin = 8994970.0
    #x_lowright = 849990.0
    #y_lowright = 8444970.0
    
    
    #Svalbard Subset -- Activate if only Svalbard is to be rasterized
    #x_origin = -90000.0  
    #y_origin = -962000.0
    #x_lowright = 505000.0
    #y_lowright = -1590000.0
    
    #Isfjorden Subset
    x_origin = 83000.0
    y_origin = -1237947.0
    x_lowright = 166247.0
    y_lowright = -1338500.0
    
    #Vest Spitsbergen
    #x_origin = -90000.0
    #y_origin = -1187934.0
    #x_lowright = 171359.0
    #y_lowright = -1458582.0
    
    location = [x_origin, y_origin, x_lowright, y_lowright]
    
    ###  landmask path located in Shape2Raster but should remain fixed ###
    
    ################### END ADJUST PARAMETERS ####################################
    
    
    filelist = CreateFilelistSHP(year, startday, startmonth, year, endday, endmonth, infilepath)
    
    
    for icechart in filelist:
        
        #Reproject Shapefile
        reprshapefile = ReprojectShapefile(icechart, outfilepath, inproj, outproj)
        
        #Convert Shapefile to Raster
        Shape2Raster(reprshapefile, rasterresolution, location)
        
        #Mask Area if needed, file masklayer.tif needs to be in 
        MaskArea(reprshapefile)
        
        #set shapefile to None so that it stays None in case reprojection fails.
        reprshapefile = None
    
    #Add Missing Days (like weekends or faulty shapefile)
    filelist = CreateFilelistTIFF(year, startday, startmonth, year, endday, endmonth, outfilepath)    
    AddMissingDays(outfilepath, filelist)
    #Repeat filelist since files were added -- input to functions
    filelist = CreateFilelistTIFF(year, startday, startmonth, year, endday, endmonth, outfilepath)
    
    #Creates map with number of days of fast ice per pixel
    CreateMapFastIceDays(infilepath, outfilepath, filelist)
    
    #Create Consecutive Fasticedays
    consecutivenumber = 14
    CreateMapConsecutiveFastIceDays(infilepath, outfilepath, consecutivenumber, filelist)
    
    #Creates map showing percentage of sea ice per pixel
    outputfile = CreatePercentageMap(infilepath, outfilepath, filelist)
    
    #Creates ice edge map
    percentage = 30  #Set percentage for ice edge map
    #CreateIceEdgeMap(infilepath, outfilepath, outputfile, percentage)
    year = year +1


print
print "*"*23
print "Done IceChartProcessing"
print "*"*23
#End