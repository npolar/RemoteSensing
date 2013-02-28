# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 09:04:29 2013

@author: max

Classification into Glacier Surface Types

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
        
    # Rasterize mask and at same time create file -- call gdal_rasterize commandline
    print '\n Rasterize ', infilename
    os.system('gdal_rasterize -burn 2 -l ' + infileshortname +' -tr 20.0 -20.0 ' +  infile + ' ' + outraster)
    



def CropGlacier(inshapefile, inSARfile):
    '''
    Crops SAR image to extent of Mask and Remove all Values outside Mask
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    outraster = inSARfilepath + '/' + inSARfileshortname + '_crop.tif'
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    #Register driver and open file
    shapedriver = ogr.GetDriverByName('ESRI Shapefile')   
    maskshape = shapedriver.Open(inshapefile, 0)
    if maskshape is None:
        print 'Could not open ', inshapefilename
        return
        
    #Get Extension of Layer
    masklayer = maskshape.GetLayer()
    maskextent = masklayer.GetExtent()
    print 'Extent of ', inshapefilename, ': '
    print maskextent
    print 'UL: ', maskextent[0], maskextent[3]
    print 'LR: ', maskextent[1], maskextent[2]

    # crop image with gdal_translate -- call gdal_rasterize commandline
    print '\n Subsetting ', inSARfilename, ' to glacier extent'
    os.system('gdal_translate -projwin ' + str(maskextent[0]) + ' ' + str(maskextent[3]) + ' ' + str(maskextent[1]) + ' ' + str(maskextent[2]) + ' ' + inSARfile + ' ' + outraster)
    
    #Close files 
    maskshape = None
    

#Core of Program follows

inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Kongsvegen2000.shp'
inSARfile = 'C:\Users\max\Documents\Svalbard\KongsvegenOtsuTest.tif'


RasterizeMask(inshapefile)
CropGlacier(inshapefile, inSARfile)


