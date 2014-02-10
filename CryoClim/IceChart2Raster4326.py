# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 10:57:28 2012

@author: max

Simply creates a unprojected WGS84 raster from ice chart shapefile, converts to ENvi format afterwards
"""
# Import Modules
import ogr, osr, os, sys, glob, numpy, gdal, gdalconst


#Defining Functions




    
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
    SvalbardCoast = 'C:\Users\max\Documents\PythonProjects\s100-landp_4326.shp'
    MainlandCoast = 'C:\Users\max\Documents\PythonProjects\ArcticSea2_4326.shp'
    #MainlandCoast = 'C:\Users\max\Documents\PythonProjects\ArcticSeaNoSval_4326.shp'
    
    print "\n \n Rasterizing", shapefilename, '\n'
    
    # The raster file to be created and receive the rasterized shapefile
    #outrastername = shapefileshortname + '.tif'
    outrastername = shapefileshortname + '.tif'
    outraster = 'C:\\Users\\max\\Documents\\Angelika\\EPSG4326\\' + outrastername
    

    
    # Rasterize first Ice Type and at same time create file -- call gdal_rasterize commandline
    print '\n Open Water'
    os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -burn 2 -l ' + shapefileshortname +' -ts 6000 6000 ' +  shapefile + ' ' + outraster)
    #os.system('gdal_rasterize -ts 1000 -1000 -a ICE_TYPE  -where \"ICE_TYPE=\'Open Water\'\" -b 1 -burn 2 -l ' + shapefileshortname +' ' +  shapefile + ' ' + outraster)
        
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
    os.system('gdal_rasterize  -b 1 -burn 8 -l s100-landp_4326 '  +  SvalbardCoast + ' ' + outraster)
    
     # Rasterize Greenland and other land area on top
    print '\n MainlandRaster'
    os.system('gdal_rasterize  -b 1 -burn 8 -l ArcticSea2_4326 '  +  MainlandCoast + ' ' + outraster)
    
    
    print "\n \n Done rasterizing", shapefilename, '\n'
    
    #Call Function to convert to Envi
    print "Tiff2Envi"
    Tiff2Envi(outraster)

def Tiff2Envi(infile):
    #check if shapefile exists
    if infile==None:
        return

    #Get Path and Name of Inputfile
    (infilefilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)           #get file name without extension
    outfile = infilepath + '\\'+ infileshortname + '.img'           #create outputfilename
    
    #Open Dataset and Read as Array
    dataset = gdal.Open(infile, gdal.GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray(0, 0, dataset.RasterXSize, dataset.RasterYSize)
    
    #Driver for output dataset
    driver = gdal.GetDriverByName('ENVI')
    driver.Register()
    
    #Get Dimensions for Outputdataset
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    bands = dataset.RasterCount
    datatype = band.DataType
    
    #Create outputfile
    print 'Creating ', outfile, ' with ', cols, rows, bands, datatype
    outDataset = driver.Create(outfile, cols, rows, bands, datatype)
    
    #Set Projectioninfo
    geoTransform = dataset.GetGeoTransform()
    outDataset.SetGeoTransform(geoTransform)
    
    proj = dataset.GetProjection()
    outDataset.SetProjection(proj)
    
    #Write Data to output file
    outBand = outDataset.GetRasterBand(1)
    outBand.WriteArray(data, 0, 0)
    
    #Close files
    outfile = None
    outDataset = None
    outBand = None
    data = None
    
    
# Core of Program follows here


# Define filepaths
infilepath = 'C:\\Users\\max\\Documents\Angelika'
outfilepath = 'C:\\Users\\max\\Documents\\Angelika\\EPSG4326'

# Iterate through all shapefiles
filelist = glob.glob('C:\Users\max\Documents\Angelika\*.shp')

for icechart in filelist:
    
    
    Shape2Raster(icechart)
    
 

#END