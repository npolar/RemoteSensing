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

import zipfile, glob, os, shutil, gdal, fnmatch, pyproj, gdalconst, osr

def CheckExistingQuicklook(radarsatfile, location):
    '''
    check if quicklook exists and if so, if area is contained in it
    '''
    
    #Get Filename of corresponding quicklook for radarsatfile
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)   
       
    existingquicklook = radarsatfilepath + '//' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_HH.tif'

    
    #check if quicklook exists
    if (not os.path.exists(existingquicklook)):
        return
    
    
    upperleft_x = location[0]
    upperleft_y = location[1]
    lowerright_x = location[2]
    lowerright_y = location[3]
    
    #Get Corners from existing quicklook
    #Open GeoTiff Quicklook
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    dataset = gdal.Open(existingquicklook, gdal.GA_ReadOnly)
    
    contained = False     
    if dataset == None:
        return contained
    
    #Get Geoinformation
    geotrans = dataset.GetGeoTransform()
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    #Determine extension and resolution
    quick_upperleft_x = geotrans[0]
    quick_upperleft_y = geotrans[3]
    pixelwidth = geotrans[1]
    pixelheight = geotrans[5]
    quick_lowerright_x = quick_upperleft_x + pixelwidth * cols
    quick_lowerright_y = quick_upperleft_y + pixelheight * rows
    
           
    #Check if two points are contained in image
    contained = False
    #print quick_upperleft_x , upperleft_x , quick_lowerright_x, quick_upperleft_x , lowerright_x  , quick_lowerright_x
    #print quick_upperleft_y , upperleft_y , quick_lowerright_y, quick_upperleft_y , lowerright_y, quick_lowerright_y
    if ((quick_upperleft_x < upperleft_x < quick_lowerright_x) and (quick_upperleft_x < lowerright_x  < quick_lowerright_x)):
        if ((quick_upperleft_y >   upperleft_y > quick_lowerright_y) and (quick_upperleft_y >  lowerright_y > quick_lowerright_y)):
            contained = True   
            print 'Found match: ', radarsatfile 
    return contained

def CreateQuicklook(radarsatfile):
    '''
    Takes the Radarsat-2 zipfile and creates a map projected quicklook from 
    the imagery_HH file
    '''
    
    
    #Split names and extensions
    (infilepath, infilename) = os.path.split(radarsatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Open zipfile
    try:
        zfile = zipfile.ZipFile(radarsatfile, 'r')
    except:
        outputfilename = None
        return outputfilename
    
    print    
    print "Decompressing image for " + infilename + " on " + infilepath    
    print
    #Extract imagery file from zipfile
    try:
        zfile.extractall(infilepath)
    except:
        outputfilename = None
        return outputfilename
    
    #Define names
    gdalsourcefile = infilepath + '\\' + infileshortname + '\\product.xml'
    outputfilename = infilepath + '\\' + infileshortname + '_EPSG3575.tif'
    
    #Call gdalwarp
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs \"+proj=laea +lat_0=90 +lon_0=10 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(infilepath + '\\' + infileshortname )
    
    #Close zipfile
    zfile.close()
    
    return outputfilename
    
def CheckLocation(radarsatfile, location):
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
    
    #print location[0], upperleft_x, location[2], location[0], lowerright_x, location[2]
    #print location[1], upperleft_y, location[3], location[1], lowerright_y, location[3]
    
  
    if ((upperleft_x < location[0] < lowerright_x) and (upperleft_x < location[2]  < lowerright_x)):
        if ((upperleft_y >  location[1] > lowerright_y) and (upperleft_y >  location[3] > lowerright_y)):
            contained = True   
            print 'Found match', radarsatfile 
    return contained            
    dataset = None
    
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
        
    if radarsatfileshortname[0:3] == 'RS2':  # RADARSAT-2
        gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
        nestfilename = 'Calib_Spk_TC_LinDB_Barents.xml'
    if radarsatfileshortname[0:2] == 'S1':   # SENTINEL-1
        gdalsourcefile = radarsatfilepath  +  '\\' + radarsatfileshortname + '.safe' + '\\' + 'manifest.safe'
        nestfilename = 'Calib_Spk_TC_LinDB_Sentinel.xml'
  
    outputfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575.dim'

    #Extract the zipfile
    try:
        zfile = zipfile.ZipFile(radarsatfile, 'r')
    except:
        return
    print    
    print "Decompressing image for " + radarsatfilename + " on " + radarsatfilepath    
    
    zfile.extractall(radarsatfilepath)
    
    #Call NEST routine
    print
    print "NEST Processing"
    print
    print "inputfile " + radarsatfileshortname
    print "outputfile " + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575.dim'
    print
      
    #check that xml file is correct!
    
    #Process using NEST
    #os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_reproj_LinDB_Barents.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\\' + nestfilename + ' -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
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
        destinationfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_temp.tif'
        #auxfile is created automatically by NEST, name defined to remove it       
        auxfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif.aux.xml'
        destinationfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        destinationfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_SUBSET.tif'
        jpegfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.jpg'
        jpegfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_SUBSET.jpg'
        
        jpegsmallfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_40percent.jpg'
        jpegsmallfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_10percent.jpg'
        jpegsmallfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_20percent.jpg'
        jpegsmallfile4 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_30percent.jpg'
        jpegsmallfile5 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_50percent.jpg'
        
        tiffsmallfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_40percent.tif'
        tiffsmallfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_10percent.tif'
        tiffsmallfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_20percent.tif'
        tiffsmallfile4 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_30percent.tif'
        
        print
        print 'Converting to GeoTIFF: '
        print '\nfrom ' + envifile
        print '\nto ' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        
 
        os.system("gdal_translate -a_srs EPSG:3575 -stats -of GTiff  " + envifile + " " +  destinationfile2)
                    
        
        if location != []:
            print
            print "subsetting the scene"
            print
            
            
            upperleft_x = location[0]
            upperleft_y = location[1]
            lowerright_x = location[2]
            lowerright_y = location[3]       
            os.system("gdal_translate -a_srs EPSG:3575 -stats  -of GTiff -projwin " + str(upperleft_x)  + " " + str(upperleft_y)  + " " + str(lowerright_x)  + " " + str(lowerright_y)  + " " + destinationfile2 + " " +  destinationfile3)
                
            #Convert to JPG
            print
            print "create jpeg scene"
            print
            os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile3 + " " +  jpegfile3) 
        else:
            
            #Convert to JPG
            print
            print "create jpeg scene"
            print
            os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
        #Create small jpeg --- THESE ARE CREATED FOR FIELD WORK TRANSFER ONLY DURING FIELD WORK
        os.system("gdal_translate -outsize 40% 40% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile)
        os.system("gdal_translate -outsize 10% 10% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile2)
        os.system("gdal_translate -outsize 20% 20% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile3)
        os.system("gdal_translate -outsize 30% 30% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile4)
        os.system("gdal_translate -outsize 50% 50% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile5)
        
        #Create small jpeg --- THESE ARE CREATED FOR FIELD WORK TRANSFER ONLY DURING FIELD WORK
        os.system("gdal_translate -ot Int16 -co COMPRESS=DEFLATE -co PREDICTOR=2 -co ZLEVEL=9 -outsize 40% 40% -of GTiff " + destinationfile2 + " " + tiffsmallfile)
        os.system("gdal_translate -outsize 10% 10%  -of GTiff " + destinationfile2 + " " + tiffsmallfile2)
        os.system("gdal_translate -outsize 20% 20%  -of GTiff " + destinationfile2 + " " + tiffsmallfile3)
        os.system("gdal_translate -outsize 30% 30%  -of GTiff " + destinationfile2 + " " + tiffsmallfile4)
    
        #Remove original GeoTIFF in 3033 since we now have 3575        
        try:
            os.remove(destinationfile)
        except:
            pass
        
        #os.remove(auxfile)
    
    #Remove BEAM-DIMAP files from NEST      
    shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
#inputfilepath = 'Z:\\Radarsat\\Flerbruksavtale\\ArcticOcean_Svalbard\\2014'
#outputfilepath = 'Z:\\Radarsat\\Flerbruksavtale\\ArcticOcean_Svalbard\\2014'
#outputfilepath = 'G:\\FramstraitExtract'

#inputfilepath = 'Z:\\Radarsat\\Flerbruksavtale\\ArcticOcean_Svalbard'
#outputfilepath = 'Z:\\Radarsat\\Flerbruksavtale\\ArcticOcean_Svalbard'
inputfilepath = 'C:\\Users\\max\\Documents\\temp'
outputfilepath  = 'C:\\Users\\max\\Documents\\temp'

filelist = []
for root, dirnames, filenames in os.walk(inputfilepath):
  for filename in fnmatch.filter(filenames, '*.zip'):
      filelist.append(os.path.join(root, filename))


#Define Area Of Interest
#upperleft_x =  -380000.0
#upperleft_y =  -1000000.0
#lowerright_x = -220000.0
#lowerright_y = -1160000.0

#upperleft_x =  -140000.0
#upperleft_y =  -1031000.0
#lowerright_x = -8400.0
#lowerright_y = -1162600.0

upperleft_x =  -464400.0
upperleft_y =  -1075577.0
lowerright_x = -259600.0
lowerright_y = -1280377.0

# IF NO IMAGE SUBSETTING, LEAVE location = []
location =[]
#location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]

#Loop through filelist and process
for radarsatfile in filelist:
    
    #Check if quicklook exists and contains area
    #Get Filename of corresponding quicklook for radarsatfile
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)   
   
    existingquicklook = radarsatfilepath + '//' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_HH.tif'
    existingquicklook2 = radarsatfilepath + '//' + radarsatfileshortname + '_EPSG3575.tif'
    
    
    contained = False
    #check if quicklook exists
    if ( os.path.exists(existingquicklook) & (location != [])):
        print        
        print "quicklook exists"
        print 
        contained = CheckExistingQuicklook(radarsatfile, location)
    elif( os.path.exists(existingquicklook2) & (location != [])):
        print "old quicklook exists"
               
        contained = CheckLocation(radarsatfile, location)
    elif (location != []):
        #Create Quicklook from which area is determined (not very good solution)
        print 
        print "quicklook to be created"
        print 
        outputfile = CreateQuicklook(radarsatfile)
        if outputfile == None:
            continue
    
        contained = CheckLocation(radarsatfile, location)
       
    
    #Check if file contains parts of Area Of Interest
    #contained = ExtractRadarsat(radarsatfile, location)
    
    #If not within Area Of Interest
    if ((location != []) & (contained == False)):
        print         
        print radarsatfile + ' skipped'    
        print 
        continue
        
    print 
    print 'Processing ', radarsatfile 
    print 
    
    #Process image
    ProcessNest(radarsatfile, outputfilepath, location)
    
    #Remove quicklook as jpeg no available
    #try:
    #    os.remove(outputfile)
    #except:
    #    pass

print 'finished extracting Barents images'

#Done