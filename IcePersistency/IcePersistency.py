
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 08:18:31 2014
@author: max
 
Creating ice persistency maps from NSIDC sea ice concentration charts
* Bin2GeoTiff -- converting binary NSIDC maps to GeoTIFF
* CreateSeaIceFrequencyMap -- create SeaIceFrequency map
* CreateMaxMinIce -- create min/max ice maps
* EPSG3411_2_EPSG3575 -- reproject raster from EPSG:3411 to EPSG:3575
* ReprojectShapefile -- reproject shapefiles from EPSG:3411 to EPSG:3575
Documentation before each function and at https://github.com/npolar/RemoteSensing/wiki/Sea-Ice-Frequency
"""

import struct, numpy, gdal, gdalconst, glob, os, osr
import shutil, sys, datetime


def AddMissingDays(year, month, infilepath):
    '''
        Replaces missing days with files from previous day
    '''
    
    #http://pymotw.com/2/datetime/
    #http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    d1 =  datetime.date(year, month, 1)
    if month != 12:
        d2 =  datetime.date(year, month +1 , 1)
    elif month == 12:
        d2 =  datetime.date(year+1, 1 , 1)
        
    diff = datetime.timedelta(days=1)
    
    #date3 is working date to be looped through  -- set to start date   
    d3 = d1
    
    print "REPLACE MISSING FILES FOR ", year
    
    
    while d3 != d2:
        # Create searchstring for file to be checked if it exists
        day = d3.day
        
        checkfile = infilepath + "nt_" + d3.strftime('%Y%m%d') + "*"
        
        # Check if that file exists
        checkfilelist = glob.glob(checkfile)
        
        # If that file does not exist, replace it with previous day file
        # check 1-3 previous days, if not exist, take following day
        # Needed because for first of monty, the 31 of previous month not available
        # as it is programmed now
        if checkfilelist == []:    
            for i in (-1, -2, -3, 1, 2):
                newdate = d3 + datetime.timedelta(days=i)
                print newdate
                replacingfile = infilepath + "nt_" + newdate.strftime('%Y%m%d') + "*"
                
                replacingfilelist = glob.glob(replacingfile)
                print replacingfilelist
                if replacingfilelist != []:
                    break
            
                        
            try:
                pathname, filename = os.path.split(replacingfilelist[0])
            except:
                d3 = (d3 + diff) 
                continue
            if day < 10:
                missingfile = pathname + "//" + filename[0:9] + "0" + str(day) + filename[11:]
            else:
                missingfile = pathname + "//" + filename[0:9] +  str(day) + filename[11:]
            print "Missing ", missingfile 
            print "replaced with ", replacingfilelist[0]
            
            # In 1987, 14 days are missing, these are not replaced, shutil fails here
            try:
                shutil.copy(replacingfilelist[0], missingfile)
            except:
                d3 = (d3 + diff) 
                continue
            
        d3 = (d3 + diff)    


def EPSG3411_2_EPSG3575(infile):
    '''
    reprojects the infile from NSIDC 3411 to EPSG 3575
    outputfile has 25km resolution
    '''
    
    (infilepath, infilename) = os.path.split(infile)
    (infileshortname, extension) = os.path.splitext(infilename)
    outdirectory = infilepath + '//EPSG3575//'
    if not os.path.exists(outdirectory):
        os.makedirs(outdirectory)
    outfile =  outdirectory + infileshortname + '_EPSG3575.tif'
    print ' Reproject ', infile, ' to ', outfile 
    os.system('gdalwarp -s_srs EPSG:3411 -tr 25000 -25000 -t_srs EPSG:3575 -of GTiff ' + infile + ' ' + outfile)
    
def ReprojectShapefile(infile, inproj = "EPSG:3411", outproj = "EPSG:3575"):
    '''
    Reprojects the shapefile given in infile
    
    inproj and outproj in format "EPSG:3575", for the filename the ":" is 
    removed in the function
    
    Assumes existence of folder as "EPSG3575" or "EPSG32633" or...
    '''
    
    #Define outputfile name
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    
    reprshapepath = infilepath + '//' + outproj[0:4] + outproj[5:9]
    reprshapeshortname = infileshortname + '_' + outproj[0:4] + outproj[5:9]
    reprshapefile = reprshapepath + '//'+ reprshapeshortname + extension
    
    #Reproject using ogr commandline
    print 'Reproject Shapefile ', infile    
    os.system('ogr2ogr -s_srs ' + inproj + ' -t_srs ' + outproj + ' '  + reprshapefile + ' ' + infile )
    print 'Done Reproject'

    return reprshapefile    

def Bin2GeoTiff(infile,outfilepath ):
    '''
        This function takes the NSIDC charts, being a flat binary string, and converts them to GeoTiff. Some details here:
        http://geoinformaticstutorial.blogspot.no/2014/02/reading-binary-data-nsidc-sea-ice.html
        Info on the ice concentration charts: http://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html 
        Info on the map projection: http://nsidc.org/data/polar_stereo/ps_grids.html
        The GeoTiff files are map projected to EPSG:3411, being the NSIDC-specific projection.
        There also is produced a GeoTiff reprojected to EPSG:3575 which is the NP-standard for Barents/Fram-Strait.
        Details on how to map project are found here:
        http://geoinformaticstutorial.blogspot.no/2014/03/geocoding-nsidc-sea-ice-concentration.html
        
    '''
    
    #Define file names 
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = outfilepath + infileshortname + '.tif'
    #Dimensions from https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    height = 448
    width = 304
    
    #####    
    # READ FLAT BINARY INTO ARRAY
    #####
    #for this code on how to read flat binary string, inspiration found at https://stevendkay.wordpress.com/category/python/
    icefile = open(infile, "rb")
    contents = icefile.read()
    icefile.close()
    
    # unpack binary data into a flat tuple z
    #offset and width/height from https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    s="%dB" % (int(width*height),)
    z=struct.unpack_from(s, contents, offset = 300) 
    nsidc = numpy.array(z).reshape((448,304))
    
    ########
    #WRITE THE ARRAY TO GEOTIFF
    ########
    driver = gdal.GetDriverByName("GTiff")
    outraster = driver.Create(outfile,  width, height,1, gdal.GDT_Int16 )
    if outraster is None: 
        print 'Could not create '
        return
    
    #set geotransform, values from https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    geotransform = (-3850000.0, 25000.0 ,0.0 ,5850000.0, 0.0, -25000.0)
    outraster.SetGeoTransform(geotransform)
    outband = outraster.GetRasterBand(1)
    #Write to file     
    outband.WriteArray(nsidc)
    
    spatialRef = osr.SpatialReference()
    #spatialRef.ImportFromEPSG(3411)  --> this one does for some reason NOT work, but using proj4 does
    spatialRef.ImportFromProj4('+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 +x_0=0 +y_0=0 +a=6378273 +b=6356889.449 +units=m +no_defs')
    outraster.SetProjection(spatialRef.ExportToWkt() )
    outband.FlushCache()
    
    #Clear arrays and close files
    outband = None
    outraster = None
    nsidc = None
    
    #####
    #REPROJECT GEOTIFF TO EPSG3575
    #####
    EPSG3411_2_EPSG3575(outfile)
    
    
def CreateSeaIceFrequencyMap(inpath, outfilepath, max_ice, min_ice, landmask_raster):
    '''
    Creates map showing percentage ice coverage over a given period
    This function creates the sea ice frequency charts. 
    The function loops through each concentration map, if the value is larger
    than 38 = 15.2%, the value of "100.0 / NumberOfDays" is added --> if there 
    is ice every single day, that pixel will be "100"
    Output is available both as EPSG:3411 and EPSG:3575    
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    # filelist is all GeoTIFF files created in outfilepath
    filelist = glob.glob(outfilepath + 'nt*.tif')
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    
    
    firstfilename = filelist[0]
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = inpath + 'icechart_seaicefrequencymap' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.tif'
    
    ########
    # CREATE OUTPUT FILE AS COPY FROM ONE ICECHART
    ########
    
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
    
    #######
    # CALCULATE SEA ICE FREQUENCY RASTER
    #######
    
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
        
        #Array calculation and burn in land values on top
        outarray = numpy.where( (iceraster >=  38), (outarray + ( 100.0 / NumberOfDays ) ) , outarray)
        outarray = numpy.where( (iceraster ==   251), 251 , outarray)
        outarray = numpy.where( (iceraster ==   252), 252 , outarray)
        outarray = numpy.where( (iceraster ==   253), 253 , outarray)
        outarray = numpy.where( (iceraster ==   254), 254 , outarray)
        outarray = numpy.where( (iceraster ==   255), 255 , outarray)
               
        #Clear iceraster for next loop -- just in case
        iceraster = None
        

    # The polar hole has different sizes in the earlier years
    # This results in the line above in %-values larger than 100
    # so setting these to 251 gives again the maximum polar hole
    outarray = numpy.where( (outarray >   255), 251 , outarray)
    
    ######
    # Filter noise areas
    ######

    #Filter with maximum map since sea ice frequency map has noise values just as max map.
    #FUNCTION CreateMaxMinIce  HAS TO BE RUN BEFORE CreateIcePercistanceMap
    max_chart = gdal.Open(max_ice, gdalconst.GA_ReadOnly)
    max_chartraster = max_chart.ReadAsArray()
    landmask = gdal.Open(landmask_raster, gdalconst.GA_ReadOnly)
    landraster = landmask.ReadAsArray()  
    outarray = numpy.where(max_chartraster == 1, outarray, 0)
    # The polar hole is not in the landmask but only in outarray!!
    outarray = numpy.where( (outarray ==   251), 251 , outarray)
    # The other values are in the landraster;
    outarray = numpy.where( (landraster ==   252), 252 , outarray)
    outarray = numpy.where( (landraster ==   253), 253 , outarray)
    outarray = numpy.where( (landraster ==   254), 254 , outarray)
    outarray = numpy.where( (landraster ==   255), 255 , outarray)
    
    outband = outraster.GetRasterBand(1)   
    outband.WriteArray(outarray)
    outband.FlushCache()
       
    #Clear arrays and close files
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    
    #####
    #REPROJECT GEOTIFF TO EPSG3575
    #####
    EPSG3411_2_EPSG3575(outfile)
    
    return outfile
    print 'Done Creating Sea Ice Frequency Map'
    
def CreateMaxMinIce(inpath, outfilepath, landmask_raster, coastalerrormask_raster, oceanmask_buffer5, NSIDC_balticmask ):   
    ''' 
         Creates maximum and minimum ice map, GeoTIFF and shapefile
         maximum = at least one day ice at this pixel
         minimum = every day ice at this pixel
         In addition a file simply giving the number of days with ice
         
         The poly shapefile has all features as polygon, the line shapefile
         only the max or min ice edge
    
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    # filelist is all GeoTIFF files created in outfilepath
    filelist = glob.glob(outfilepath + 'nt*.tif')
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    
    #Files are all the same properties, so take first one to get info
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    
    outfile =  inpath + 'icechart_NumberOfDays' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.tif'
    outfilemax = inpath + 'icechart_maximum' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.tif'
    outfilemin = inpath + 'icechart_minimum' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.tif'
    
    outshape_polymax = inpath + 'icechart_poly_maximum' + os.path.split(filelist[0])[1][3:9]+ '_' + os.path.split(filelist[-1])[1][3:9] + '.shp'
    outshape_polymin = inpath + 'icechart_poly_minimum' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.shp'
    outshape_linemax = inpath + 'icechart_line_maximum' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.shp'
    outshape_linemin = inpath + 'icechart_line_minimum' + os.path.split(filelist[0])[1][3:9] + '_' + os.path.split(filelist[-1])[1][3:9] + '.shp'
    
    #Temporary shapefile, all subfiles specified so that they can be removed later
    #Many because gdal commands expect existing files
    outshape_tempmax = inpath + 'icechart_tempmax.shp'
    outshape_tempmax2 = inpath + 'icechart_tempmax.dbf'
    outshape_tempmax3 = inpath + 'icechart_tempmax.prj'
    outshape_tempmax4 = inpath + 'icechart_tempmax.shx'
    outshape_tempmin = inpath + 'icechart_tempmin.shp'
    outshape_tempmin2 = inpath + 'icechart_tempmin.dbf'
    outshape_tempmin3 = inpath + 'icechart_tempmin.prj'
    outshape_tempmin4 = inpath + 'icechart_tempmin.shx'
    
    outshape_temp2max = inpath + 'icechart_temp2max.shp'
    outshape_temp2max2 = inpath + 'icechart_temp2max.dbf'
    outshape_temp2max3 = inpath + 'icechart_temp2max.prj'
    outshape_temp2max4 = inpath + 'icechart_temp2max.shx'
    outshape_temp2min = inpath + 'icechart_temp2min.shp'
    outshape_temp2min2 = inpath + 'icechart_temp2min.dbf'
    outshape_temp2min3 = inpath + 'icechart_temp2min.prj'
    outshape_temp2min4 = inpath + 'icechart_temp2min.shx'
    
    outshape_temp3max = inpath + 'icechart_temp3max.shp'
    outshape_temp3max2 = inpath + 'icechart_temp3max.dbf'
    outshape_temp3max3 = inpath + 'icechart_temp3max.prj'
    outshape_temp3max4 = inpath + 'icechart_temp3max.shx'
    outshape_temp3min = inpath + 'icechart_temp3min.shp'
    outshape_temp3min2 = inpath + 'icechart_temp3min.dbf'
    outshape_temp3min3 = inpath + 'icechart_temp3min.prj'
    outshape_temp3min4 = inpath + 'icechart_temp3min.shx'
   
    ########
    # CREATE NUMBER OF DAYS RASTER FILE AS COPY FROM ICE FILE
    ########    
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
    
    #######
    # CALCULATE NUMBER OF DAYS RASTER = NUMBER SAYS HOW MANY DAYS ICE IN PIXEL
    #######
    #Loop through all files to do calculation
    for infile in filelist:
        
        (infilepath, infilename) = os.path.split(infile)
        print 'Processing ', infilename
        
        #open the IceChart
        icechart = gdal.Open(infile, gdalconst.GA_ReadOnly)
        if infile is None:
            print 'Could not open ', infilename
            return
        
        #Read input raster into array
        iceraster = icechart.ReadAsArray()
        
        #Array calculation -- if ice > 15% count additional day, otherwise keep value
        outarray = numpy.where( (iceraster >=  38), outarray + 1 , outarray)
                       
        #Clear iceraster for next loop -- just in case
        iceraster = None
    
    
    
    
    #outarray contains now NumberOfDay with ice -- burn in landmask
    landmask = gdal.Open(landmask_raster , gdalconst.GA_ReadOnly)
    landraster = landmask.ReadAsArray()
    outarray = numpy.where( (landraster == 251), 251, outarray)
    outarray = numpy.where( (landraster == 252), 252, outarray)
    outarray = numpy.where( (landraster == 253), 253, outarray)
    outarray = numpy.where( (landraster == 254), 254, outarray)
    outarray = numpy.where( (landraster == 255), 255, outarray)
    
    #######
    # CALCULATE MAXIMUM RASTER
    #######
    # Where never was ice, set map to 0, elsewhere to 1, i.e. at least one day ice
    # Using landraster again -- otherwise if NumberOfDay mask by chance 252, it is masked out
    outarraymax = numpy.where( (outarray == 0), 0, 1 )
    outarraymax = numpy.where( (landraster ==   251), 251 , outarraymax)
    outarraymax = numpy.where( (landraster ==   252), 252 , outarraymax)
    outarraymax = numpy.where( (landraster ==   253), 253 , outarraymax)
    outarraymax = numpy.where( (landraster ==   254), 254 , outarraymax)
    outarraymax = numpy.where( (landraster ==   255), 255 , outarraymax)
    
    #######
    # CALCULATE MINIMUM RASTER
    #######
    # Where every day was ice, set to 1, otherwise to 0
    # Keep in mind: Problems may arise when one value is missing (bad file)
    # such that value is just one or two less than NumberofDays
    outarraymin = numpy.where( (outarray == NumberOfDays), 1, 0 )
    outarraymin = numpy.where( (landraster ==   251), 251 , outarraymin)
    outarraymin = numpy.where( (landraster ==   252), 252 , outarraymin)
    outarraymin = numpy.where( (landraster ==   253), 253 , outarraymin)
    outarraymin = numpy.where( (landraster ==   254), 254 , outarraymin)
    outarraymin = numpy.where( (landraster ==   255), 255 , outarraymin)
    
        
    #get the bands 
    outband = outraster.GetRasterBand(1)    
    outbandmax = outrastermax.GetRasterBand(1)
    outbandmin = outrastermin.GetRasterBand(1)
    
    
    #Write all arrays to file
    
    outband.WriteArray(outarray)
    outband.FlushCache()    
    
    outbandmax.WriteArray(outarraymax)
    outbandmax.FlushCache()
    
    outbandmin.WriteArray(outarraymin)
    outbandmin.FlushCache()
    
    ##########
    # FILTER NOISE IN MINIMUM ARRAY / RASTER
    #########
    # the sieve filter takes out singular "islands" of pixels
    srcband = outbandmin
    dstband = outbandmin    
    maskband = None
    print "Apply SieveFilter on ", outfilemin
    gdal.SieveFilter( srcband, maskband, dstband,threshold = 3, connectedness = 4  )
    #load outbandmin once more and burn landmask again since sieve influences coastline
    outarraymin = outrastermin.ReadAsArray()
    outarraymin = numpy.where( (landraster ==   251), 251 , outarraymin)
    outarraymin = numpy.where( (landraster ==   252), 252 , outarraymin)
    outarraymin = numpy.where( (landraster ==   253), 253 , outarraymin)
    outarraymin = numpy.where( (landraster ==   254), 254 , outarraymin)
    outarraymin = numpy.where( (landraster ==   255), 255 , outarraymin)
    outbandmin = outrastermin.GetRasterBand(1)    
    outbandmin.WriteArray(outarraymin)
    outbandmin.FlushCache()
    
    ##########
    # FILTER NOISE IN MINIMUM ARRAY / RASTER
    #########    
    # the sieve filter takes out singular "islands" of pixels
    srcband = outbandmax
    dstband = outbandmax    
    maskband = None
    print "Apply SieveFilter one ", outrastermax
    gdal.SieveFilter( srcband, maskband, dstband,threshold = 3, connectedness = 4  )
    #load outbandmin once more and burn landmask again since sieve influences coastline
    outarraymax = outrastermax.ReadAsArray()
    outarraymax = numpy.where( (landraster ==   251), 251 , outarraymax)
    outarraymax = numpy.where( (landraster ==   252), 252 , outarraymax)
    outarraymax = numpy.where( (landraster ==   253), 253 , outarraymax)
    outarraymax = numpy.where( (landraster ==   254), 254 , outarraymax)
    outarraymin = numpy.where( (landraster ==   255), 255 , outarraymin)
    outbandmax = outrastermax.GetRasterBand(1)    
    outbandmax.WriteArray(outarraymax)
    outbandmax.FlushCache()
    
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
    landraster = None   
    landmask = None     
    
    ###################
    # CONVERT THE RASTERS CREATED ABOVE TO SHAPEFILES
    ###################

    # conversion to shape    
    print '\n Convert ', outfilemax, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfilemax + ' -f "ESRI Shapefile" ' + outshape_tempmax )
    print '\n Convert ', outfilemin, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfilemin + ' -f "ESRI Shapefile" ' + outshape_tempmin ) 
    
    # FILTERING MAX / MIN    
    # Get the large polygon only, this removes mistaken areas at coast and noise. KEEP IN MIND: CHECK VALUE IF TOO BIG SUCH THAT REAL AREAS ARE REMOVED
    # Do this only for polymax -- the minimum would remove real areas, patches like East of Svalbard. Polymin selects here all polygons basically
    print "Select large polygon, ignoring the small ones"
    os.system('ogr2ogr -progress '+ outshape_polymax + ' ' + outshape_tempmax + ' -sql "SELECT *, OGR_GEOM_AREA FROM icechart_tempmax WHERE DN=1 AND OGR_GEOM_AREA > 10000000000.0"')
    os.system('ogr2ogr -progress '+ outshape_polymin + ' ' + outshape_tempmin + ' -sql "SELECT *, OGR_GEOM_AREA FROM icechart_tempmin WHERE DN=1 AND OGR_GEOM_AREA > 10.0"')
    
    # Convert polygon to lines
    print 'Convert ice edge map to Linestring Map'
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_temp2max + ' ' + outshape_polymax)
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_temp2min + ' ' + outshape_polymin)
    
    # Remove coast line from ice edge by clipping with coastline
    # Prerequisite: Create NISDC coast line mask ( ogr2ogr -progress C:\Users\max\Desktop\NSIDC_oceanmask.shp C:\Users \max\Desktop\temp.shp
    # -sql "SELECT *, OGR_GEOM_AREA FROM temp WHERE DN<250 )
    # use "dissolve" to get ocean only with one value and the run buffer -5000m such that coast line does not match but overlaps ice polygon
    # because only then it is clipped
    os.system('ogr2ogr -progress -clipsrc ' + oceanmask_buffer5 + ' ' +  outshape_linemax + ' ' + outshape_temp2max)
    os.system('ogr2ogr -progress -clipsrc ' + oceanmask_buffer5 + ' ' +  outshape_linemin + ' ' + outshape_temp2min)
    
    #Cleaning up temporary files 
    os.remove(outshape_tempmax)
    os.remove(outshape_tempmax2)
    os.remove(outshape_tempmax3)
    os.remove(outshape_tempmax4)
    os.remove(outshape_tempmin)
    os.remove(outshape_tempmin2)
    os.remove(outshape_tempmin3)
    os.remove(outshape_tempmin4)
    os.remove(outshape_temp2max)
    os.remove(outshape_temp2max2)
    os.remove(outshape_temp2max3)
    os.remove(outshape_temp2max4)
    os.remove(outshape_temp2min)
    os.remove(outshape_temp2min2)
    os.remove(outshape_temp2min3)
    os.remove(outshape_temp2min4)
    
    ##########
    # ADDING BALTIC SEA
    ##########
    
    #Treated separatedly since close to coast and therefore sensitive to coastal errors
    print '\n Add Baltic Sea Ice.'
    
    #polygonice only Baltic Sea
    os.system('gdal_polygonize.py ' + outfilemax + ' -mask ' + NSIDC_balticmask + ' -f "ESRI Shapefile" ' + outshape_tempmax )    
    os.system('gdal_polygonize.py ' + outfilemin + ' -mask ' + NSIDC_balticmask + ' -f "ESRI Shapefile" ' + outshape_tempmin )    
        
    # Add Baltic to existing polymax and polymin 
    os.system('ogr2ogr -update -append ' + outshape_polymax + ' ' +   outshape_tempmax +  ' -sql "SELECT *, OGR_GEOM_AREA FROM icechart_tempmax WHERE DN=1 AND OGR_GEOM_AREA > 20000000000.0"')
    os.system('ogr2ogr -update -append ' + outshape_polymin + ' ' +   outshape_tempmin +  ' -sql "SELECT *, OGR_GEOM_AREA FROM icechart_tempmin WHERE DN=1"')
    
    # Convert polygon to lines
    print 'Convert ice edge map to Linestring Map'
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_temp2max + ' ' + outshape_polymax)
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_temp2min + ' ' + outshape_polymin)
    
    #clip coast as above
    os.system('ogr2ogr -progress -clipsrc ' + oceanmask_buffer5 + ' ' +  outshape_temp3max + ' ' + outshape_temp2max)
    os.system('ogr2ogr -progress -clipsrc ' + oceanmask_buffer5 + ' ' +  outshape_temp3min + ' ' + outshape_temp2min)
    
    # Add Baltic line to existing min/max line
    os.system('ogr2ogr -update -append ' + outshape_linemax + ' ' +   outshape_temp3max )
    os.system('ogr2ogr -update -append ' + outshape_linemin + ' ' +   outshape_temp3min )
    

    #########
    # REDO MAX MIN RASTER
    #########    
    
    #The polygon and line files are now cleaned for noise since only large polygon
    # was chosen for minimum polygon
    # Re-rasterize to tif, such that the tiff is also cleaned

    # gdal rasterize should be able to overwrite / create new a file. Since this does not work, I set the
    # existing one to zero and rasterize the polgon into it
    print 'Rerasterize max and min GeoTIFF'
    outarray = gdal.Open( outfilemax, gdalconst.GA_Update)
    outarraymax = outarray.ReadAsArray()
    outarraymax = numpy.zeros((rows, cols), numpy.float) 
    outbandmax = outarray.GetRasterBand(1)    
    outbandmax.WriteArray(outarraymax)
    outbandmax.FlushCache()
    outarray = None
    
    #Rasterize polygon
    
    os.system('gdal_rasterize -burn 1 ' + outshape_polymax + ' ' + outfilemax )
    # OPen raster and burn in landmask again -- is not contained in polygon
    outarray = gdal.Open( outfilemax, gdalconst.GA_Update)
    outarraymax = outarray.ReadAsArray()
    landmask = gdal.Open(landmask_raster, gdalconst.GA_ReadOnly)
    landraster = landmask.ReadAsArray()
    outarraymax = numpy.where( (landraster ==   251), 251 , outarraymax)
    outarraymax = numpy.where( (landraster ==   252), 252 , outarraymax)
    outarraymax = numpy.where( (landraster ==   253), 253 , outarraymax)
    outarraymax = numpy.where( (landraster ==   254), 254 , outarraymax)
    outarraymax = numpy.where( (landraster ==   255), 255 , outarraymax)
    outbandmax = outarray.GetRasterBand(1)    
    outbandmax.WriteArray(outarraymax)
    outbandmax.FlushCache()
    outarray = None
    landmask = None
    landraster = None
    
    #Reraster the min image
    outarray = gdal.Open( outfilemin, gdalconst.GA_Update)
    outarraymin = outarray.ReadAsArray()
    outarraymin = numpy.zeros((rows, cols), numpy.float) 
    outbandmin = outarray.GetRasterBand(1)    
    outbandmin.WriteArray(outarraymin)
    outbandmin.FlushCache()
    outarray = None
    #Rasterize polygon
    os.system('gdal_rasterize -burn 1 ' + outshape_polymin + ' ' + outfilemin )
    # OPen raster and burn in landmask again -- is not contained in polygon
    outarray = gdal.Open( outfilemin, gdalconst.GA_Update)
    outarraymin = outarray.ReadAsArray()
    landmask = gdal.Open(landmask_raster, gdalconst.GA_ReadOnly)
    landraster = landmask.ReadAsArray()
    outarraymin = numpy.where( (landraster ==   251), 251 , outarraymin)
    outarraymin = numpy.where( (landraster ==   252), 252 , outarraymin)
    outarraymin = numpy.where( (landraster ==   253), 253 , outarraymin)
    outarraymin = numpy.where( (landraster ==   254), 254 , outarraymin)
    outarraymin = numpy.where( (landraster ==   255), 255 , outarraymin)
    outbandmin = outarray.GetRasterBand(1)    
    outbandmin.WriteArray(outarraymin)
    outbandmin.FlushCache()
    landmask = None
    landraster = None
        
    #Cleaning up temporary files 
    os.remove(outshape_tempmax)
    os.remove(outshape_tempmax2)
    os.remove(outshape_tempmax3)
    os.remove(outshape_tempmax4)
    os.remove(outshape_tempmin)
    os.remove(outshape_tempmin2)
    os.remove(outshape_tempmin3)
    os.remove(outshape_tempmin4)
    os.remove(outshape_temp2max)
    os.remove(outshape_temp2max2)
    os.remove(outshape_temp2max3)
    os.remove(outshape_temp2max4)
    os.remove(outshape_temp2min)
    os.remove(outshape_temp2min2)
    os.remove(outshape_temp2min3)
    os.remove(outshape_temp2min4)
    os.remove(outshape_temp3max)
    os.remove(outshape_temp3max2)
    os.remove(outshape_temp3max3)
    os.remove(outshape_temp3max4)
    os.remove(outshape_temp3min)
    os.remove(outshape_temp3min2)
    os.remove(outshape_temp3min3)
    os.remove(outshape_temp3min4)
    
    
    #Reproject to EPSG:3575
    ReprojectShapefile(outshape_polymax)
    ReprojectShapefile(outshape_polymin)
    ReprojectShapefile(outshape_linemax)
    ReprojectShapefile(outshape_linemin)
  
    #reproject to EPSG3575
    EPSG3411_2_EPSG3575(outfilemax)        
    EPSG3411_2_EPSG3575(outfilemin) 
    EPSG3411_2_EPSG3575(outfile) 
    print    
    print 'Done Creating Max/Min Maps'        
    return outfilemax, outfilemin
    
def FilterCoastalAreas(outfilepath, landmask_raster, coastalerrormask_raster):
    '''
    Problem: Along Coastal Areas, the land/ocean boundary appears as ice values
    Solution: Mask for problematice areas, but consider as ice if value remains
    for a number of consecutive days -- filters singular error pixels
    
    Loop through all NSIDC ice concentration areas
    In the coastal areas (defined by NSIDC_coastalerrormask_raster.tif) ice concentration
    above 15% is only considered if ice is present three days before and after the date
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    filelist = glob.glob(outfilepath + 'nt*.tif')
    
    
    #Files are all the same properties, so take first one to get info
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    

    
    #Open Coastal Mask into array
    #THe coastal mask defines error areas -- value 1 for coast, value 2 for Baltic and value 3 for never-ice areas.
    coastalerrormask = gdal.Open(coastalerrormask_raster, gdalconst.GA_ReadOnly)
    coastalerrormaskarray = coastalerrormask.ReadAsArray()
    
    #Create file receiving the ice mask
    #get image size
    rows = coastalerrormask.RasterYSize
    cols = coastalerrormask.RasterXSize   
    
    coastalicemaskraster = numpy.zeros((rows, cols), numpy.float) 
    #Loop through all files to do calculation
    for infile in filelist:
        #Find present data    
        #Find present data
        #If NSIDC changes filenames, this may need adjustment, happened in 2016
        #(os.path.split(infile)[1] is the filename without path, then split date
        presentyear = int(os.path.split(infile)[1][3:7])
        presentmonth = int(os.path.split(infile)[1][7:9])
        presentday = int(os.path.split(infile)[1][9:11])
        
        presentdate =  datetime.date(presentyear, presentmonth, presentday) 
        
        ########################
        # COASTAL ERROR FOR COAST
        ########################        
        # ADJUST HOW MANY DAYS PLUS AND MINUS THE PRESENT DATE YOU WANT
        dayrange = 2
        
        #Let ice value in coastal zone persist if there was ice the days around it
        presentdayfilename = outfilepath + "nt_" + presentdate.strftime('%Y%m%d') +  str(os.path.split(infile)[1])[11:]
        presentdayfile = gdal.Open( presentdayfilename, gdalconst.GA_Update)
        presentdayraster = presentdayfile.ReadAsArray()
        print "coastal error mask for ", presentdayfilename
        #Reset coastalicemaskraster to zero
        coastalicemaskraster = numpy.zeros((rows, cols), numpy.float) 
        #Loop through the files around present day and determine how many days there is ice in coastal zone    
        for i in range(-dayrange, dayrange +1):
            diff = datetime.timedelta(days=i)
            diffdate = presentdate + diff
            checkfilename = outfilepath + "nt_" + diffdate.strftime('%Y%m%d') +  str(os.path.split(infile)[1])[11:]
            
            if os.path.isfile(checkfilename):
                checkfile = gdal.Open(checkfilename, gdalconst.GA_ReadOnly)
                #Read input raster into array
                checkfileraster = checkfile.ReadAsArray()
                coastalicemaskraster = numpy.where( (coastalerrormaskarray == 1) & (checkfileraster >= 38), coastalicemaskraster + 1 , coastalicemaskraster )
                
                
            else:
                #If previous day files do not exist, take present day one -- otherwise it does not add up with number of Days                
                coastalicemaskraster = numpy.where( (coastalerrormaskarray == 1) & (presentdayraster >= 38), coastalicemaskraster + 1 , coastalicemaskraster )
                
        

        
        presentdayraster = numpy.where( (coastalerrormaskarray == 1) & ( coastalicemaskraster < 5 ), 0, presentdayraster)
        ########################
        # COASTAL ERROR FOR DEFINITE NO ICE AREAS
        ########################       
        presentdayraster = numpy.where( (coastalerrormaskarray == 3), 0, presentdayraster)
        
        
        ########################
        # COASTAL ERROR FOR BALTIC
        ########################
        dayrange = 2
        #Reset coastalicemaskraster to zero
        coastalicemaskraster = numpy.zeros((rows, cols), numpy.float) 
        #Loop through the files around present day and determine how many days there is ice in coastal zone    
        for i in range(-dayrange, dayrange +1):
            diff = datetime.timedelta(days=i)
            diffdate = presentdate + diff
            checkfilename = outfilepath + "nt_" + diffdate.strftime('%Y%m%d') +  str(os.path.split(infile)[1])[11:]
            
            if os.path.isfile(checkfilename):
                checkfile = gdal.Open(checkfilename, gdalconst.GA_ReadOnly)
                #Read input raster into array
                checkfileraster = checkfile.ReadAsArray()
                
                coastalicemaskraster = numpy.where( (coastalerrormaskarray == 2) & (checkfileraster >= 38), coastalicemaskraster + 1 , coastalicemaskraster )
            else:
                #If previous day files do not exist, take present day one -- otherwise it does not add up with number of Days                
                
                coastalicemaskraster = numpy.where( (coastalerrormaskarray == 2) & (presentdayraster >= 38), coastalicemaskraster + 1 , coastalicemaskraster )
                
                
        

        # coastalicemaskraster < 5 or rather a value of 4 should be considered in future checks
        presentdayraster = numpy.where( (coastalerrormaskarray == 2) & (coastalicemaskraster < 5 ), 0, presentdayraster)
                
        # outarray contains filtered values -- burn in landmask
        landmask = gdal.Open(landmask_raster, gdalconst.GA_ReadOnly)
        landraster = landmask.ReadAsArray()
        presentdayraster = numpy.where( (landraster == 251), 251, presentdayraster)
        presentdayraster = numpy.where( (landraster == 252), 252, presentdayraster)
        presentdayraster = numpy.where( (landraster == 253), 253, presentdayraster)
        presentdayraster = numpy.where( (landraster == 254), 254, presentdayraster)
        presentdayraster = numpy.where( (landraster == 255), 255, presentdayraster)        
        
        presentdayfileband = presentdayfile.GetRasterBand(1)
            
        presentdayfileband.WriteArray(presentdayraster)
        presentdayfileband.FlushCache()
    
    
    
        
def FilterConsecDays(outfilepath, landmask_raster, coastalerrormask_raster):
    '''
    Problem: Singular pixels claiming to be ice
    Solution: Consider as ice if value has ice "dayrange"-number
    before of after a given day-- filters singular error pixels
    
    Loop through all NSIDC ice concentration areas
    In the coastal areas (defined by NSIDC_coastalerrormask_raster.tif) ice concentration
    above 15% is only considered if ice is present three days before and after the date
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    filelist = glob.glob(outfilepath + 'nt*.tif')
    
    
    #Files are all the same properties, so take first one to get info
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    

    
    #Open Coastal Mask into array
    coastalerrormask = gdal.Open(coastalerrormask_raster, gdalconst.GA_ReadOnly)
    coastalerrormaskarray = coastalerrormask.ReadAsArray()
    
    #Create file receiving the ice mask
    #get image size
    rows = coastalerrormask.RasterYSize
    cols = coastalerrormask.RasterXSize   
    
    coastalicemaskraster = numpy.zeros((rows, cols), numpy.float) 
        #Loop through all files to do calculation
    for infile in filelist:
        #Find present data
        #If NSIDC changes filenames, this may need adjustment, happened in 2016
        #(os.path.split(infile)[1] is the filename without path, then split date
        presentyear = int(os.path.split(infile)[1][3:7])
        presentmonth = int(os.path.split(infile)[1][7:9])
        presentday = int(os.path.split(infile)[1][9:11])
        
        presentdate =  datetime.date(presentyear, presentmonth, presentday) 
        
        # ADJUST HOW MANY DAYS PLUS AND MINUS THE PRESENT DATE YOU WANT
        dayrange = 1
        
        #Let ice value in coastal zone persist if there was ice the days around it
        presentdayfilename = outfilepath + "nt_" + presentdate.strftime('%Y%m%d') +  str(os.path.split(infile)[1])[11:]
        presentdayfile = gdal.Open( presentdayfilename, gdalconst.GA_Update)
        presentdayraster = presentdayfile.ReadAsArray()
        print "Filter consec days for ", presentdayfilename
        
        #Reset coastalicemaskraster to zero
        coastalicemaskraster = numpy.zeros((rows, cols), numpy.float) 
        #Loop through the files around present day and determine how many days there is ice in coastal zone    
        for i in range(-dayrange, dayrange +1):
            diff = datetime.timedelta(days=i)
            diffdate = presentdate + diff
            checkfilename = outfilepath + "nt_" + diffdate.strftime('%Y%m%d') +  str(os.path.split(infile)[1])[11:]
            
            if os.path.isfile(checkfilename):
                checkfile = gdal.Open(checkfilename, gdalconst.GA_ReadOnly)
                #Read input raster into array
                checkfileraster = checkfile.ReadAsArray()
                
                coastalicemaskraster = numpy.where(  ((checkfileraster >= 38) & (presentdayraster >= 38)), coastalicemaskraster + 1 , coastalicemaskraster )
                
            else:
                #If previous day files do not exist, take present day one -- otherwise it does not add up with number of Days                
                coastalicemaskraster = numpy.where(  (presentdayraster >= 38), coastalicemaskraster + 1 , coastalicemaskraster )
                
                
                
                
        

        
        #Pixel is ice only if presentday is ice (see for loop) AND if a day before OR after is ice (from three days, two need to be ice)
        #This does not shorten or lengthen the ice season since only day before or after is needed
        presentdayraster = numpy.where( (coastalicemaskraster <= ((dayrange * 2)) ), 0, presentdayraster)
        #outarray contains now NumberOfDay with ice -- burn in landmask
        landmask = gdal.Open(landmask_raster, gdalconst.GA_ReadOnly)
        landraster = landmask.ReadAsArray()
        presentdayraster = numpy.where( (landraster == 251), 251, presentdayraster)
        presentdayraster = numpy.where( (landraster == 252), 252, presentdayraster)
        presentdayraster = numpy.where( (landraster == 253), 253, presentdayraster)
        presentdayraster = numpy.where( (landraster == 254), 254, presentdayraster)
        presentdayraster = numpy.where( (landraster == 255), 255, presentdayraster)        
        
        presentdayfileband = presentdayfile.GetRasterBand(1)
            
        presentdayfileband.WriteArray(presentdayraster)
        presentdayfileband.FlushCache()
    
    
    
        
        
                
        
    
    
        
     
##############################################################################

###   Core of Program follows here ###

##############################################################################


#############################
# SET PATH AND VARIABLES HERE
#############################

### Location of needed Raster Masks ###
### these files are located on \\berner\SeaIceRemoteSensing\Isfrekvens\landmasks
### the present paths below are mounted Ubuntu paths to this location

landmask_raster = '//mnt//seaiceremotesensing//Isfrekvens//landmasks//NSIDC_landmask_raster.tif'
coastalerrormask_raster = "//mnt//seaiceremotesensing//Isfrekvens//landmasks//NSIDC_coastalerrormask_raster.tif"
oceanmask_buffer5 = '//mnt//seaiceremotesensing//Isfrekvens//landmasks//NSIDC_oceanmask_buffer5.shp'
NSIDC_balticmask = '//mnt//seaiceremotesensing//Isfrekvens//landmasks//NSIDC_balticmask.tif'


#Get all files from given month
#Set this to the startyear and stopyear for your 30-year period (e.g. 1986-2015)
#Run once for each month 1-2
startyear = 1986
stopyear = 2015
month = 1                          #Values 1 to 12

# Set destinationpath where all results are supposed to be stored
destinationpath = '//mnt//seaiceremotesensing//Isfrekvens//Isfrekvens1986-2015//'


# Set path where NSIDC sea ice concentration is stored
nsidcpath = '//mnt//seaiceremotesensing//SSMI//IceConcentration//NASATEAM//final-gsfc//north//daily//'

##############################
# END OF VARIABLES TO BE SET
##############################




### Set outfilepath where 
monthDict={1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
outfilepath = destinationpath + monthDict[month] + '//'

if os.path.exists(outfilepath):
    answer = raw_input(outfilepath + " exists, delete and overwrite folder? [Y]es?")
    if answer.lower().startswith('y'):
        print "Overwriting " + outfilepath        
        shutil.rmtree(outfilepath)
        os.makedirs(outfilepath)
    else:
        print "Ending program"
        sys.exit()
        
elif not os.path.exists(outfilepath):
    os.makedirs(outfilepath)
    
#Create filelist including all files for the given month between startyear and stopyear inclusive
filelist = []
for year in range(startyear, (stopyear + 1)):
    foldername = nsidcpath + str(year) + '//'
    if month < 10: 
        file_searchstring = 'nt_' + str(year) + '0' + str(month) + '*.bin'
    else:
        file_searchstring = 'nt_' + str(year)  + str(month) + '*.bin'
    
    foldersearchstring = foldername + file_searchstring
    filelist.extend(glob.glob(foldersearchstring))


for icechart in filelist:
    #Convert NSIDC files to GeoTiff
    print'convert ', icechart
    Bin2GeoTiff(icechart, outfilepath)
    
# Fix January 1988
# 1-12 January 1988 data is missing
# Manually interpolated data is copied (linear interpolated between 31/12 and 13/1)
# If other unterpolation wanted, just replace all data in folder
if month == 1:
    list1988 = glob.glob("//mnt//seaiceremotesensing//Isfrekvens//interpolatedJanuar1988//nt*.tif")
    for file1988 in list1988:
        shutil.copy(file1988, outfilepath)


# Add missing days for 3411 as well as 3575 versions
for year in range(startyear, (stopyear + 1)):
    AddMissingDays(year,month, outfilepath)
    AddMissingDays(year,month, outfilepath + "EPSG3575//")



# Filter singular pixels
# THIS FILTER WAS DECIDED NOT TO BE USED
###FilterConsecDays(outfilepath, landmask_raster, coastalerrormask_raster)

#Filter erroneous pixels at coast line
FilterCoastalAreas(outfilepath, landmask_raster, coastalerrormask_raster)
    

#Create maximum and minimum extent map
#Max / Min must be done before sea ice frequency , since the latter is filtered with max-map
max_ice, min_ice = CreateMaxMinIce(outfilepath, outfilepath, landmask_raster, coastalerrormask_raster, oceanmask_buffer5, NSIDC_balticmask )

#Create the isfrekvens / ice frequency / ice persistence map
CreateSeaIceFrequencyMap(outfilepath, outfilepath, max_ice, min_ice, landmask_raster)

print 24*'#'
print "Done creating Ice Persistance Map"
print 24*'#'

