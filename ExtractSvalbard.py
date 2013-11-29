# -*- coding: utf-8 -*-
"""
Created on August 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
Then calibrate and project image to EPSG:32633 (UTM33 WGS84) as GeoTIFF and JPG

Steps (more details in each function):
    
RadarsatDetailedQuicklook
- Creates a rough quicklook
- subsequently only used to get coordinates and projection
- better way for this needed in future version

ExtractRadarsat
- uses location to extract images matching a rectangle

ProcessNest(svalbardlist)
- Geocode and Process with NEST
- Convert NEST format toGEOTIFF
- Reprojectfrom polarstereo To3575
- needed because NEST only can project to ESPG3575

Requirements to run this code see:
http://geoinformaticstutorial.blogspot.no/2013/03/installing-python-with-gdal-on-windows.html

ISSUES AT PRESENT:
- better way to get corner coordinates
- two no data values in GeoTIFF and JPG due to reprojecting twice
- check if scene contains too much NAN
- solve NEST reprojection issue (does not do all)
- ideally scenes containing Svalbard should be terraincorrected
- Svalbard area usually has EPSG32633 and Barents EPSG 3575
"""

import zipfile, glob, os, shutil, gdal

def RadarsatDetailedQuicklook(radarsatfile):
    '''
    Takes the Radarsat-2 zipfile and creates a map projected quicklook from 
    the imagery_HH file
    '''
    
    
    #Split names and extensions
    (infilepath, infilename) = os.path.split(radarsatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Open zipfile
    zfile = zipfile.ZipFile(radarsatfile, 'r')
    print    
    print "Decompressing image for " + infilename + " on " + infilepath    
    
    #Extract imagery file from zipfile
    try:
        zfile.extractall(infilepath)
    except:
        browseimage = None
        return browseimage
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = infilepath + '\\' + infileshortname + '\\product.xml'
    outputfilename = infilepath + '\\' + infileshortname + '\\' + infileshortname + '_EPSG32633.tif'
    browseimage = infilepath + '\\' + infileshortname + '_EPSG32633.tif'
    
    #Call gdalwarp
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs EPSG:32633 ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate    
    print
    print "downsampling file"
    print
    os.system('gdal_translate -ot byte -outsize 8% 8% -scale 0 50000 0 255 ' + outputfilename + ' ' + browseimage )
    
    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(infilepath + '\\' + infileshortname )
    
    #Close zipfile
    zfile.close()
    
    return browseimage

    
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
    radarsatquicklook = radarsatfilepath + '//' + radarsatfileshortname + '_EPSG32633.tif'
    
    
    #Open GeoTiff Quicklook
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    dataset = gdal.Open(radarsatquicklook, gdal.GA_ReadOnly)
    
    contained = False     
    if dataset == None:
        return contained
    
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
    print upperleft_x , location[0] , lowerright_x, upperleft_x , location[2]  , lowerright_x
    print upperleft_y ,  location[1] , lowerright_y, upperleft_y ,  location[3] , lowerright_y
    if ((upperleft_x < location[0] < lowerright_x) and (upperleft_x < location[2]  < lowerright_x)):
        if ((upperleft_y >  location[1] > lowerright_y) and (upperleft_y >  location[3] > lowerright_y)):
            contained = True   
            print radarsatfile + ' matches'
            
    #quicklook can be removed since now jpg produced
    dataset = None     
    os.remove(radarsatquicklook)
    
    return contained            
    
    
def ProcessNest(radarsatfile, outputfilepath, location):
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
    outputfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633.dim'

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
        destinationfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633_' + polarisation + '.tif'
        jpegfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633_' + polarisation + '.jpg'
        
        print
        print 'Converting: '
        print '\nfrom ' + envifile
        print '\nto ' + destinationfile
        
        
        upperleft_x = str(location[0])        
        upperleft_y = str(location[1])     
        lowerright_x = str(location[2])    
        lowerright_y = str(location[3])   
        
        #Inglefieldbukta        
        os.system("gdal_translate -a_srs EPSG:32633 -stats -of GTiff -projwin " + upperleft_x  + " " + upperleft_y  + " " + lowerright_x  + " " + lowerright_y  + " " + envifile + " " +  destinationfile)
        
        os.system("gdal_translate -scale -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile + " " +  jpegfile) 
           
    shutil.rmtree(dim_datafolder)
    #os.remove(outputfile)
    
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
filelist = glob.glob(r'Z:\\Radarsat\\Sathav\\2010\\10_October\\RS2*.zip')
outputfilepath = 'Z:\\Radarsat\\Sathav\\processed_images\\HoltedalsfonnaKongsfjorden\\2010_10_October'

#Define Area Of Interest
#upperleft_x = 8000.0
#upperleft_y = -1010000.0
#lowerright_x = 350000.0
#lowerright_y = -1495000.0

#Holtedalfonne
upperleft_x = 419726.0
upperleft_y =  8805375.0       
lowerright_x = 471648.0        
lowerright_y = 8737956.0    

#Inglefieldbukta
#upperleft_x = 564955.9196850983425975
#upperleft_y = 8750041.7983950804919004 
#lowerright_x = 726949.9692189423367381
#lowerright_y = 8490034.1236895751208067


location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]

#Loop through filelist and process
for radarsatfile in filelist:
    
    #Create Quicklook from which area is determined (not very good solution)
    outputfile = RadarsatDetailedQuicklook(radarsatfile)
    if outputfile == None:
        continue
    
    #Check if file contains parts of Area Of Interest
       
    contained = ExtractRadarsat(radarsatfile, location)
    
    #If not within Area Of Interest
    if contained == False:
        print radarsatfile + ' skipped'
        continue
        
    
    print radarsatfile + ' processed'
    #Process image
    ProcessNest(radarsatfile, outputfilepath, location)
    

print 'finished extracting Svalbard images'

#Done