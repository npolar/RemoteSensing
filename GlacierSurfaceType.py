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
    
    # Rasterize mask and at same time create file -- call gdal_rasterize commandline
    print '\n Rasterize ', infilename
    os.system('gdal_rasterize -burn 2 -l ' + infileshortname +' -tr 20.0 -20.0 ' +  infile + ' ' + outraster)
    
    #Close files 
    maskshape = None


def CropGlacier(infile, glacier):
    '''
    Crops SAR image to extent of Mask and Remove all Values outside Mask
    '''
    # Define filenames
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    outraster = infilepath + '/' + infileshortname + '_crop.tif'

    
    
    

#Core of Program follows

inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Kongsvegen2000.shp'
inSARfile = 'C:\Users\max\Documents\Svalbard\KongsvegenOtsuTest.tif'


RasterizeMask(inshapefile)
CropGlacier(inSARfile)


