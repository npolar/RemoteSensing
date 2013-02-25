# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 09:04:29 2013

@author: max
"""

#import modules

import ogr, os, gdal, numpy


# Define Functions

def RasterizeMask(infile):
    '''
    Takes infile and creates raster with extension of shapefil
    '''
    
    # Define filenames
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    outraster = infilepath + '/' + infileshortname + '.tif'    
    
    #Register driver and open file
    shapedriver = ogr.GetDriverByName('ESRI Shapefile')   
    maskshape = shapedriver.Open(infile, 0)
    if maskshape is None:
        print 'Could not open ', infilename
        return
    
    #Get Extension of Layer
    masklayer = maskshape.GetLayer()
    maskextent = masklayer.GetExtent()
    print 'Extent of ', infilename, ': '
    print maskextent
    print 'UL: ', maskextent[0], maskextent[3]
    print 'LR: ', maskextent[1], maskextent[2]
    
#    #Create Raster
#    #Dimensions of raster
#    x_origin =  maskextent[0]  
#    y_origin =  maskextent[3]
#    x_lowright = maskextent[1]
#    y_lowright = maskextent[2] 
#    
#    x_resolution = 20.0
#    y_resolution = -20.0  #VALUE MUST BE MINUS SINCE DOWNWARD !
#       
#    x_cols = int((x_lowright - x_origin) / x_resolution )
#    x_rows = int((y_lowright - y_origin) / y_resolution )
#    
#    rasterdriver = gdal.GetDriverByName('GTiff')
#    outfile = rasterdriver.Create(outraster, x_cols, x_rows, 1, gdal.GDT_Float64)    
#    
#    #Projection remains same, if Extent thus Geotransform is changed, change outfile size
#    outfile.SetGeoTransform([x_origin, x_resolution, 0.0, y_origin, 0.0, y_resolution])
#    #EPSG:32633 UTM 33N / WGS84 -- http://spatialreference.org/ref/epsg/32633/
#    outfile.SetProjection('PROJCS["WGS_1984_UTM_Zone_33N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]')
#      
#    #Fill new raster with zeros and close
#    rows = outfile.RasterYSize
#    cols = outfile.RasterXSize
#    raster = numpy.zeros((rows, cols), numpy.float) 
#    outfile.GetRasterBand(1).WriteArray( raster )
#    outfile = None

    # Rasterize mask and at same time create file -- call gdal_rasterize commandline
    print '\n Rasterize ', infilename
    os.system('gdal_rasterize -burn 2 -l ' + infileshortname +' -tr 20.0 -20.0 ' +  infile + ' ' + outraster)
    
    
    print 'Done'
    
    #Close files
    outfile = None
    maskshape = None

#Core of Program follows

infile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Kongsvegen2000.shp'

RasterizeMask(infile)
