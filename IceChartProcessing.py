# -*- coding: utf-8 -*-
"""
Created on Tue Dec 03 13:31:59 2013

Processing met.no ice charts

@author: max
"""
# Import Modules
import ogr, osr, os, sys, glob, numpy, gdal, gdalconst, datetime



##############################################################################
#  Defining Functions
##############################################################################

def ReprojectShapefile(infile, inproj, outproj):
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
    print 'Reproject Shapefile'    
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
    SvalbardCoast = 'C:\Users\max\Documents\Icecharts\landmasks\s100-landp_3575.shp'
    MainlandCoast = 'C:\Users\max\Documents\Icecharts\landmasks\ArcticSeaNoSval.shp'
    
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
    

def AddMissingDays(outfilepath):
    '''
    if file is missing, replace by previous one
    
    look through all files located at outfilepath
    '''
    #register all gdal drivers
    gdal.AllRegister()    
    
    # Create a list of all available raster icechart files
    filelist = sorted(glob.glob(outfilepath + "\\*.tif"))
    
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
    
    #http://pymotw.com/2/datetime/
    #http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    d1 =  datetime.date(year1, month1, day1)
    d2 =  datetime.date(year2, month2, day2)
    diff = datetime.timedelta(days=1)
    
    #date3 is working date to be looped through  -- set to start date   
    date3 = date1
    d3 = d1
    
    print 'Search for missing files and replace with precious ones'
    
    while date3 != date2:
        
        #Create filename whose existence is to be checked
        checkfilename = outfilepath + "ice" + d3.strftime('%Y%m%d') +  filelist[1][-13:]
                
        if (checkfilename in filelist) is False:
            
            #Create filename previous day
            previousday = d3 - diff
            replacingfile = outfilepath + "ice" + previousday.strftime('%Y%m%d') +  filelist[1][-13:]
            
            #Replace by previous day         
            print  os.path.split(checkfilename)[1] + " is missing!"
            print "Replacing " + os.path.split(checkfilename)[1] + " with " + os.path.split(replacingfile)[1]
            print
            
            src_ds = gdal.Open( replacingfile )
            if src_ds is None:
                print 'Could not open ', replacingfile
            driver = src_ds.GetDriver()
            driver.Register()
            dst_ds = driver.CreateCopy(checkfilename, src_ds , 0 )
    
            # close properly the dataset
            dst_ds = None
            src_ds = None
            
            ##### ADD SHAPEFILES TO BE REPLACED AS WELL #######
            
            
        #Increase working date for next loop
        date3 = int((d3 + diff).strftime('%Y%m%d'))         
        d3 = (d3 + diff)

                
  
    print "Done replacing missing dates"    

##############################################################################
#  Core of program follows here
##############################################################################

# Path where shapefiles are located and output files to be stored
infilepath = 'C:\\Users\\max\\Documents\\Icecharts\Data\\'
outfilepath = 'C:\\Users\\max\\Documents\\Icecharts\Data\\EPSG3575\\'



#################### ADJUST ALL PARAMETERS HERE ##############################  
#Define parameters
inproj = "EPSG:4326"  #EPSG:4326 is map projection of met.no shapefiles
outproj = "EPSG:3575" #EPSG:3575 for Arctic Ocean, EPSG:32633 for Svalbard

rasterresolution = 100.0
 
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

location = [x_origin, y_origin, x_lowright, y_lowright]

###  landmask path located in Shape2Raster but should remain fixed ###

################### END ADJUST PARAMETERS ####################################



# Iterate through all shapefiles
filelist = glob.glob(infilepath + '*.shp')

for icechart in filelist:
    
    #Reproject Shapefile
    reprshapefile = ReprojectShapefile(icechart, inproj, outproj)
    
    #Convert Shapefile to Raster
    Shape2Raster(reprshapefile, rasterresolution, location)
    
    #set shapefile to None so that it stays None in case reprojection fails.
    reprshapefile = None

#Add Missing Days (like weekends or faulty shapefile)
AddMissingDays(outfilepath) 

#Process Raster



print "Done"

#End