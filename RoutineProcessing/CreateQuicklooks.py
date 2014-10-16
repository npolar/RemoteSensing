# -*- coding: utf-8 -*-
"""
Creates Quicklooks from zipped Sentinel-1 or Radarsat-2 files
"""

import zipfile, glob, os, shutil, gdal, fnmatch, pyproj, gdalconst, osr


    
def CreateQuicklook(radarsatfile, outputfilepath):
    '''

    '''
            
    #Various file paths and names:    
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)             
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)        
        
    #Define names of input and outputfile
        
    if radarsatfileshortname[0:3] == 'RS2':  # RADARSAT-2
        gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
        nestfilename = 'Spk_reproj_Barents.xml'
    if radarsatfileshortname[0:2] == 'S1':   # SENTINEL-1
        gdalsourcefile = radarsatfilepath  +  '\\' + radarsatfileshortname + '.safe' + '\\' + 'manifest.safe'
        nestfilename = 'Spk_reproj_Barents.xml'
  
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
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\\' + nestfilename + ' -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
    #Close zipfile
    zfile.close()
    
    #############################################
    # Convert DIM to GEOTIFF and JPEG
    #############################################

    #Get *.img files in dim-folder
    (outputfilenamepath, outputfilename) =  os.path.split(outputfile)
    (outputfileshortname, extension) = os.path.splitext(outputfilename)
    dim_datafolder = outputfilenamepath + '//' + outputfileshortname + '.data'
    dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/Amplitude*.img'
    dimlist = glob.glob(dim_datafile)
    
    #Loop through Sigma*.img files and convert to GeoTIFF and JPG
    for envifile in dimlist:
        polarisation = envifile[-6:-4]
        destinationfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_temp.tif'
        #auxfile is created automatically by NEST, name defined to remove it       
        auxfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif.aux.xml'
        destinationfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        jpegfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.jpg'


        print
        print 'Converting to GeoTIFF: '
        print '\nfrom ' + envifile
        print '\nto ' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        
 
        os.system("gdal_translate -a_srs EPSG:3575 -stats -of GTiff  " + envifile + " " +  destinationfile2)
                    
        

            
        #Convert to JPG
        print
        print "create jpeg scene"
        print
        if radarsatfileshortname[0:3] == 'RS2':
             os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
        if radarsatfileshortname[0:2] == 'S1': 
            os.system("gdal_translate -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        #Remove original GeoTIFF in 3033 since we now have 3575        
        try:
            os.remove(destinationfile)
        except:
            pass
        
        try:
            os.remove(auxfile)
        except:
            pass
        
        try:
            os.remove(destinationfile2)
        except:
            pass
    #Remove BEAM-DIMAP files from NEST      
    
    try:
        shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname + '.SAFE')
    except:
        pass

    try:
        shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname )
    except:
        pass   
    
    shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)
inputfilepath =  'G:\\satellittdata\\flerbrukBarents'
outputfilepath = 'G:\\satellittdata\\flerbrukBarents'

filelist = []
for root, dirnames, filenames in os.walk(inputfilepath):
  for filename in fnmatch.filter(filenames, '*.zip'):
      filelist.append(os.path.join(root, filename))


#Loop through filelist and process
for radarsatfile in filelist:
    
    #Check if quicklook exists and contains area
    #Get Filename of corresponding quicklook for radarsatfile
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)   
   
    
    print 
    print 'Processing ', radarsatfile 
    print 
    
    #Process image
    CreateQuicklook(radarsatfile, outputfilepath)
    

print 'finished Creating Quicklooks'

#Done