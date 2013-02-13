# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 07:38:16 2013

Extracts Radarsat sathav scenes containing a selected point on Svalbard
Subsets the file to wanted area

@author: max
"""



import zipfile, glob, os, shutil, gdal

#List of quicklooks in folder
#filelist = glob.glob(r'C:\Users\max\Documents\trash\*.zip')
filelist = glob.glob(r'Z:\Radarsat\Sathav\2013\01_Januar\*EPSG3575.tif')


svalbardlist = []


#Loop through zipfiles, extract and create list with Svalbard files

for radarsatfile in filelist:
    
    #Open GeoTiff Quicklook
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    
    dataset = gdal.Open(radarsatfile, gdal.GA_ReadOnly)
    #Get corner coordinates 
    svalbard_x = 60000.0        #Values in EPSG3575
    svalbard_y = -1234000.0      #Values in EPSG3575
    
    geotrans = dataset.GetGeoTransform()
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    
    upperleft_x = geotrans[0]
    upperleft_y = geotrans[3]
    pixelwidth = geotrans[1]
    pixelheight = geotrans[5]
    lowerright_x = upperleft_x + pixelwidth * cols
    lowerright_y = upperleft_y + pixelheight * rows

    
    #  check if KONGSFJORDEN in image
    if upperleft_x < svalbard_x < lowerright_x:
        if upperleft_y >  svalbard_y > lowerright_y:
            svalbardlist.append(radarsatfile)
            print ' matches: ', radarsatfile
    dataset = None
            
#Loop through svalbardlist and create map projected GeoTiffs

for svalbardfile in svalbardlist:
    (svalbardfilepath, svalbardfilename) = os.path.split(svalbardfile)             
    (svalbardfileshortname, extension) = os.path.splitext(svalbardfilename)        
    svalbardzipfile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '.zip'

    #Open zipfile
    zfile = zipfile.ZipFile(svalbardzipfile, 'r')
    print    
    print "Decompressing image for " + svalbardfilename + " on " + svalbardfilepath    
    
    zfile.extractall(svalbardfilepath)
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '\\product.xml'
    outputfilename = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_EPSG32633.tif'
    outputsubset = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_EPSG32633_Svalbard.tif'
    #Call gdalwarp
    print
    print "map projecting file"
    print
    #os.system('gdalwarp -tps -te 363100 8460000 870000 8850000 -t_srs \"+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )  
    os.system('gdalwarp -tps -te 410000 8720000 480000 8780000 -t_srs \"+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )
    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(svalbardfilepath + '\\' + svalbardfileshortname[0:-9] )

    #Close zipfile
    zfile.close()
    
    
print   
print 'Done'
    

    
    