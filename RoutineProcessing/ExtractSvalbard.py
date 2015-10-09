# -*- coding: utf-8 -*-
"""
Created on August 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
Then calibrate and project image to EPSG:32633 (UTM33 WGS84) as GeoTIFF and JPG

Steps (more details in each function):
    
CheckLocation
- Reads Corners from product.xml
- checks if Area of Interest falls in image

ProcessNest(svalbardlist)
- Geocode and Process with NEST
- Convert NEST format toGEOTIFF
- Reprojectfrom polarstereo To3575
- needed because NEST only can project to ESPG3575

Requirements to run this code see:
http://geoinformaticstutorial.blogspot.no/2013/03/installing-python-with-gdal-on-windows.html

ISSUES AT PRESENT:
- two no data values in GeoTIFF and JPG due to reprojecting twice
- check if scene contains too much NAN
- ideally scenes containing Svalbard should be terraincorrected
- Svalbard area usually has EPSG32633 and Barents EPSG 3575
"""

import zipfile, glob, os, shutil, gdal, fnmatch, pyproj
import xml.etree.ElementTree as ET




def splitfilepath(inputfile):
    """
    takes input file and returns inputfilepath, inputfilename, inputfileshortname, extension
    """
     #Get Filename of corresponding quicklook for radarsatfile
    (inputfilepath, inputfilename) = os.path.split(inputfile)
    (inputfileshortname, extension) = os.path.splitext(inputfilename)
    
    return inputfilepath, inputfilename, inputfileshortname, extension

def CheckLocation(radarsatfile, location):
    " check of radarsatfile is within location"
    
    #Divide filename    
    radarsatfilepath, radarsatfilename, radarsatfileshortname, extension = splitfilepath(radarsatfile)
    
    #zipfile and check that it is ok
    try:
        zfile = zipfile.ZipFile(radarsatfile, 'r')
    except:
        outputfilename = None
        print radarsatfile, ' is corrupt.'
        print 'Writing to ', 'C:\Users\max\Desktop\corruptRS.txt'
        textfile = open( 'C:\Users\max\Desktop\corruptRS.txt', 'a')
        textfile.write(radarsatfile + '\n' )
        textfile.close()
        return outputfilename
    
    #Extract product.xml file from zipfile
    zfile.extract(radarsatfileshortname + '/product.xml', radarsatfilepath)

    zfile.close()
    
    #Read coordinates from product.xml    
    tree = ET.parse(radarsatfilepath + '//' + radarsatfileshortname + '//' + 'product.xml')
    root = tree.getroot()
    
    latitude_list = []
    for latitude in root.iter('{http://www.rsi.ca/rs2/prod/xml/schemas}latitude'):
         latitude_list.append(latitude.text)
    
    longitude_list = []
    for longitude in root.iter('{http://www.rsi.ca/rs2/prod/xml/schemas}longitude'):
         longitude_list.append(longitude.text)
    
    #upperleft is the first coordinate, lowerright the last in the list in product.xml     
    # QUICKFIX: THE LARGEST SMALLEST COORDINATE NEEDS TO BE THE CORNER!    
#    RS2_upperleftEPSG4326_x = float(longitude_list[0])
#    RS2_upperleftEPSG4326_y = float(latitude_list[0])
#    RS2_lowerrightEPSG4326_x = float(longitude_list[-1])
#    RS2_lowerrightEPSG4326_y = float(latitude_list[-1])
    
    RS2_upperleftEPSG4326_x = float(min(longitude_list))
    RS2_upperleftEPSG4326_y = float(max(latitude_list))
    RS2_lowerrightEPSG4326_x = float(max(longitude_list))
    RS2_lowerrightEPSG4326_y = float(min(latitude_list))
    
     
    AreaOfInterest_upperleft_EPSG32633_x = location[0]
    AreaOfInterest_upperleft_EPSG32633_y = location[1]
    AreaOfInterest_lowerright_EPSG32633_x = location[2]
    AreaOfInterest_lowerright_EPSG32633_y = location[3]
      
    #convert location to EPSG32633
    EPSG3575 = pyproj.Proj("+init=EPSG:3575")
    EPSG32633 = pyproj.Proj("+init=EPSG:32633") #UTM33
    EPSG4326 = pyproj.Proj("+init=EPSG:4326")
    
    AreaOfInterest_upperleft_EPSG4326_x, AreaOfInterest_upperleft_EPSG4326_y = pyproj.transform(EPSG32633, EPSG4326, AreaOfInterest_upperleft_EPSG32633_x, AreaOfInterest_upperleft_EPSG32633_y)
    AreaOfInterest_lowerright_EPSG4326_x, AreaOfInterest_lowerright_EPSG4326_y =pyproj.transform(EPSG32633, EPSG4326, AreaOfInterest_lowerright_EPSG32633_x, AreaOfInterest_lowerright_EPSG32633_y)
    
    
    #Check if two points are contained in image
    contained = False
    print RS2_upperleftEPSG4326_x, AreaOfInterest_upperleft_EPSG4326_x, RS2_lowerrightEPSG4326_x
    print RS2_upperleftEPSG4326_x, AreaOfInterest_lowerright_EPSG4326_x, RS2_lowerrightEPSG4326_x
    print RS2_upperleftEPSG4326_y, AreaOfInterest_upperleft_EPSG4326_y, RS2_lowerrightEPSG4326_y
    print RS2_upperleftEPSG4326_y, AreaOfInterest_lowerright_EPSG4326_y, RS2_lowerrightEPSG4326_y

    
    if ((RS2_upperleftEPSG4326_x < AreaOfInterest_upperleft_EPSG4326_x < RS2_lowerrightEPSG4326_x) and (RS2_upperleftEPSG4326_x < AreaOfInterest_lowerright_EPSG4326_x  < RS2_lowerrightEPSG4326_x)):
        
        if ((RS2_upperleftEPSG4326_y > AreaOfInterest_upperleft_EPSG4326_y > RS2_lowerrightEPSG4326_y) and (RS2_upperleftEPSG4326_y >  AreaOfInterest_lowerright_EPSG4326_y > RS2_lowerrightEPSG4326_y)):
            contained = True   
            print radarsatfilename, ' matches'
    
    shutil.rmtree(radarsatfilepath + '//' + radarsatfileshortname)
    
    return contained        
    
    
def ProcessNest(radarsatfile, outputfilepath, location, resolution):
    '''
    Calls Nest SAR Toolbox to calibrate, map project and if wanted 
    terraincorrect images
    see http://nest.array.ca/
    
    needed Nest files at https://github.com/npolar/RemoteSensing/tree/master/Nest
    
    converts afterwards to GeoTIFF and JPEG clipped to extents of Svalbard DEM
    
    Map projection Svalbard EPSG:32633 UTM 33N
    Map Projection Barents Sea EPSG:3575
    '''
            
    #Divide filename    
    radarsatfilepath, radarsatfilename, radarsatfileshortname, extension = splitfilepath(radarsatfile)       
        
    #Define names of input and outputfile
    gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
    outputfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG32633.dim'

    #Extract the zipfile
    try:
        zfile = zipfile.ZipFile(radarsatfile, 'r')
    except:
        print 'radarsatfile corrupted: ', radarsatfile
        print 'Writing to ', 'C:\Users\max\Desktop\corruptRS.txt'
        textfile = open( 'C:\Users\max\Desktop\corruptRS.txt', 'a')
        textfile.write(radarsatfile + '\n' )
        textfile.close()

        return
    print    
    print "Decompressing image for " + radarsatfilename
    print " on "
    print radarsatfilepath    
    
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
    if resolution == 50:
        os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_LinDB_RS2_dem50.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    elif resolution == 20:
        os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_LinDB_RS2_dem20.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    elif resolution == 25:
        os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_LinDB_RS2_dem25.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
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
    os.remove(outputfile)
    
    print   
       



#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################

year = 2015

while year <= 2015:
    
    # Define filelist to be processed (radarsat zip files)
    #filelist = glob.glob(r'G:\\satellittdata\\SCNA\\RS2*.zip')
    #filelist = glob.glob(r'G:\\Radarsat\\sathav\\2013\\10_October\\RS2*.zip')
    
    foldername = 'G:\\Radarsat\\flerbruksavtale\\ArcticOcean_Svalbard\\' + str(year) 
    #outputfilepath = 'G:\\Aavatsmarkbreen'
    outputfilepath = 'Z:\\Radarsat\\Flerbruksavtale\\processed_images\\Austfonna'
    
    print 'check ', year, foldername
    
    filelist = []
   
     
    for root, dirnames, filenames in os.walk(foldername):
      for filename in fnmatch.filter(filenames, 'RS2_20150*.zip'):
          filelist.append(os.path.join(root, filename))
    
    
    #DEFINE AREA OF INTEREST IN EPSG:32633
    #upperleft_x = 8000.0
    #upperleft_y = -1010000.0
    #lowerright_x = 350000.0
    #lowerright_y = -1495000.0
    
    #Austfonna
    upperleft_x = 651500.0
    upperleft_y =  8891000.0       
    lowerright_x = 740000.0        
    lowerright_y = 8800881.0     
    
    #Linnevatnet
    #upperleft_x = 466210.0
    #upperleft_y = 8668260.0
    #lowerright_x = 477220.0
    #lowerright_y = 8660340.0
    
    #Holtedalfonne
    #upperleft_x = 419726.0
    #upperleft_y =  8812000.0       
    #lowerright_x = 475000.0        
    #lowerright_y = 8737956.0    
    
    #Inglefieldbukta
    #upperleft_x = 564955.9196850983425975
    #upperleft_y = 8750041.7983950804919004 
    #lowerright_x = 726949.9692189423367381
    #lowerright_y = 8490034.1236895751208067
    
    #Wahlenbergbreen
    
    #upperleft_x = 462579.6007352703018114
    #upperleft_y= 8734288.4610685724765062
    #lowerright_x= 483506.7996030483045615
    #lowerright_y= 8708179.2891478203237057
    
    #Aavatsmark
    #upperleft_x = 430000.0
    #upperleft_y =  8755000.0       
    #lowerright_x = 463000.0        
    #lowerright_y = 8710000.0  
    
    
    location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]
    
    #Loop through filelist and process
    for radarsatfile in filelist:
        
        
        #resolution = 50  #for SCWA
        ###Activate if only SCNA files wanted ###
        #skip file if SCWA
        resolution = 50
        #if 'SCWA' in radarsatfile:
        #    continue
        
        #Check if quicklook exists and contains area
        #Get Filename of corresponding quicklook for radarsatfile
        (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
        (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)   
       
        existingquicklook = radarsatfilepath + '//' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_HH.jpg'
        print existingquicklook
        
        

           
        contained = CheckLocation(radarsatfile, location)
        
        #If not within Area Of Interest
        if contained == False:
            print os.path.split(radarsatfile)[1] + ' skipped'
            continue
            
           
        print os.path.split(radarsatfile)[1] + ' processed'
        #Process image
        ProcessNest(radarsatfile, outputfilepath, location, resolution)
            #Remove quicklook as jpeg no available
        try:
            os.remove(outputfile)
        except:
            pass
    
    year = year + 1

print 'finished extracting Svalbard images'

#Done