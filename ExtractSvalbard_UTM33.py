# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 07:38:16 2013

Extracts Radarsat sathav scenes containing a selected point on Svalbard
Subsets the file to wanted area
  or
Calibrates and terraincorrects the image calling NEST

@author: max
"""



import zipfile, glob, os, shutil, gdal

#List of quicklooks in folder
#filelist = glob.glob(r'C:\Users\max\Documents\trash\*.zip')
filelist = glob.glob(r'Z:\Radarsat\Sathav\2013\06_June\*EPSG3575.tif')


svalbardlist = []

#Point to be included
svalbard_x = 60000.0        #Values in EPSG3575
svalbard_y = -1234000.0      #Values in EPSG3575

#Loop through zipfiles, extract and create list with Svalbard files

for radarsatfile in filelist:
    
    #Open GeoTiff Quicklook
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    dataset = gdal.Open(radarsatfile, gdal.GA_ReadOnly)

    
    geotrans = dataset.GetGeoTransform()
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    
    #Determine extension and resolution
    upperleft_x = geotrans[0]
    upperleft_y = geotrans[3]
    pixelwidth = geotrans[1]
    pixelheight = geotrans[5]
    lowerright_x = upperleft_x + pixelwidth * cols
    lowerright_y = upperleft_y + pixelheight * rows
    
    #Textfile to receive list of matching files
    filename = 'F:\\Jack\\' + 'selectedSAR.txt'
    
    #  check if KONGSFJORDEN in image
    if upperleft_x < svalbard_x < lowerright_x:
        if upperleft_y >  svalbard_y > lowerright_y:
            svalbardlist.append(radarsatfile)
            print ' matches: ', radarsatfile
            #append matching file to textfile            
            f = open(filename, 'a')
            f.write(radarsatfile + " \n")
            f.close()  
    
    dataset = None
            
#Loop through svalbardlist and create map projected GeoTiffs

#for svalbardfile in svalbardlist:
#    (svalbardfilepath, svalbardfilename) = os.path.split(svalbardfile)             
#    (svalbardfileshortname, extension) = os.path.splitext(svalbardfilename)        
#    svalbardzipfile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '.zip'
#    
#
#    
#    
#    #Open zipfile
#    zfile = zipfile.ZipFile(svalbardzipfile, 'r')
#    print    
#    print "Decompressing image for " + svalbardfilename + " on " + svalbardfilepath    
#    
#    zfile.extractall(svalbardfilepath)
#    
#    #Define names
#    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
#    gdalsourcefile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '\\product.xml'
#    outputfilename = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_EPSG32633.tif'
#    outputsubset = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_EPSG32633_Svalbard.tif'
#    
#    #write occurrences to file
#    filename = 'F:\\Jack\\' + 'selectedSAR.txt'
#    f = open(filename, 'a')
#    f.write(svalbardfile + " \n")
#    f.close()  
#    
#    #Call gdalwarp
#    print
#    print "map projecting file"
#    print
#    #os.system('gdalwarp -tps -te 363100 8460000 870000 8850000 -t_srs \"+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )  
#    os.system('gdalwarp -tps -te 410000 8720000 480000 8780000 -t_srs \"+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )
#    #Remove folder where extracted and temporary files are stored
#    shutil.rmtree(svalbardfilepath + '\\' + svalbardfileshortname[0:-9] )
#
#    #Close zipfile
#    zfile.close()
    

#Loop through svalbardlist and create terrain corrected GeoTiffs
for svalbardfile in svalbardlist:
    
    #Various file paths and names:    
    (svalbardfilepath, svalbardfilename) = os.path.split(svalbardfile)             
    (svalbardfileshortname, extension) = os.path.splitext(svalbardfilename)        
    svalbardzipfile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '.zip'
        
    #Extract the zipfile
    zfile = zipfile.ZipFile(svalbardzipfile, 'r')
    print    
    print "Decompressing image for " + svalbardfilename + " on " + svalbardfilepath    
    
    zfile.extractall(svalbardfilepath)
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '\\product.xml'
    outputfilename = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_Cal_Spk_SARSIM_EPSG32633.dim'
    outputsubset = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_EPSG32633_Svalbard.tif'
    
    
    #Call NEST routine
    print
    print "calibration and speckle and SARSIM"
    print
    print "inputfile " + svalbardfileshortname[0:-9]
    print "outputfile " + outputfilename
    print
    print "this may take some time per image (> 1h)..."
    
    #check that xml file is correct!
    #os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_RS2.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfilename + '"' )
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_SarsimTC_LinDB_RS2.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfilename + '"' )
    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(svalbardfilepath + '\\' + svalbardfileshortname[0:-9] )

    #Close zipfile
    zfile.close()
    
print   
print 'Done'
    
#End
    
    