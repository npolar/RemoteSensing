# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 09:07:01 2012

@author: max
"""

# Importing needed modules
import os

# The shapefile to be rasterized:
shapefile = 'C:\Users\max\Documents\Icecharts\Data\IceChart_2012\ice20120608_3575.shp'
print 'Rasterize ' + shapefile

(shapefilefilepath, shapefilename) = os.path.split(shapefile)             #get path and filename seperately
(shapefileshortname, extension) = os.path.splitext(shapefilename)           #get file name without extension

# The land area to be masked out, also being a shapefile to be rasterized
SvalbardCoast = 'C:\Users\max\Documents\PythonProjects\s100-landp_3575.shp'

# The raster file to be created and receive the rasterized shapefile
outrastername = shapefileshortname + '.tif'
outraster = 'C:\\Users\\max\\Documents\\Icecharts\\Data\\IceChart_2012\\' + outrastername

# Rasterize first Ice Type and at same time create file -- call gdal_rasterize commandline
print '\n Open Water'
os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -burn 2 -l ' + shapefileshortname +' -tr 1000 -1000 ' +  shapefile + ' ' + outraster)

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

print "\n Done"