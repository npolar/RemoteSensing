# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 08:18:31 2014

@author: max
 
Creating ice persistency maps from NSIDC sea ice concentration charts

* Bin2GeoTiff -- converting binary NSIDC maps to GeoTIFF
* CreateIcePercistanceMap -- create ice persistence map
* CreateMaxMinIce -- create min/max ice maps
* EPSG3411_2_EPSG3575 -- reproject raster from EPSG:3411 to EPSG:3575
* ReprojectShapefile -- reproject shapefiles from EPSG:3411 to EPSG:3575

Documentation before each function and at https://github.com/npolar/RemoteSensing/wiki/Sea-Ice-Frequency

"""

import struct, numpy, gdal, gdalconst, glob, os, osr, datetime

def EPSG3411_2_EPSG3575(infile):
    '''
    reprojects the infile from NSIDC 3411 to EPSG 3575
    outputfiel has 25km resolution
    '''
    
    (infilepath, infilename) = os.path.split(infile)
    (infileshortname, extension) = os.path.splitext(infilename)
    outfile = infilepath + '\\EPSG3575\\' + infileshortname + '_EPSG3575.tif'
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
    
    reprshapepath = infilepath + '\\' + outproj[0:4] + outproj[5:9]
    reprshapeshortname = infileshortname + '_' + outproj[0:4] + outproj[5:9]
    reprshapefile = reprshapepath + '\\'+ reprshapeshortname + extension
    
    #Reproject using ogr commandline
    print 'Reproject Shapefile ', infile    
    os.system('ogr2ogr -s_srs ' + inproj + ' -t_srs ' + outproj + ' '  + reprshapefile + ' ' + infile )
    print 'Done Reproject'

    return reprshapefile    

def Bin2GeoTiff(infile,outfilepath ):
    '''
        This function takes the NSIDC charts, being a flat binary string, and converts them to GeoTiff. 
        This function takes the NSIDC charts, being a flat binary string, and converts them to GeoTiff. Some details here:
        http://geoinformaticstutorial.blogspot.no/2014/02/reading-binary-data-nsidc-sea-ice.html

        Info on the ice concentration charts: http://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html 
        Info on the map projection: http://nsidc.org/data/polar_stereo/ps_grids.html

        The GeoTiff files are map projected to EPSG:3411, being the NSIDC-specific projection.
        There also exists a GeoTiff reprojected to EPSG:3575 which is the NP-standard for Barents/Fram-Strait.
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
    
    geotransform = (-3850000.0, 25000.0 ,0.0 ,5850000.0, 0.0, -25000.0)
    outraster.SetGeoTransform(geotransform)
    outband = outraster.GetRasterBand(1)
    #Write to file     
    outband.WriteArray(nsidc)
    
    spatialRef = osr.SpatialReference()
    #spatialRef.ImportFromEPSG(3411)  --> this one does for some reason NOT work, but proj4 does
    spatialRef.ImportFromProj4('+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 +x_0=0 +y_0=0 +a=6378273 +b=6356889.449 +units=m +no_defs')
    outraster.SetProjection(spatialRef.ExportToWkt() )
    outband.FlushCache()
    
    #Clear arrays and close files
    outband = None
    outraster = None
    nsidc = None
    
    #reproject to EPSG3575
    EPSG3411_2_EPSG3575(outfile)
    
    
def CreateIcePercistanceMap(inpath, outfilepath):
    '''
    Creates map showing percentage ice coverage over a given period
    This function creates the ice persistence charts. 
    The function loops through each concentration map, if the value is larger
    than 38 = 15.2%, the value of "100.0 / NumberOfDays" is added --> if there 
    is ice every single day, that pixel will be "100"

    Output is available both as EPSG:3411 and EPSG:3575    
    '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    filelist = glob.glob(outfilepath + 'nt*.tif')
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    
    
    firstfilename = filelist[0]
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = inpath + 'icechart_persistencemap' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.tif'
    
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
        
    #coastalerrormask = gdal.Open("C:\\Users\\max\\Documents\\IcePersistency\\landmasks\\NSIDC_coastalerrormask_raster.tif", gdalconst.GA_ReadOnly)
    #coastalerrormaskarray = coastalerrormask.ReadAsArray()
    #outarray = numpy.where( (coastalerrormaskarray == 1) & (outarray <= ( NumberOfDays / 60.0)), 0.0 , outarray )
    
       
    outband.WriteArray(outarray)
    outband.FlushCache()
    
    outband = outraster.GetRasterBand(1)
    srcband = outband
    dstband = outband    
    maskband = None
    print "Apply SieveFilter one ", outraster
    #gdal.SieveFilter( srcband, maskband, dstband,threshold = 3, connectedness = 4  )
    
    #Clear arrays and close files
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    
    #reproject to EPSG3575
    EPSG3411_2_EPSG3575(outfile)
    
    return outfile
    print 'Done Creating Persistence Map'
    
def CreateMaxMinIce(inpath, outfilepath):   
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
    filelist = glob.glob(outfilepath + 'nt*.tif')
    
    #Determine Number of Days from available ice chart files
    NumberOfDays = len(filelist)
    
    #Files are all the same properties, so take first one to get info
    firstfilename = filelist[0]
    
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    
    outfile =  inpath + 'icechart_NumberOfDays' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.tif'
    outfilemax = inpath + 'icechart_maximum' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.tif'
    outfilemin = inpath + 'icechart_minimum' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.tif'
    
    outshape_polymax = inpath + 'icechart_poly_maximum' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.shp'
    outshape_polymin = inpath + 'icechart_poly_minimum' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.shp'
    outshape_linemax = inpath + 'icechart_line_maximum' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.shp'
    outshape_linemin = inpath + 'icechart_line_minimum' + filelist[0][-22:-16] + '_' + filelist[-1][-22:-16] + '.shp'
    
    #Temporary shapefile, all subfiles specified so that they can be removed later
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
        
        #Read input raster into array
        iceraster = icechart.ReadAsArray()
        
        #Array calculation with numpy -- much faster
        outarray = numpy.where( (iceraster >=  38), outarray + 1 , outarray)
                       
        #Clear iceraster for next loop -- just in case
        iceraster = None
    
    
    
    
    #outarray contains now NumberOfDay with ice -- burn in landmask
    landmask = gdal.Open('C:\\Users\\max\\Documents\\IcePersistency\\landmasks\\NSIDC_landmask_raster.tif', gdalconst.GA_ReadOnly)
    landraster = landmask.ReadAsArray()
    outarray = numpy.where( (landraster == 251), 251, outarray)
    outarray = numpy.where( (landraster == 252), 252, outarray)
    outarray = numpy.where( (landraster == 253), 253, outarray)
    outarray = numpy.where( (landraster == 254), 254, outarray)
    outarray = numpy.where( (landraster == 255), 255, outarray)
    
    #Error Areas at Coast
    #coastalerrormask = gdal.Open("C:\\Users\\max\\Documents\\IcePersistency\\landmasks\\NSIDC_coastalerrormask_raster.tif", gdalconst.GA_ReadOnly)
    #coastalerrormaskarray = coastalerrormask.ReadAsArray()
    #outarray = numpy.where( (coastalerrormaskarray == 1) & (outarray <= ( NumberOfDays / 60.0)), 0.0 , outarray )
    
    
    #Calculate the maximum-map from the NumberOfDays outarray
    #Using landraster again -- otherwise if NumberOfDay mask by chance 252, it is masked out
    outarraymax = numpy.where( (outarray == 0), 0, 1 )
    outarraymax = numpy.where( (landraster ==   251), 251 , outarraymax)
    outarraymax = numpy.where( (landraster ==   252), 252 , outarraymax)
    outarraymax = numpy.where( (landraster ==   253), 253 , outarraymax)
    outarraymax = numpy.where( (landraster ==   254), 254 , outarraymax)
    outarraymax = numpy.where( (landraster ==   255), 255 , outarraymax)
    
    #Calculate the minimum-map from the NumberOfDays outarray
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
    
    # Remove noise in outbandmin    
    srcband = outbandmin
    dstband = outbandmin    
    maskband = None
    print "Apply SieveFilter one ", outrastermin
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
    
    # Remove noise in outbandmax    
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
    
    ##### CONVERSION TO SHAPEFILE #######################    
    print '\n Convert ', outfilemax, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfilemax + ' -f "ESRI Shapefile" ' + outshape_tempmax )
    print '\n Convert ', outfilemin, ' to shapefile.'
    os.system('gdal_polygonize.py ' + outfilemin + ' -f "ESRI Shapefile" ' + outshape_tempmin ) 
    
    #Get the large polygon only, this removes mistaken areas at coast and noise. CHECK VALUE IF TOO BIG FOR SOME YEARS(?)
    print "Select large polygon, ignoring the small ones"
    os.system('ogr2ogr -progress '+ outshape_polymax + ' ' + outshape_tempmax + ' -sql "SELECT *, OGR_GEOM_AREA FROM icechart_tempmax WHERE DN=1 AND OGR_GEOM_AREA > 10000000000000.0"' )
    os.system('ogr2ogr -progress '+ outshape_polymin + ' ' + outshape_tempmin + ' -sql "SELECT *, OGR_GEOM_AREA FROM icechart_tempmin WHERE DN=1 AND OGR_GEOM_AREA > 10000000000000.0" ')
    
    # Convert polygon to lines
    print 'Convert ice edge map to Linestring Map'
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_temp2max + ' ' + outshape_polymax)
    os.system('ogr2ogr -progress -nlt LINESTRING -where "DN=1" ' + outshape_temp2min + ' ' + outshape_polymin)
    
    # Remove coast line from ice edge
    # Prerequisite: Create NISDC coast line mask ( ogr2ogr -progress C:\Users\max\Desktop\NSIDC_oceanmask.shp C:\Users \max\Desktop\temp.shp
    # -sql "SELECT *, OGR_GEOM_AREA FROM temp WHERE DN<250 )
    # use "dissolve" to get ocean only with one value and the run buffer -5000m such that coast line does not match ice polygon
    os.system('ogr2ogr -progress -clipsrc C:\Users\max\Documents\IcePersistency\landmasks\NSIDC_oceanmask_buffer5.shp '+  outshape_linemax + ' ' + outshape_temp2max)
    os.system('ogr2ogr -progress -clipsrc C:\Users\max\Documents\IcePersistency\landmasks\NSIDC_oceanmask_buffer5.shp '+  outshape_linemin + ' ' + outshape_temp2min)
    
       
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
    
def FilterCoastalAreas(outfilepath):
    '''
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
    coastalerrormask = gdal.Open("C:\\Users\\max\\Documents\\IcePersistency\\landmasks\\NSIDC_coastalerrormask_raster.tif", gdalconst.GA_ReadOnly)
    coastalerrormaskarray = coastalerrormask.ReadAsArray()
    
    #Create file receiving the ice mask
    #get image size
    rows = coastalerrormask.RasterYSize
    cols = coastalerrormask.RasterXSize   
    
    coastalicemaskraster = numpy.zeros((rows, cols), numpy.float) 
        #Loop through all files to do calculation
    for infile in filelist:
        #Find present data    
        presentyear = int(infile[-22:-18])
        presentmonth = int(infile[-18:-16])
        presentday = int(infile[-16:-14])
        
        presentdate =  datetime.date(presentyear, presentmonth, presentday) 
        
        # ADJUST HOW MANY DAYS PLUS AND MINUS THE PRESENT DATE YOU WANT
        dayrange = 2
        
        #Loop through the files around present day and determine how many days there is ice in coastal zone    
        for i in range(-dayrange, dayrange +1):
            diff = datetime.timedelta(days=i)
            diffdate = presentdate + diff
            checkfilename = outfilepath + "nt_" + diffdate.strftime('%Y%m%d') +  infile[-14:]
            if os.path.isfile(checkfilename):
                checkfile = gdal.Open(checkfilename, gdalconst.GA_ReadOnly)
                #Read input raster into array
                checkfileraster = checkfile.ReadAsArray()
                
                coastalicemaskraster = numpy.where( (coastalerrormaskarray == 1) & (checkfileraster >= 38), coastalicemaskraster + 1 , 0 )
                
                
        
        #Let ice value in coastal zone persist if there was ice the days around it
        presentdayfilename = outfilepath + "nt_" + presentdate.strftime('%Y%m%d') +  infile[-14:]
        presentdayfile = gdal.Open( presentdayfilename, gdalconst.GA_Update)
        presentdayraster = presentdayfile.ReadAsArray()
        print "coastal error mask for ", presentdayfilename
        
        presentdayraster = numpy.where( (coastalerrormaskarray == 1) & (coastalicemaskraster != 4 ), 0, presentdayraster)
        #outarray contains now NumberOfDay with ice -- burn in landmask
        landmask = gdal.Open('C:\\Users\\max\\Documents\\IcePersistency\\landmasks\\NSIDC_landmask_raster.tif', gdalconst.GA_ReadOnly)
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


#infilepath = 'U:\\SSMI\\IceConcentration\\NASATEAM\\final-gsfc\\north\\daily\\2012\\'
outfilepath = 'C:\\Users\\max\\Documents\\IcePersistency\\'

#filelist = glob.glob(infilepath + 'nt_201202*.bin')

#Get all files from given month
startyear = 1980
stopyear = 2010
month = 3 #Values 1 to 12

#Create filelist including all files for the given month between startyear and stopyear inclusive
filelist = []
for year in range(startyear, stopyear + 1):
    foldername = 'U:\\SSMI\\IceConcentration\\NASATEAM\\final-gsfc\\north\\daily\\' + str(year) + '\\'
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


FilterCoastalAreas(outfilepath)
    
CreateIcePercistanceMap(outfilepath, outfilepath)

max_ice, min_ice = CreateMaxMinIce(outfilepath, outfilepath)

print 24*'#'
print "Done creating Ice Persistance Map"
print 24*'#'