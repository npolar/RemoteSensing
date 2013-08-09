# -*- coding: utf-8 -*-
"""
Created on August 2013

Extracts and processes Radarsat sathav scenes containing Svalbard

*ExtractRadarsat -- finds images matching the location (UL, LR rectangle)

@author: max
"""

import zipfile, glob, os, shutil, gdal

def ExtractRadarsat(radarsatfile, location):
    '''
    USE IF ONLY SCENES FROM SPECIFIED LOCATION WANTED

    Checks corresponding EPSG3575 quicklook and checks RS-2 files against 
    wanted location, returning True or False
    
    Location is ULX, ULY, LRX, LRY
    
    Uses the existing quicklooks to match point, NOT the zipped RS-2 file
    since it takes longer time to extract the zip files.
    
    If no quicklooks exist, run RadarsatDetailedQuicklook.py
    
    '''
   
    #Get Filename of corresponding quicklook for radarsatfile
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)   
    radarsatquicklook = radarsatfilepath + '//' + radarsatfileshortname + '_EPSG3575.tif'
    
    
    #Open GeoTiff Quicklook
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    dataset = gdal.Open(radarsatquicklook, gdal.GA_ReadOnly)
  
    #Get Geoinformation
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
    
           
    #Check if two points are contained in image
    contained = False
    if ((location[0] < upperleft_x < location[2]) or (location[0] < lowerright_x < location[2])):
        if ((location[1] >  upperleft_y > location[3]) or (location[1] >  lowerright_y > location[3])):
            contained = True   
            print radarsatfile + ' matches'
    
    return contained            
    dataset = None
    
def ProcessNest(radarsatfile):
    '''
    Calls Nest SAR Toolbox to calibrate, map project and if wanted 
    terraincorrect images
    see http://nest.array.ca/
    
    needed Nest files at https://github.com/npolar/RemoteSensing/tree/master/Nest
    
    converts afterwards to GeoTIFF and JPEG clipped to extents of Svalbard DEM
    
    Map projection Svalbard EPSG:32633 UTM 33N
    Map Projection Barents Sea EPSG:3575
    '''
            
    #Various file paths and names:    
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)             
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)        
        
    #Define names of input and outputfile
    gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
    outputfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633.dim'

    #Extract the zipfile
    zfile = zipfile.ZipFile(radarsatfile, 'r')
    print    
    print "Decompressing image for " + radarsatfilename + " on " + radarsatfilepath    
    
    zfile.extractall(radarsatfilepath)
    
    #Call NEST routine
    print
    print "calibration and speckle and SARSIM"
    print
    print "inputfile " + radarsatfileshortname
    print "outputfile " + outputfile
    print
    print "Range Doppler terraincorrect, around 10 minutes."
    print
    
    #check that xml file is correct!
    
    #This one for Range Doppler Correction
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_LinDB_RS2.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname )

    #Close zipfile
    zfile.close()
    
    #############################################
    # Convert DIM to GEOTIFF and JPEG
    #############################################

    #Get *.img files in dim-folder
    (outputfilenamepath, outputfilename) =  os.path.split(outputfile)
    (outputfileshortname, extension) = os.path.splitext(outputfilename)
    dim_datafolder = outputfilenamepath + '//' + outputfileshortname + '.data'
    dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/*.img'
    dimlist = glob.glob(dim_datafile)
    for envifile in dimlist:
        polarisation = envifile[-9:-7]
        destinationfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633_' + polarisation + '.tif'
        jpegfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633_' + polarisation + '.jpg'
        
        print
        print 'Converting: '
        print '\nfrom ' + envifile
        print '\nto ' + destinationfile
        
        os.system("gdal_translate -a_srs EPSG:32633 -stats -of GTiff -projwin 395000 8990000 841000 8460000  " + envifile + " " +  destinationfile)
        
        os.system("gdal_translate -scale -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile + " " +  jpegfile) 
           
    #shutil.rmtree(dim_datafolder)
    #os.remove(outputfile)
    
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
filelist = glob.glob(r'C:\Users\max\Documents\08_August\*.zip')

#Define Area Of Interest
upperleft_x = 8000.0
upperleft_y = -1010000.0
lowerright_x = 350000.0
lowerright_y = -1495000.0

location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]

#Loop through filelist and process
for radarsatfile in filelist:
    
    #Check if file contains parts of Area Of Interest
    contained = ExtractRadarsat(radarsatfile, location)
    
    #If not within Area Of Interest
    if contained == False:
        continue
        print radarsatfile + ' skipped'
    
    print radarsatfile + ' processed'
    #Process image
    ProcessNest(radarsatfile)
    

print 'finished extracting Svalbard images'

#Done