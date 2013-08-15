# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
Then calibrate and project image to EPSG:3031 as GeoTIFF and JPG
The point (svalbard_x, svalbard_y) is searched in the EPSG3575 quicklooks

THIS VERSION FOR DRONNING MAUD LAND

Steps (more details in each function):
    
RadarsatDetailedQuicklook
- Creates a rough quicklook
- subsequently only used to get coordinates and projection
- better way for this needed in future version

ExtractRadarsat
- taken out for now
- meant to extract specigic images based on location

ProcessNest(svalbardlist)
- Geocode and Process with NEST
- Convert NEST format toGEOTIFF
- Reprojectfrom 3033 To3031
- needed because NEST only can project to ESPG3033

Requirements to run this code see:
http://geoinformaticstutorial.blogspot.no/2013/03/installing-python-with-gdal-on-windows.html


@author: max
"""



import zipfile, glob, os, shutil

def RadarsatDetailedQuicklook(radarsatfile):
    
    #Split names and extensions
    (infilepath, infilename) = os.path.split(radarsatfile)
    (infileshortname, extension) = os.path.splitext(infilename)
    
    #Open zipfile
    zfile = zipfile.ZipFile(radarsatfile, 'r')
    print    
    print "Decompressing image for " + infilename + " on " + infilepath    
    

    #zfile.extract(imagefile, infilepath)  
    zfile.extractall(infilepath)
    
    #Define names
    #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
    gdalsourcefile = infilepath + '\\' + infileshortname + '\\product.xml'
    outputfilename = infilepath + '\\' + infileshortname + '_EPSG3031.tif'
    browseimage = infilepath + '\\' + infileshortname + '_EPSG3031.tif'
    
    #Call gdalwarp
    print
    print "map projecting file"
    print
    os.system('gdalwarp -tps  -t_srs \"+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs \" ' + gdalsourcefile + ' ' + outputfilename )  
    
    
    #Call gdaltranslate to downsample and overwrite the original file 
    print
    print "downsampling file"
    print
    os.system('gdal_translate -ot byte -outsize 8% 8% -scale 0 30000 0 255 ' + outputfilename + ' ' + browseimage )

    #Remove folder where extracted and temporary files are stored
    shutil.rmtree(infilepath + '\\' + infileshortname )

    #Close zipfile
    zfile.close()
    
    #return name of quicklookfile so that it can be deleted at the end
    return outputfilename    
    
    

def ProcessNest(radarsatfile):
    '''
    Calls Nest SAR Toolbox to calibrate, map project and if wanted 
    terraincorrect images
    see http://nest.array.ca/
    
    needed Nest files at https://github.com/npolar/RemoteSensing/tree/master/Nest
    
    Map projection Svalbard EPSG:32633 UTM 33N
    Map Projection Barents Sea EPSG:3575
    Map Projection DML EPSG:3033 --> EPSG:3031 is wanted but NEST error using this
    '''
    

    
    #Various file paths and names:    
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)             
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename) 
    
    #Define names of input and outputfile
    gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
    outputfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3033.dim'
    
    #Extract the zipfile
    zfile = zipfile.ZipFile(radarsatfile, 'r')
    print    
    print "Decompressing image for " + radarsatfile + " on " + radarsatfilepath    
    
    zfile.extractall(radarsatfilepath)
    
 
    
    #Call NEST routine
    print
    print "calibration and speckle and SARSIM"
    print
    print "inputfile " + radarsatfileshortname
    print "outputfile " + outputfile
    print
    print 
    print "takes around 10 minutes."
    print
    
    #check that xml file is correct!
    
    #Process using NEST
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_reproj_LinDB_DML.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
            
    
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
        destinationfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3033_' + polarisation + '.tif'
        #auxfile is created automatically by NEST, name defined to remove it        
        auxfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3033_' + polarisation + '.tif.aux.xml'
        destinationfile2 = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '.tif'
        jpegfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '.jpg'
        
        print
        print 'Converting: '
        print '\nfrom ' + envifile
        print '\nto ' + destinationfile
        
        
        #Convert to GeoTIFF
        os.system("gdal_translate -a_nodata None -a_srs EPSG:3033 -of GTiff " + envifile + " " +  destinationfile)
        
        #Reproject to EPSG 3031
        os.system("gdalwarp -s_srs EPSG:3033 -t_srs \"+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs \" -srcnodata none -dstnodata 999.0 " + destinationfile + " " +  destinationfile2)
        
        #Create JPG
        os.system("gdal_translate -scale -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
        #Remove original GeoTIFF in 3033 since we now have 3031
        os.remove(destinationfile)
        os.remove(auxfile)
    
    #Remove BEAM-DIMAP files from NEST    
    shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    
    
        
        
#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
filelist = glob.glob(r'Z:\Radarsat\2013\RS2_20130815*.zip')


#Loop through filelist and process
for radarsatfile in filelist:
    
    #Create Quicklook from which area is determined (not very good solution)
    outputfile = RadarsatDetailedQuicklook(radarsatfile)
    
    print radarsatfile + ' processed'
    #Process image
    ProcessNest(radarsatfile)
    
    #Remove quicklook as jpeg now available as quicklook
    os.remove(outputfile)

print 'finished extracting DML images'


#End
    
    