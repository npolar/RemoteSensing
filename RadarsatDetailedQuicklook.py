# -*- coding: utf-8 -*-
"""
Created on Wed Jan 16 15:43:07 2013

Takes the Radarsat-2 zipfile and creates a map projected quicklook from 
the imagery_HH file

@author: max
"""


import zipfile, glob, os, shutil

#List of zip-files to be extracted
#filelist = glob.glob(r'C:\Users\max\Documents\trash\*.zip')
filelist = glob.glob(r'Z:\Radarsat\Sathav\2013\02_Februar\temp\*.zip')


#Loop through zipfiles, extract and create quicklook

for radarsatfile in filelist:
    
    #Split names and extensions
    (infilepath, infilename) = os.path.split(radarsatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Open zipfile
    zfile = zipfile.ZipFile(radarsatfile, 'r')
    print    
    print "Decompressing image for " + infilename + " on " + infilepath    
    
    #Extract imagery file from zipfile
    imagefile = infileshortname + '/imagery_HH.tif'
    #zfile.extract(imagefile, infilepath)  
    zfile.extractall(infilepath)
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = infilepath + '\\' + infileshortname + '\\product.xml'
    outputfilename = infilepath + '\\' + infileshortname + '\\' + infileshortname + '_EPSG3575.tif'
    browseimage = infilepath + '\\' + infileshortname + '_EPSG3575.tif'
    
    #Call gdalwarp
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs \"+proj=laea +lat_0=90 +lon_0=10 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate    
    print
    print "downsampling file"
    print
    os.system('gdal_translate -ot byte -outsize 8% 8% -scale 0 50000 0 255 ' + outputfilename + ' ' + browseimage )

    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(infilepath + '\\' + infileshortname )

    #Close zipfile
    zfile.close()
    
    
print   
print 'Done creating quicklooks for ', infilepath

#end