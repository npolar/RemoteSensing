# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 10:57:28 2012

@author: max
"""
# Import Modules
import ogr, osr, os, sys, glob, numpy, gdal, gdalconst


#Defining Functions

def ReprojectShapefile(infile):
    ''' 
    Takes infile and projects it into EPSG defined within the function.
    Could be changed to receive EPSG from outside
    '''
    #Define outputfile name
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    reprshapepath = infilepath + '\\EPSG3575'
    reprshapeshortname = infileshortname + '_EPSG3575'
    reprshapefile = reprshapepath + '\\'+ reprshapeshortname + extension
    
    #get file name without extension
    print '\n reproject ', infileshortname
    
    # Spatial Reference of the input file
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(4326)         # unprojected WGS84
    
    # Spatial Reference of the output file
    outSpatialRef = osr.SpatialReference()
    #outSpatialRef.ImportFromEPSG(32633)     # WGS84 UTM33N
    # outSpatialRef.ImportFromEPSG(3995)
    outSpatialRef.ImportFromEPSG(3575)       # WGS 84 / North Pole LAEA Europe
     
    # create Coordinate Transformation
    coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    
    # Open the input shapefile and get the layer
    driver = ogr.GetDriverByName('ESRI Shapefile')
    indataset = driver.Open(infile, 0)
    if indataset is None:
        print ' Could not open file'
        sys.exit(1)
    inlayer = indataset.GetLayer()
    
    # Create the output shapefile
    if os.path.exists(reprshapefile):
        driver.DeleteDataSource(reprshapefile)
    
    outdataset = driver.CreateDataSource(reprshapefile)
    
    if reprshapefile is None:
        print ' Could not create file'
        sys.exit(1)
    outlayer = outdataset.CreateLayer(reprshapeshortname, geom_type=ogr.wkbPolygon)
    
    # Get the FieldDefn for ICE_TYPE and ID and add to output shapefile
    feature = inlayer.GetFeature(0)
    fieldDefn1 = feature.GetFieldDefnRef('ICE_TYPE')
    #fieldDefn2 = feature.GetFieldDefnRef('ID')
    
    outlayer.CreateField(fieldDefn1)
    #outlayer.CreateField(fieldDefn2)
    
    # get the FeatureDefn for the output shapefile
    featureDefn = outlayer.GetLayerDefn()
    
    #Loop through input features and write to output file
    infeature = inlayer.GetNextFeature()
    while infeature:
        # for some files geometryRef does not exist. skip it
        try:
            #get the input geometry
            geometry = infeature.GetGeometryRef()
            #reproject the geometry
            geometry.Transform(coordTransform)
        except AttributeError:
            print 'Cannot process', infileshortname
            return
                
        #create a new output feature
        outfeature = ogr.Feature(featureDefn)
        
        #set the geometry and attribute
        outfeature.SetGeometry(geometry)
        outfeature.SetField('ICE_TYPE', infeature.GetField('ICE_TYPE'))
        #contains only "0" and is not in earlier files  
        #earlier files have many fields not taken here
        #outfeature.SetField('ID', infeature.GetField('ID')) 
        
        #add the feature to the output shapefile
        outlayer.CreateFeature(outfeature)
        
        #destroy the features and get the next input features
        outfeature.Destroy
        infeature.Destroy
        infeature = inlayer.GetNextFeature()
        
    #close the shapefiles
    indataset.Destroy()
    outdataset.Destroy()
    
    #create the prj projection file
    outSpatialRef.MorphToESRI()
    file = open(reprshapepath + '\\'+ reprshapeshortname + '.prj', 'w')
    file.write(outSpatialRef.ExportToWkt())
    file.close()
    
    return reprshapefile

def ReprojectShapefile2(infile):
    
    #Define outputfile name
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    reprshapepath = infilepath + '\\EPSG3575'
    reprshapeshortname = infileshortname + '_EPSG3575'
    reprshapefile = reprshapepath + '\\'+ reprshapeshortname + extension
    
    print 'Reproject Shapefile'
    os.system('ogr2ogr -s_srs EPSG:4326 -t_srs EPSG:3575 ' + reprshapefile + ' ' + infile )
    print 'Done Reproject'
    return reprshapefile
    
    
def Shape2Raster(shapefile):
    '''
    Take the input shapefile and create a raster from it
    Same name and location as input but GeoTIFF
    '''
    
    #check if shapefile exists, may not if failed in reprojection
    if shapefile==None:
        return

    #Get Path and Name of Inputfile
    (shapefilefilepath, shapefilename) = os.path.split(shapefile)             #get path and filename seperately
    (shapefileshortname, extension) = os.path.splitext(shapefilename)           #get file name without extension
    
    # The land area to be masked out, also being a shapefile to be rasterized
    SvalbardCoast = 'C:\Users\max\Documents\PythonProjects\s100-landp_3575.shp'
    MainlandCoast = 'C:\Users\max\Documents\PythonProjects\ArcticSeaNoSval.shp'
    
    print "\n \n Rasterizing", shapefilename, '\n'
    
    # The raster file to be created and receive the rasterized shapefile
    outrastername = shapefileshortname + '.tif'
    outraster = 'C:\\Users\\max\\Documents\\Icecharts\\Data\\Kit\\EPSG3575\\' + outrastername
    
    #Raster Dimensions of Raster to be created
    #Set Resolution and col / rows are calculated
    #For dimensions look at example file in EPSG 3575
    x_resolution = 100.0
    y_resolution = -100.0  #VALUE MUST BE MINUS SINCE DOWNWARD !! 
    
    #All the Arctic Ocean
    #x_origin = -3121844.7112938007
    #y_origin = 482494.5951363358
    #x_lowright = 2361155.2887061993
    #y_lowright = -3396505.404863664
    
    #Svalbard Subset -- Activate if only Svalbard is to be rasterized
    x_origin = -90000.0  
    y_origin = -962000.0
    x_lowright = 505000.0
    y_lowright = -1590000.0
    
    x_cols = int((x_lowright - x_origin) / x_resolution )
    x_rows = int((y_lowright - y_origin) / y_resolution )

    
    
    #Create raster with values defined above
    driver = gdal.GetDriverByName('GTiff')
    outfile = driver.Create(outraster, x_cols, x_rows, 1, gdal.GDT_Float64)    
    
    #Set Geotransform from largest extent (check that!)
    #Projection remains same, if Extent thus Geotransform is changed, change outfile size two lines above
    outfile.SetGeoTransform([x_origin, x_resolution, 0.0, y_origin, 0.0, y_resolution])
    outfile.SetProjection('PROJCS["WGS_84_North_Pole_LAEA_Europe",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]],PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["latitude_of_center",90],PARAMETER["longitude_of_center",10],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]')
  
    rows = outfile.RasterYSize
    cols = outfile.RasterXSize
    raster = numpy.zeros((rows, cols), numpy.float) 
    outfile.GetRasterBand(1).WriteArray( raster )
    outfile = None
    
    # Rasterize first Ice Type and at same time create file -- call gdal_rasterize commandline
    print '\n Open Water'
    #os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -burn 2 -l ' + shapefileshortname +' -tr 1000 -1000 ' +  shapefile + ' ' + outraster)
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -b 1 -burn 2 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
        
    # Rasterize the other Ice types, adding them to the already created file
    print '\nVery Open Drift Ice'
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Very Open Drift Ice\'\" -b 1 -burn 3 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Open Drift Ice'
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Drift Ice\'\" -b 1 -burn 4 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Close Drift Ice'
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Close Drift Ice\'\" -b 1 -burn 5 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Very Close Drift Ice'
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Very Close Drift Ice\'\" -b 1 -burn 6 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    print '\n Fast Ice'
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Fast Ice\'\" -b 1 -burn 1 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
    
    # Rasterize Spitsbergen land area on top
    print '\n SvalbardRaster'
    os.system('gdal_rasterize  -b 1 -burn 8 -l s100-landp_3575 '  +  SvalbardCoast + ' ' + outraster)
    
     # Rasterize Greenland and other land area on top
    print '\n MainlandRaster'
    os.system('gdal_rasterize  -b 1 -burn 8 -l ArcticSeaNoSval '  +  MainlandCoast + ' ' + outraster)
    
    
    print "\n \n Done rasterizing", shapefilename, '\n'
    

def ProcessRaster():
    ''' code allows adjusting for various calculations on the data '''
    
    #register all gdal drivers
    gdal.AllRegister()
    
    # Iterate through all rasterfiles
    filelist = glob.glob('C:\Users\max\Documents\Icecharts\Data\Kit\EPSG3575\*.tif')
    
    firstfilename = filelist[0]
    #Define file names 
    (infilepath, infilename) = os.path.split(firstfilename)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = 'C:\\Users\\max\\Documents\\Icecharts\\Data\\Kit\\icechart_processed.tif'
    
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
        inband = icechart.GetRasterBand(1)
        
        outband = outraster.GetRasterBand(1)
        

        
        #Read input raster into array
        iceraster = icechart.ReadAsArray()
        
        #Process the image
        for i in range(rows):
            for j in range(cols):
                if iceraster[i,j] == 1:
                    outarray[i,j] = outarray[i,j] + 1
                else:
                    outarray[i,j] = 0
                    
                if iceraster[i,j] == 8:
                    outarray[i,j] = 999
        

        
        
      
# Process outraster
#    print 'Process outraster'
#    for k in range(rows):
#        for l in range(cols):
#            if (outarray[k,l] / 1500.0 ) > 1:
#                outarray[k,l] = 1
#            else:
#                outarray[k,l] = 0
#                
#            if iceraster[k,l] == 8:
#                    outarray[k,l] = 8
        
    # Write outraster to file
    outband.WriteArray(outarray)
    outband.FlushCache()
       

    #Clear arrays and close files
    inband = None
    outband = None
    iceraster = None
    outraster = None
    outarray = None
    print 'Done Processing Raster'


def AddMissingDays():
    ''' searches through mid-march til end of April files and replace
    missing rasterconverted ice chart files with the nearest available previous one
    
    MUCH TOO COMPLICATED ___ LOOK AT IceChartProcessing.py SCRIPT
    '''
    # Create a list of all available raster icechart files
    filelist = sorted(glob.glob('C:\Users\max\Documents\Icecharts\Data\Kit\EPSG3575\*EPSG3575.tif'))
    
    #Settings
    #Year to be analyzed but then from 15 March til 30 April -- read from first file
    year = int(filelist[0][54:58])
        
    
    outfilepath = 'C:\\Users\\max\\Documents\\Icecharts\Data\\Kit\\EPSG3575'
    
    print 'Search for missing files and replace with precious ones'
    #register all gdal drivers
    gdal.AllRegister()
    

    
    #Check all dates in march
    #Read first filename and determine first available date, format mmdd
    date = int(filelist[0][58:62])
    
    #loop through files from first file to end of month
    for i in range(date, 332):
        
        #compile file name to be searched for
        filename = outfilepath + '\\ice' + str(year) + '0' + str(i) + '_EPSG3575.tif'
        
        
        if (filename in filelist) == False:
            
            replacingfile = outfilepath + '\\ice' + str(year) + '0' + str(i-1) + '_EPSG3575.tif'
            
            j = i-1
            while (replacingfile in filelist) == False:
                j = j-1
                replacingfile = outfilepath + '\\ice' + str(year) + '0' + str(j) + '_EPSG3575.tif'
                src_ds = gdal.Open( replacingfile )
                
            print 'WARNING: ice' + str(year) + '0' + str(i) + '_EPSG3575.tif replaced with ice' + str(year) + '0' + str(j) + '_EPSG3575.tif'
           
            
            src_ds = gdal.Open( replacingfile )
            if src_ds is None:
                print 'Could not open ', replacingfile
            driver = src_ds.GetDriver()
            driver.Register()
            dst_ds = driver.CreateCopy(filename, src_ds , 0 )
    
            # close properly the dataset
            dst_ds = None
            src_ds = None
    
    
    #Check all dates in April
    #Find first availabel date for April
    for i in range(401, 431):
        filename = outfilepath + '\\ice' + str(year) + '0' + str(i) + '_EPSG3575.tif'
        if (filename in filelist) is True:
            date = int(i)
            break
    
    #loop through files from first April to first available date to replace these by 31 March
    for i in range(401, date):
        filename = outfilepath + '\\ice' + str(year) + '0' + str(i) + '_EPSG3575.tif'
        if (filename in filelist) is False:
            replacingfile = outfilepath + '\\ice' + str(year) + '0331_EPSG3575.tif'
            src_ds = gdal.Open( replacingfile )
                
            print 'WARNING: ice' + str(year) + '0' + str(i) + '_EPSG3575.tif replaced with ice' + str(year) + '0331_EPSG3575.tif'
           
            
            src_ds = gdal.Open( replacingfile )
            if src_ds is None:
                print 'Could not open ', replacingfile
            driver = src_ds.GetDriver()
            driver.Register()
            dst_ds = driver.CreateCopy(filename, src_ds , 0 )
    
            # close properly the dataset
            dst_ds = None
            src_ds = None
    
    
    #loop through files from first file to end of month
    for i in range(date, 430):
        
        #compile file name to be searched for
        filename = outfilepath + '\\ice' + str(year) + '0' + str(i) + '_EPSG3575.tif'
        
        
        if (filename in filelist) == False:
            
            replacingfile = outfilepath + '\\ice' + str(year) + '0' + str(i-1) + '_EPSG3575.tif'
            
            j = i-1
            while (replacingfile in filelist) == False:
                j = j-1
                replacingfile = outfilepath + '\\ice' + str(year) + '0' + str(j) + '_EPSG3575.tif'
                src_ds = gdal.Open( replacingfile )
                
            print 'WARNING: ice' + str(year) + '0' + str(i) + '_EPSG3575.tif replaced with ice' + str(year) + '0' + str(j) + '_EPSG3575.tif'
           
            
            src_ds = gdal.Open( replacingfile )
            if src_ds is None:
                print 'Could not open ', replacingfile
            driver = src_ds.GetDriver()
            driver.Register()
            dst_ds = driver.CreateCopy(filename, src_ds , 0 )
    
            # close properly the dataset
            dst_ds = None
            src_ds = None
            
       
    print 'Done replacing missing years'    

    
#end
# Core of Program follows here


# Define filepaths
# name of outputfile = inputname_EPSG3575.shp and inputname_EPSG3575.tif
# Kit needs between 15/3 and 1/5

infilepath = 'C:\\Users\\max\\Documents\\Icecharts\Data\\Kit'
outfilepath = 'C:\\Users\\max\\Documents\\Icecharts\Data\\Kit\\EPSG3575'

# Iterate through all shapefiles
filelist = glob.glob('C:\Users\max\Documents\Icecharts\Data\Kit\*.shp')

for icechart in filelist:
    
    #reprshapefile = ReprojectShapefile(icechart)
    reprshapefile = ReprojectShapefile2(icechart)
    Shape2Raster(reprshapefile)
    
    #set shapefile to None so that it stays None in case reprojection fails.
    reprshapefile = None    

#Activate AddMissingDays if you want to add missing days with the previous one
AddMissingDays()    
ProcessRaster()    

#END