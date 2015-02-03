# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
Then calibrate and project image to EPSG:3031 as GeoTIFF and JPG

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

ISSUES AT PRESENT:
- better way to get corner coordinates
- two no data values in GeoTIFF and JPG due to reprojecting twice
- solve NEST reprojection issue (does not do all)

@author: max
"""



import zipfile, glob, os, shutil, gdal, fnmatch, pyproj, gdalconst, osr


def ProcessNest(radarsatfile, Terraincorrection):
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
    if Terraincorrection == 'YES':
        outputfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031.dim'
    else:
        outputfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3033.dim'
    
    
    #Extract the zipfile
    zfile = zipfile.ZipFile(radarsatfile, 'r')
    print    
    print "Decompressing image for " + radarsatfile + " on " + radarsatfilepath    
    
    zfile.extractall(radarsatfilepath)
    
 
    
    #Call NEST routine
    print
    print "Terrain Correction"
    print
    print "inputfile " + radarsatfileshortname
    print "outputfile " + outputfile
    print
    print 
    print "takes around 10 minutes."
    print
    
    #check that xml file is correct!
    
    if "SLC" in radarsatfile:
        SLC == 'YES'
    else:
        SLC == 'NO'
        
    #Process using NEST
    #os.system(r'gpt C:\Users\max\Desktop\Calib_Spk_reproj_LinDB_Barents3031TEST.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    #TERRAIN CORRECTION:    
    if  Terraincorrection == 'YES':
        
        if "_U" in radarsatfile:
            os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_GETASSE_Ultrafine_LinDB_DML.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
        if "_SC" in radarsatfile:                
            os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_LinDB_DML.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
        if "_F" in radarsatfile:
            if SLC == 'YES':
                os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\ML_Calib_Spk_TC_GETASSE_FINE_LinDB_DML.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )

            else:
                os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_GETASSE_FINE_LinDB_DML.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    else:
        if SLC == 'YES':
            os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\ML_Calib_Spk_reproj_DML.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
        else:
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
        destinationfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '.tif'
        #auxfile is created automatically by NEST, name defined to remove it        
        auxfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '.tif.aux.xml'
        destinationfile2 = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '.tif'
        jpegfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '.jpg'
        
        #jpegsmallfile = radarsatfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_TC_EPSG3031_' + polarisation + '_SMALL.jpg'
        
        print
        print 'Converting: '
        print '\nfrom ' + envifile
        print '\nto ' + destinationfile
        
        
        #Convert to GeoTIFF
        os.system("gdal_translate -a_srs EPSG:3031 -stats -of GTiff " + envifile + " " +  destinationfile)
        #Build overviews
        #os.system("gdaladdo -r NEAREST -ro " + destinationfile + " 2 4 8 16 32 64")  #Build overviews
        
        #Create JPG
        os.system("gdal_translate -scale -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile + " " +  jpegfile) 
        os.system("gdaladdo -r NEAREST -ro " + jpegfile + " 2 4 8 16 32 64")  #Build overviews
        
        #Create small jpeg
        #os.system("gdal_translate -outsize 8% 8% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile)
        

        
    #Remove BEAM-DIMAP files from NEST    
    shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    
    
        
        
#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
#Terraincorrection = 'YES'
Terraincorrection = 'NO'



filelist = glob.glob(r'G:\satellittdata\DML\RS2*.zip')

#Loop through filelist and process
for radarsatfile in filelist:
    
   
    print 'processing ', radarsatfile 
    #Process image
    ProcessNest(radarsatfile, Terraincorrection)
    
    #Remove quicklook as jpeg now available as quicklook
    try:
        os.remove(outputfile)
    except:
        pass
    
print 'finished extracting DML images'


#End
    
    