# -*- coding: utf-8 -*-
"""
Created on August 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
Then calibrate and project image to EPSG:3575 as GeoTIFF and JPG

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
    
    #Process using NEST
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_reproj_LinDB_Barents.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
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
    dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/Sigma*.img'
    dimlist = glob.glob(dim_datafile)
    
    #Loop through Sigma*.img files and convert to GeoTIFF and JPG
    for envifile in dimlist:
        polarisation = envifile[-9:-7]
        destinationfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_polarstereo_' + polarisation + '.tif'
        #auxfile is created automatically by NEST, name defined to remove it       
        auxfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_polarstereo_' + polarisation + '.tif.aux.xml'
        destinationfile2 = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3575_' + polarisation + '.tif'
        jpegfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3575_' + polarisation + '.jpg'
        
        jpegsmallfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '_40percent.jpg'
        jpegsmallfile2 = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '_09percent.jpg'
        
        print
        print 'Converting: '
        print '\nfrom ' + envifile
        print '\nto ' + destinationfile
        
        
        #Convert toGeoTIFF
        os.system("gdal_translate -a_srs C:\Users\max\Documents\PythonProjects\Nest\polarstereo.prj -stats -of GTiff  " + envifile + " " +  destinationfile)
        
        #Reproject to EPSG:3575
        os.system("gdalwarp -s_srs C:\Users\max\Documents\PythonProjects\Nest\polarstereo.prj -t_srs EPSG:3575 " + destinationfile + " " +  destinationfile2)
        
        #Convert to JPG
        os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
        #Create small jpeg
        os.system("gdal_translate -outsize 40% 40% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile)
        os.system("gdal_translate -outsize 09% 09% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile2)
        
        
        #Remove original GeoTIFF in 3033 since we now have 3575        
        os.remove(destinationfile)
        #os.remove(auxfile)
    
    #Remove BEAM-DIMAP files from NEST      
    shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
filelist = glob.glob(r'G:\satellittdata\flerbrukBarents\*.zip')

#Define Area Of Interest
upperleft_x = 8000.0
upperleft_y = -1010000.0
lowerright_x = 350000.0
lowerright_y = -1495000.0

location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]

#Loop through filelist and process
for radarsatfile in filelist:
    
    #Create Quicklook from which area is determined (not very good solution)
    outputfile = RadarsatDetailedQuicklook(radarsatfile)
    
    #Check if file contains parts of Area Of Interest
    #contained = ExtractRadarsat(radarsatfile, location)
    
    #If not within Area Of Interest
    #if contained == False:
    #    continue
    #    print radarsatfile + ' skipped'
    
    print radarsatfile + ' processed'
    #Process image
    ProcessNest(radarsatfile)
    
    #Remove quicklook as jpeg no available
    os.remove(outputfile)

print 'finished extracting Barents images'

#Done