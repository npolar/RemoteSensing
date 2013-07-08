# -*- coding: utf-8 -*-
"""
Created on Thu Jul 03 2013

Extracts Radarsat sathav scenes containing a selected point geographical point.
The point (svalbard_x, svalbard_y) is searched in the EPSG3575 quicklooks

Steps:
Extract files including the location
ExtractRadarsat()

Geocode with gdalwarp
GeocodeGdalwarp(svalbardlist)

Geocode and Process with NEST
ProcessNest(svalbardlist)




@author: max
"""



import zipfile, glob, os, shutil, gdal, fnmatch

def ExtractRadarsat():
    '''
    Goes through EPSG3575 quicklooks and writes matching point to textfile
    or copies them to specfied folder
    
    '''
    
    #Point to be included in image
    #svalbard_x = 60000.0        #Values in EPSG3575
    #svalbard_y = -1234000.0      #Values in EPSG3575  
    
    #Inglefieldbukta
    svalbard_x = 210000.0
    svalbard_y = -1304000.0
    svalbard2_x = 233000.0
    svalbard2_y = -1304000.0
    
    #If results to be copied this is destinationfolder
    destinationfolder = 'F:\\Gunnar\\'
    
    #List of quicklooks in folder
    #filelist = glob.glob(r'C:\Users\max\Documents\trash\*.zip')
    filelist = glob.glob(r'Z:\Radarsat\Sathav\2013\03_Mars\*EPSG3575.tif')
    
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
        
        #  check if svalbard_x, svalbard_y contained in image
        #if upperleft_x < svalbard_x < lowerright_x:
        #    if upperleft_y >  svalbard_y > lowerright_y:
                
        #Two points in Inglefieldbukta
        if ((upperleft_x < svalbard_x < lowerright_x) and (upperleft_x < svalbard2_x < lowerright_x)):
            if ((upperleft_y >  svalbard_y > lowerright_y) and (upperleft_y >  svalbard2_y > lowerright_y)):
                
                
                #Find pixel for svalbard_x and svalbard_y to see if NaN being 0 in quicklook
                svalbard_x_col = int((svalbard_x - upperleft_x) / pixelwidth)
                svalbard_y_row = int((svalbard_y - upperleft_y) / pixelwidth)
                if (raster[svalbard_y_row, svalbard_x_col] == 0):
                    continue
                
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

def GeocodeGdalwarp(svalbardlist):
    '''
    takes matching results from svalbardlist and geocodes them with gdalwarp
    Results for Svalbard not perfect, uncertainty 100-200 meters
    '''
    
    for svalbardfile in svalbardlist:
        
        #Paths and filenames        
        (svalbardfilepath, svalbardfilename) = os.path.split(svalbardfile)             
        (svalbardfileshortname, extension) = os.path.splitext(svalbardfilename)        
        svalbardzipfile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '.zip'
        
        #Define names of input and outputfile
        #gdalsourcefile = infilepath + '\\' + infileshortname + '\\imagery_HH.tif'
        gdalsourcefile = svalbardfilepath + '\\' + svalbardfileshortname[0:-9] + '\\product.xml'
        outputfilename = 'F:\\Jack\\' +  svalbardfileshortname[0:-9] + '_EPSG32633.tif'
        
          
        
        #Extract zipfile
        zfile = zipfile.ZipFile(svalbardzipfile, 'r')
        print    
        print "Decompressing image for " + svalbardfilename + " on " + svalbardfilepath    
        
        zfile.extractall(svalbardfilepath)
                
     
        #Call gdalwarp
        print
        print "map projecting file"
        print
        
        # -te contains extension of resulting file, see http://www.gdal.org/gdalwarp.html        
        #os.system('gdalwarp -tps -te 363100 8460000 870000 8850000 -t_srs \"+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )  
        os.system('gdalwarp -tps -te 410000 8720000 480000 8780000 -t_srs \"+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\" ' + gdalsourcefile + ' ' + outputfilename )
        
        #Remove folder where extracted and temporary files are stored
        shutil.rmtree(svalbardfilepath + '\\' + svalbardfileshortname[0:-9] )
    
        #Close zipfile
        zfile.close()
    

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
        outputfilename = 'F:\\Gunnar\\' +  svalbardfileshortname[0:-9] + '_Cal_Spk_TC_EPSG32633.dim'
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
        print "if terraincorrect, this may take some time per image (> 1h)..."
        
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
    
    sourcefolder = 'F:\\Gunnar\\'  
    #recursive compiling file list
    filelist = []
    for root, dirnames, filenames in os.walk(sourcefolder):
        for filename in fnmatch.filter(filenames, '*.img'):
            filelist.append(os.path.join(root, filename))
    
    print filelist
    
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
        
        #Convert from BEAM-DIMAP to GeoTIFF
        #os.system("gdal_translate -of GTiff " + sourcefile + " " +  destinationfile)
        
        #Use this one for BEAM-DIMAP to GeoTIFF with subsetting
        #Kongsvegen, Holtedalfonne
        #os.system("gdal_translate -of GTiff -projwin 419775 8805374 471689 8737941 " + sourcefile + " " +  destinationfile)
        
        #Inglefieldbukta        
        os.system("gdal_translate -of GTiff -projwin 565000 8750000 727000 8490000 " + sourcefile + " " +  destinationfile)
        
        
###############################
# CORE OF PROGRAM FOLLOWS HERE 
###############################


#Extract matching images
svalbardlist = ExtractRadarsat()

#Geocode with gdal
#GeocodeGdalwarp(svalbardlist)

#Geocode and Process with Nest
ProcessNest(svalbardlist)

ConvertENVItoGEOTIFF()



   
#End
    
    