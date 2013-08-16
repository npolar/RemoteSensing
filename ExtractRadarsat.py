# -*- coding: utf-8 -*-
"""
Created on Thu Jul 19 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
The point (svalbard_x, svalbard_y) is searched in the EPSG3575 quicklooks

Steps (more details in each function):

ExtractRadarsat()
- Use if only images from a specific location wanted
- Extract files including the location from the EPSG3575 quicklooks
- is faster using these quicklooks, no zip extraction needed


ProcessNest(svalbardlist)
- Geocode and Process with NEST

ConvertNESTtoGEOTIFF

Requirements to run this code see:
http://geoinformaticstutorial.blogspot.no/2013/03/installing-python-with-gdal-on-windows.html


@author: max
"""



import zipfile, glob, os, shutil, gdal, fnmatch

def ExtractRadarsat():
    '''
    USE IF ONLY SCENES FROM SPECIFIED LOCATION WANTED

    Goes through EPSG3575 quicklooks and writes matching RS-2 files containing 
    wanted location to textfile or copies them to specfied folder
    
    Uses the existing quicklooks to match point, NOT the zipped RS-2 file
    since it takes longer time to extract the zip files.
    
    If no quicklooks exist, run RadarsatDetailedQuicklook.py
    
    '''
    
    #############################################
    # ADD POINT(S) WHOSE MATCHING IMAGE YOU NEED
    #############################################
    
    #Holtedalfonne
    #svalbard_x = 60000.0        #Values in EPSG3575
    #svalbard_y = -1234000.0      #Values in EPSG3575
    #svalbard2_x = 86000.0        #Values in EPSG3575
    #svalbard2_y = -1215000.0      #Values in EPSG3575
    
    #Inglefieldbukta
    svalbard_x = 210000.0
    svalbard_y = -1304000.0
    svalbard2_x = 250000.0
    svalbard2_y = -1396000.0

    #If results to be copied this is destinationfolder
    destinationfolder = 'C:\\Users\\max\\Documents\\Gunnar\\'
    
    #List of quicklooks in folder
    #filelist = glob.glob(r'C:\Users\max\Documents\trash\*.zip')
    filelist = glob.glob(r'Z:\Radarsat\Sathav\2012\12_December\*EPSG3575.tif')
    
    #list containing matching images
    svalbardlist = []
    
  
    #Loop through zipfiles, extract and create list with Svalbard files
    
    for radarsatfile in filelist:
        
        #Open GeoTiff Quicklook
        driver = gdal.GetDriverByName('GTiff')
        driver.Register()
        dataset = gdal.Open(radarsatfile, gdal.GA_ReadOnly)
        band = dataset.GetRasterBand(1)
        raster = band.ReadAsArray()
        
        
        
        
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
        
     
        
        #Textfile to receive list of matching files
        filename = destinationfolder + 'selectedSAR.txt'
        
               
        #Check if two points are contained in image
        if ((upperleft_x < svalbard_x < lowerright_x) and (upperleft_x < svalbard2_x < lowerright_x)):
            if ((upperleft_y >  svalbard_y > lowerright_y) and (upperleft_y >  svalbard2_y > lowerright_y)):
                
                # point may be in image but in NAN area
                #Find pixel for svalbard_x and svalbard_y to see if NaN being 0 in quicklook
                svalbard_x_col = int((svalbard_x - upperleft_x) / pixelwidth)
                svalbard_y_row = int((svalbard_y - upperleft_y) / pixelwidth)
                if (raster[svalbard_y_row, svalbard_x_col] == 0):
                    continue
                
                #Find pixel for svalbard2_x and svalbard2_y to see if NaN being 0 in quicklook
                svalbard2_x_col = int((svalbard2_x - upperleft_x) / pixelwidth)
                svalbard2_y_row = int((svalbard2_y - upperleft_y) / pixelwidth)
                if (raster[svalbard2_y_row, svalbard2_x_col] == 0):
                    continue
                
                #If image matches location, append to list
                svalbardlist.append(radarsatfile)
                print ' matches: ', radarsatfile
                #append matching file to textfile            
                f = open(filename, 'a')
                f.write(radarsatfile + " \n")
                f.close()
                
                #COPY THE MATCHING FILES TO OTHER FOLDER
                #Get filenames
                #(radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
                #radarsatsourcefile = radarsatfilepath + '\\' + radarsatfilename[0:-13] + '.zip'
                #destinationfile = destinationfolder + '\\' + radarsatfilename[0:-13] + '.zip'
                #Copy the zip file
                #shutil.copyfile(radarsatsourcefile, destinationfile)
        
                
        dataset = None
        raster = None
        
    #end for    
    
    return(svalbardlist)


def ProcessNest(svalbardlist):
    '''
    Calls Nest SAR Toolbox to calibrate, map project and if wanted 
    terraincorrect images
    see http://nest.array.ca/
    
    needed Nest files at https://github.com/npolar/RemoteSensing/tree/master/Nest
    
    Map projection Svalbard EPSG:32633 UTM 33N
    Map Projection Barents Sea EPSG:3575
    '''
    
    for svalbardfile in svalbardlist:
        
        #Various file paths and names:    
        (svalbardfilepath, svalbardfilename) = os.path.split(svalbardfile)             
        (svalbardfileshortname, extension) = os.path.splitext(svalbardfilename)        
        svalbardzipfile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '.zip'
        
        #Define names of input and outputfile
        #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
        gdalsourcefile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '\\product.xml'
        #outputfilename = 'F:\\Gunnar\\' +  svalbardfileshortname[0:-9] + '_Cal_Spk_TC_EPSG32633.dim'
        outputfilename = 'C:\\Users\\max\\Documents\\Gunnar\\' +  svalbardfileshortname[0:-9] + '_Cal_Spk_TC_EPSG32633.dim'

        #outputfilename = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_Cal_Spk_SARSIM_EPSG32633.dim'
        
        
        #Extract the zipfile
        zfile = zipfile.ZipFile(svalbardzipfile, 'r')
        print    
        print "Decompressing image for " + svalbardfilename + " on " + svalbardfilepath    
        
        zfile.extractall(svalbardfilepath)
        
     
        
        #Call NEST routine
        print
        print "calibration and speckle and SARSIM"
        print
        print "inputfile " + svalbardfileshortname[0:-9]
        print "outputfile " + outputfilename
        print
        print "if SARSIM terraincorrect, this may take some time per image (> 1h)..."
        print "if Range Doppler terraincorrect, around 10 minutes."
        print
        
        #check that xml file is correct!
        
        #This one for sea ice -- calibration and map projection
        #os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_reproj_RS2.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfilename1 + '"' )
        #os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_SarsimTC_LinDB_RS2.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfilename2 + '"' )
        
        #This one for Range Doppler Correction
        os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_TC_LinDB_RS2.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfilename + '"' )
                
        
        #Remove folder where extracted and temporary files are stored
        shutil.rmtree(svalbardfilepath + '\\' + svalbardfileshortname[0:-9] )
    
        #Close zipfile
        zfile.close()
        
    print   
    print 'Done'

def ConvertENVItoGEOTIFF():
    '''
    Nest cannot export as GeoTIFF at present.
    The Beam-Dimap images contain raster with "sigma*.img" names
    This routines renames them to RS-2 file name and converts to GeoTIFF
    '''
    
    #Folder containing the Beam-DIMAP files
    #sourcefolder = 'F:\\Gunnar\\'  
    sourcefolder = 'C:\\Users\\max\\Documents\\Gunnar\\'
    #recursive checking and compiling file list
    filelist = []
    for root, dirnames, filenames in os.walk(sourcefolder):
        for filename in fnmatch.filter(filenames, '*.img'):
            filelist.append(os.path.join(root, filename))
    
    #Loop through filelist    
    for convertfile in filelist:
        
        #Various file paths and names:    
        (convertfilepath, convertfilename) = os.path.split(convertfile)             
        (convertfileshortname, extension) = os.path.splitext(convertfilename)
        (radarsatname) = os.path.basename(convertfilepath)    
        polarisation = convertfilename[7:-7]
        
        sourcefile = convertfile
        destinationfile = sourcefolder + radarsatname[0:-5] + '_' + polarisation + '.tif'
        
        print
        print 'Converting: '
        print '\nfrom ' + sourcefile
        print '\nto ' + destinationfile
        
        ####################################
        #Convert from BEAM-DIMAP to GeoTIFF
        ####################################
        
        #os.system("gdal_translate -of GTiff " + sourcefile + " " +  destinationfile)
        
        #Use this one for BEAM-DIMAP to GeoTIFF with subsetting
        #Kongsvegen, Holtedalfonne
        #os.system("gdal_translate -a_srs EPSG:32633 -stats -of GTiff -projwin 419775 8805374 471689 8737941 " + sourcefile + " " +  destinationfile)
        
        #Inglefieldbukta        
        os.system("gdal_translate -a_srs EPSG:32633 -stats -of GTiff -projwin 565000 8750000 727000 8490000 " + sourcefile + " " +  destinationfile)
        
def GeoTIFFtoJPEG():
           
    '''
    Convert GeoTIFF to JPEG
    Issue at present -- even though GeoTIFF only 999 as nodata-value, the jpg 
    contains two nodata values 0 and 255
    '''
     
    
    #filelist = glob.glob(r'C:\\Users\\max\\Documents\\Gunnar\\*.tif')
    filelist = glob.glob(r'Z:\Radarsat\Sathav\processed_images\Storfjorden\2012_12_December\*.tif')
    
    #Loop through filelist    
    for convertfile in filelist:
        
        #Various file paths and names:    
        (convertfilepath, convertfilename) = os.path.split(convertfile)             
        (convertfileshortname, extension) = os.path.splitext(convertfilename)
           
        
        
        sourcefile = convertfile
        destinationfile = convertfilepath + '\\' + convertfileshortname  + '.jpg'
        
        print
        print 'Converting: '
        print '\nfrom ' + sourcefile
        print '\nto ' + destinationfile
        
        ####################################
        #Convert from BEAM-DIMAP to GeoTIFF
        ####################################
        
        # a_srs needs to set projection since info missing in img files
        #os.system("gdal_translate -of GTiff " + sourcefile + " " +  destinationfile)
        
        #Use this one for BEAM-DIMAP to GeoTIFF with subsetting
        #Kongsvegen, Holtedalfonne
        #os.system("gdal_translate -of GTiff -projwin 419775 8805374 471689 8737941 " + sourcefile + " " +  destinationfile)
        
        #DML        
        os.system("gdal_translate -scale -ot Byte -co WORLDFILE=YES -of JPEG " + sourcefile + " " +  destinationfile) 
        
        
        #THIS DOES NOT WORK FOR JPG; CANNOT UPDATE WITH JPG DRIVER
        #driver = gdal.GetDriverByName('JPEG')
        #driver.Register()
        #dataset = gdal.Open(destinationfile, gdal.GA_Update)
        #band = dataset.GetBand(1)
        #raster = band.ReadAsArray()
        #raster[raster == 0] = 255
        #band.WriteArray(raster)
        #band.FlushCache()
        
        #band = None
        #dataset = None
        
        #dataset.SetProjection(projection)

        
###############################
# CORE OF PROGRAM FOLLOWS HERE 
###############################


#Extract matching images
svalbardlist = ExtractRadarsat()

#Geocode and Process with Nest
ProcessNest(svalbardlist)

ConvertENVItoGEOTIFF()

GeoTIFFtoJPEG()

print
print "Done"

   
#End
    
    