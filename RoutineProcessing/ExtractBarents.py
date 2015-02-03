# -*- coding: utf-8 -*-
"""
Created on August 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
Then calibrate and project image to EPSG:3575 as GeoTIFF and JPG

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
- ideally scenes containing Svalbard should be terraincorrected
- Svalbard area usually has EPSG32633 and Barents EPSG 3575
"""

import zipfile, glob, os, shutil, gdal, fnmatch, pyproj, gdalconst, osr
import xml.etree.ElementTree as ET
import Tkinter, tkFileDialog

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
    RS2_upperleftEPSG4326_x = float(longitude_list[0])
    RS2_upperleftEPSG4326_y = float(latitude_list[0])
    RS2_lowerrightEPSG4326_x = float(longitude_list[-1])
    RS2_lowerrightEPSG4326_y = float(latitude_list[-1])
    
     
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
            
    #Divide filename    
    radarsatfilepath, radarsatfilename, radarsatfileshortname, extension = splitfilepath(radarsatfile)      
        
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
    #shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname )

    #Close zipfile
    zfile.close()
    
    #############################################
    # Convert DIM to GEOTIFF and JPEG
    #############################################

    #Get *.img files in dim-folder
    (outputfilenamepath, outputfilename) =  os.path.split(outputfile)
    (outputfileshortname, extension) = os.path.splitext(outputfilename)
    dim_datafolder = outputfilenamepath + '//' + outputfileshortname + '.data'
    if radarsatfileshortname[0:3] == 'RS2':
        dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/Sigma*.img'
    if radarsatfileshortname[0:2] == 'S1':  #Once Sentinel can be calibrated, both will be Sigma*.img
        dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/Amplitude*.img'
    dimlist = glob.glob(dim_datafile)
    
    #Loop through Sigma*.img files and convert to GeoTIFF and JPG
    for envifile in dimlist:
        if radarsatfileshortname[0:3] == 'RS2':
            polarisation = envifile[-9:-7]
        if radarsatfileshortname[0:2] == 'S1':    
            polarisation = envifile[-6:-4]
            
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
            if radarsatfileshortname[0:3] == 'RS2':
                os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of GTiff -projwin " + str(upperleft_x)  + " " + str(upperleft_y)  + " " + str(lowerright_x)  + " " + str(lowerright_y)  + " " + destinationfile2 + " " +  destinationfile3)
        
            if radarsatfileshortname[0:2] == 'S1': 
                os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of GTiff -projwin " + str(upperleft_x)  + " " + str(upperleft_y)  + " " + str(lowerright_x)  + " " + str(lowerright_y)  + " " + destinationfile2 + " " +  destinationfile3)
          
            #Convert to JPG
            print
            print "create jpeg scene"
            print
            if radarsatfileshortname[0:3] == 'RS2':
                os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile3 + " " +  jpegfile3) 
        
            if radarsatfileshortname[0:2] == 'S1': 
                os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile3 + " " +  jpegfile3) 
        else:
            
            #Convert to JPG
            print
            print "create jpeg scene"
            print
            if radarsatfileshortname[0:3] == 'RS2':
                os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
            if radarsatfileshortname[0:2] == 'S1': 
                os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
        #Create small jpeg --- THESE ARE CREATED FOR FIELD WORK TRANSFER ONLY DURING FIELD WORK
        #os.system("gdal_translate -outsize 40% 40% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile)
        #os.system("gdal_translate -outsize 10% 10% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile2)
        #os.system("gdal_translate -outsize 20% 20% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile3)
        os.system("gdal_translate -outsize 30% 30% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile4)
        #os.system("gdal_translate -outsize 50% 50% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile5)
        
        #Create small jpeg --- THESE ARE CREATED FOR FIELD WORK TRANSFER ONLY DURING FIELD WORK
        #os.system("gdal_translate -ot Int16 -co COMPRESS=DEFLATE -co PREDICTOR=2 -co ZLEVEL=9 -outsize 40% 40% -of GTiff " + destinationfile2 + " " + tiffsmallfile)
        #os.system("gdal_translate -outsize 10% 10%  -of GTiff " + destinationfile2 + " " + tiffsmallfile2)
        #os.system("gdal_translate -outsize 20% 20%  -of GTiff " + destinationfile2 + " " + tiffsmallfile3)
        #os.system("gdal_translate -outsize 30% 30%  -of GTiff " + destinationfile2 + " " + tiffsmallfile4)
    
        #Remove original GeoTIFF in 3033 since we now have 3575        
        try:
            os.remove(destinationfile)
        except:
            pass
        
        #os.remove(auxfile)
    

    #Clean up temp files    
    
    try:
        shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname + '.SAFE')
    except:
        pass

    try:
        shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname )
    except:
        pass   
    
    #shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)

root = Tkinter.Tk()
root.attributes("-topmost", True)  #puts window on top of Spyder
root.withdraw() #use to hide tkinter window

#currdir = os.getcwd()
currdir = 'G:\\satellittdata\\flerbrukBarents'  #start search at standard directory
inputfilepath = tkFileDialog.askdirectory(parent=root, initialdir=currdir, title='Please select a input directory containing SAR scenes')
outputfilepath = tkFileDialog.askdirectory(parent=root, initialdir=currdir, title='Please select a output directory')

#inputfilepath =  'G:\\satellittdata\\flerbrukBarents'
#outputfilepath = 'G:\\satellittdata\\flerbrukBarents'

filelist = []
for root, dirnames, filenames in os.walk(inputfilepath):
  for filename in fnmatch.filter(filenames, 'RS*.zip'):
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
    if location != []:
        print        
        print "check location"
        print 
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