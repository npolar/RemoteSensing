# -*- coding: utf-8 -*-
"""
Created on Wed Feb 05 08:14:28 2014

@author: max
"""
import zipfile, glob, os, shutil, gdal, fnmatch

def EnvisatERSDetailedQuicklook_CEOS(envisatfile):
    '''
    Takes the Radarsat-2 zipfile and creates a map projected quicklook from 
    the imagery_HH file
    '''
    
    ##### FIRST FOR CEOS FORMAT #####
    #Split names and extensions
    (infilepath, infilename) = os.path.split(envisatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = envisatfile
    outputfilename = infilepath + '\\' + infilepath[-40:-7] + 'temp_EPSG32633.tif'
    
    split = envisatfile.split("\\")
    
    browseimage = split[0] + '\\' + split[1] + "\\" + split[2] + "\\" + split[3] + "\\" + infilepath[-40:-7] + '_EPSG32633.jpg'
    
    #Call gdalwarp
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs EPSG:32633 ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate    
    print
    print "downsampling file"
    print
    os.system('gdal_translate -of JPEG -ot byte -outsize 20% 20% -scale 0 1000 0 255 ' + outputfilename + ' ' + browseimage )
    
    #Remove folder where extracted and temporary files are stored
    os.remove(outputfilename)
    
    #Close zipfile



    return browseimage


def EnvisatERSDetailedQuicklook_E1E2(envisatfile):
    '''
    Takes the Radarsat-2 zipfile and creates a map projected quicklook from 
    the imagery_HH file
    '''
    
    ##### FIRST FOR CEOS FORMAT #####
    #Split names and extensions
    (infilepath, infilename) = os.path.split(envisatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = envisatfile
    outputfilename = infilepath + '\\' + infileshortname + 'temp_EPSG32633.tif'
    
    split = envisatfile.split("\\")
    
    browseimage = split[0] + '\\' + split[1] + "\\" + split[2] + "\\" + split[3] + "\\" + infileshortname + '_EPSG32633.jpg'
    
    #Call gdalwarp
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs EPSG:32633 ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate    
    print
    print "downsampling file"
    print
    os.system('gdal_translate -of JPEG -ot byte -b 1 -outsize 20% 20% -scale 0 1000 0 255 ' + outputfilename + ' ' + browseimage )
    
    #Remove folder where extracted and temporary files are stored
    os.remove(outputfilename)
    
    #Close zipfile



    return browseimage
    

#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
#filelist = glob.glob(r'G:\\satellittdata\\SCNA\\RS2*.zip')
#filelist = glob.glob(r'G:\\Radarsat\\sathav\\2013\\10_October\\RS2*.zip')
filelist_CEOS = []
for root, dirnames, filenames in os.walk('Z:\\ERS_Envisat_SAR\\Arctic\\2005'):
  for filename in fnmatch.filter(filenames, 'DAT_01.001'):
      filelist_CEOS.append(os.path.join(root, filename))

filelist_E1E2 = []
for root, dirnames, filenames in os.walk('Z:\\ERS_Envisat_SAR\\Arctic\\2005'):
  for filename in fnmatch.filter(filenames, '*.E1'):
      filelist_E1E2.append(os.path.join(root, filename))      
for root, dirnames, filenames in os.walk('Z:\\ERS_Envisat_SAR\\Arctic\\2005'):
  for filename in fnmatch.filter(filenames, '*.E2'):
      filelist_E1E2.append(os.path.join(root, filename))  
for root, dirnames, filenames in os.walk('Z:\\ERS_Envisat_SAR\\Arctic\\2005'):
  for filename in fnmatch.filter(filenames, '*.N1'):
      filelist_E1E2.append(os.path.join(root, filename)) 

    
outputfilepath = 'C:\\Users\\max\\Documents\\processed_Envisat'


#outputfilepath = 'G:\\satellittdata\\processed_SCNA\\'


#Define Area Of Interest
#upperleft_x = 8000.0
#upperleft_y = -1010000.0
#lowerright_x = 350000.0
#lowerright_y = -1495000.0

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


#location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]

#Loop through filelist and process
for envisatfile in filelist_CEOS:
    outputfile = EnvisatERSDetailedQuicklook_CEOS(envisatfile)
    if outputfile == None:
        continue

for envisatfile in filelist_E1E2:        
    outputfile = EnvisatERSDetailedQuicklook_E1E2(envisatfile)
    if outputfile == None:
        continue
    
    
    
    
    
    #Check if file contains parts of Area Of Interest
       
    #contained = ExtractRadarsat(envisatfile, location)
    
    #If not within Area Of Interest
    #if contained == False:
    #    print envisatfile + ' skipped'
    #    continue
        
    #resolution = 50  #for SCWA
    ###Activate if only SCNA files wanted ###
    #skip file if SCWA
    #resolution = 20
    #if envisatfile[-37:-33] == 'SCWA':
    #    continue
        
    print envisatfile + ' processed'
    #Process image
    #ProcessNest(envisatfile, outputfilepath, location)
    

print 'finished extracting Svalbard images'

#Done