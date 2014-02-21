# -*- coding: utf-8 -*-
"""
Created on Wed Feb 05 08:14:28 2014

@author: max

Creates map projected quicklooks from ERS /ASAR files

"""
import  os, fnmatch

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
    gdalsourcefile = envisatfile
    outputfilename = infilepath + '\\' + infilepath[-40:-7] + 'temp_EPSG32633.tif'
    
    #split the filepath to create the outputpath for the browseimage
    split = envisatfile.split("\\")
    
    browseimage = split[0] + '\\' + split[1] + "\\" + split[2] + "\\" + split[3] + "\\" + infilepath[-40:-7] + '_EPSG32633.jpg'
    
    #Call gdalwarp and map project the file
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs EPSG:32633 ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate to create a smaller jpeg quicklook
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
    
    #Split names and extensions
    (infilepath, infilename) = os.path.split(envisatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Define names
    gdalsourcefile = envisatfile
    outputfilename = infilepath + '\\' + infileshortname + 'temp_EPSG32633.tif'
    
    #split the filepath to create the outputpath for the browseimage
    split = envisatfile.split("\\")
    
    browseimage = split[0] + '\\' + split[1] + "\\" + split[2] + "\\" + split[3] + "\\" + infileshortname + '_EPSG32633.jpg'
    
    #Call gdalwarp and map project the file
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs EPSG:32633 ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate to create a smaller jpeg quicklook   
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


#Loop through filelist and process
for envisatfile in filelist_CEOS:
    outputfile = EnvisatERSDetailedQuicklook_CEOS(envisatfile)
    if outputfile == None:
        continue

for envisatfile in filelist_E1E2:        
    outputfile = EnvisatERSDetailedQuicklook_E1E2(envisatfile)
    if outputfile == None:
        continue
    
print 'finished extracting Svalbard images'

#Done