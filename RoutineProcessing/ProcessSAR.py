# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 08:48:44 2015

@author: max
"""
import os, fnmatch, pyproj, gdal, zipfile, glob, shutil, ogr
import xml.etree.ElementTree as etree  

def CheckLocation(sarfile, location, locationEPSG, outputfolder):
    """
    Checks of the area of interest defined by location is contained in sarfile
    sarfile is a map projected jpeg, the xml file containing the projection 
    needs to be in the same location as sarfile
    
    THIS VERSION FINALLY WITH INTERSECT OF POLYGONS OGR
    """

    
    #Various file paths and names:    
    (sarfilepath, sarfilename)    = os.path.split(sarfile)             
    (sarfileshortname, extension) = os.path.splitext(sarfilename)  
    
    #Get metadata dependent on satellite sensor
    if "RS2" in sarfile:
        #Path to product.xml-file within zipped Radarsat image
        xml_file = sarfileshortname + "/product.xml"
    if "S1A" in sarfile:
        #Path to product.xml-file within zipped Radarsat image
        xml_file = sarfileshortname + ".SAFE/preview/map-overlay.kml"

    #Path to product.xml file once extracted
    xml_file_extracted = outputfolder + "//" + xml_file     
    
    #Extract the zipfile
    print "Decompressing ", sarfile
    try:
        zfile = zipfile.ZipFile(sarfile, 'r')
        zfile.extract(xml_file, outputfolder )
        zfile.close()
    except:
        print "zipfile cannot open"
        contained = False
        return contained
        
    #Parse the xml file
    tree = etree.parse(xml_file_extracted)
    root = tree.getroot()
   
    #Access corners for Radarsat
    if "RS2" in sarfile:
        # Get rasterAttriute element and children (there is only one)
        for attributes in root.iter('{http://www.rsi.ca/rs2/prod/xml/schemas}rasterAttributes'):
            attribute_list = attributes.getchildren()
            
            #get child element containing lines/pixels and read
            for attribute in attribute_list:
                if attribute.tag == "{http://www.rsi.ca/rs2/prod/xml/schemas}numberOfSamplesPerLine":
                    # subtract one since first line/pixel is 0,0
                    numberOfSamplesPerLine = float(attribute.text) - 1
                if attribute.tag == "{http://www.rsi.ca/rs2/prod/xml/schemas}numberOfLines":
                    # subtract one since first line/pixel is 0,0
                    numberOfLines = float(attribute.text) - 1
   
        # Loop through all imageTiePoint elements and get lat/long for corners
        for tiepoint in root.iter('{http://www.rsi.ca/rs2/prod/xml/schemas}imageTiePoint'):
            child_list = tiepoint.getchildren()
            
            # this requires that the list has the same order in the future!
            # consider rewriting as above
            line      = float(child_list[0][0].text)
            pixel     = float(child_list[0][1].text)
            latitude  = float(child_list[1][0].text)
            longitude = float(child_list[1][1].text)
            
            
            #check if upper left
            if (line == 0.0) and (pixel == 0.0):
                sar_upperleft_x = longitude
                sar_upperleft_y = latitude
            
            #check if upper right
            if (line == 0.0) and (pixel == numberOfSamplesPerLine):
                sar_upperright_x = longitude
                sar_upperright_y = latitude
                    
            #check if lower left    
            if (line == numberOfLines) and (pixel == 0.0):
                sar_lowerleft_x = longitude
                sar_lowerleft_y = latitude
                    
            #check if upper right
            if (line == numberOfLines) and (pixel == numberOfSamplesPerLine):
                sar_lowerright_x = longitude
                sar_lowerright_y = latitude
        
        #Create WKT representation of bounding box polygon
        wkt_sarimage = "POLYGON((" + str(sar_upperleft_x) + " " +  str(sar_upperleft_y) + "," \
                  + str(sar_upperright_x) + " " + str(sar_upperright_y) + \
                  "," + str(sar_lowerright_x) + " " + str(sar_lowerright_y) + "," + str(sar_lowerleft_x) \
                  + " " + str(sar_lowerleft_y) + "," + str(sar_upperleft_x) + " " +  str(sar_upperleft_y) + "))"
                  
                
    # Access corners for Sentinel-1
    if "S1A" in sarfile:   
        # Get bounding box
        for tiepoint in root.iter('{http://www.google.com/kml/ext/2.2}LatLonQuad'):
            child_list = tiepoint.getchildren()
        bounding_box = child_list[0].text
        bounding_box_list = bounding_box.split(" ")
        #WKT requires that last point = first point in polygon, add first point
        wkt_sarimage1 = "POLYGON((" + bounding_box + " " + bounding_box_list[0] + "))"
        #WKT requires other use of comma and spaces in coordinate list
        wkt_sarimage2 = wkt_sarimage1.replace(" ", ";")
        wkt_sarimage3 = wkt_sarimage2.replace(",", " ")
        wkt_sarimage  = wkt_sarimage3.replace(";", ",")
        

    # Define projections
    datasetEPSG  = pyproj.Proj("+init=EPSG:4326")
    locationEPSG = pyproj.Proj("+init=" + str(locationEPSG))
    
    #Transform coordinates of location into sarfile coordinates
    upperleft_x,  upperleft_y  = pyproj.transform(locationEPSG, datasetEPSG, \
                                 location[0], location[1])
    lowerright_x, lowerright_y = pyproj.transform(locationEPSG, datasetEPSG, \
                                 location[2], location[3])   
    wkt_location = "POLYGON((" + str(upperleft_x) + " " +  str(upperleft_y) + "," \
                  + str(upperleft_x) + " "  + str(lowerright_y) + \
                  "," + str(lowerright_x) + " " + str(lowerright_y) + "," + str(lowerright_x) \
                  + " " + str(upperleft_y) + "," + str(upperleft_x) + " " +  str(upperleft_y) + "))"
                  
    print wkt_sarimage  
    print wkt_location    
    # Use ogr to check if polygon contained
    poly_location = ogr.CreateGeometryFromWkt(wkt_location)
    poly_sarimage = ogr.CreateGeometryFromWkt(wkt_sarimage)             
    contained = poly_location.Intersect(poly_sarimage)
    print contained
    os.remove(xml_file_extracted)
    return contained
    
    
def CreateQuicklook(sarfile, outputfilepath, quicklookEPSG):
    '''
    Creates quicklooks from Radarsat and Sentinel-1 files
    '''
            
    #Various file paths and names:    
    (sarfilepath, sarfilename)    = os.path.split(sarfile)             
    (sarfileshortname, extension) = os.path.splitext(sarfilename)        
    
    if len(quicklookEPSG) == 10:
        EPSGnumber = quicklookEPSG[5:10]
        EPSGname = 'EPSG' + EPSGnumber
    elif len(quicklookEPSG) == 9:
        EPSGnumber = quicklookEPSG[5:9]
        EPSGname = 'EPSG' + EPSGnumber
    
    # Choose SNAP file matching map projection
    snapfilename = 'Calib_Spk_reproj_LinDB_EPSG' + EPSGnumber + '.xml'
    
    # Filename for Sentinel or Radarsat to be processed
    if sarfileshortname[0:3] == 'RS2':  # RADARSAT-2
        gdalsourcefile = sarfilepath + '//' + sarfileshortname + '//product.xml'
        outputfile = outputfilepath + '//' + sarfileshortname + '_Cal_Spk_reproj' \
              + '_' + EPSGname + '.dim'
    if sarfileshortname[0:2] == 'S1':   # SENTINEL-1
        gdalsourcefile = sarfilepath  +  '//' + sarfileshortname + '.SAFE' + \
             '//' + 'manifest.safe'
        outputfile = outputfilepath + '//' + sarfileshortname + '_Cal_Spk_reproj' \
              + '_' + EPSGname + '.dim'
    if extension == '.001':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + \
             '//VDF_DAT.001' 
        split = sarfilepath.split("/")
        outputfile = outputfilepath + '//' + split[-2] + '_Cal_Spk_reproj' \
              + '_' + EPSGname + '.dim'

    if extension == '.E1':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + sarfileshortname + '.E1'

    if extension == '.E2':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + sarfileshortname + '.E2'
    
    #Extract the zipfile, skip if corrupt
    if extension == ".zip":    
        try:
            zfile = zipfile.ZipFile(sarfile, 'r')
            zfile.extractall(sarfilepath)
            zfile.close()
        except:
            print sarfile + " is corrupt and skipped."
            return
        


    
    print "Create Quicklook ", sarfilename    
          
    #Process using SNAP
    os.system(r'gpt //home//max//Documents//PythonProjects//SNAP//' + \
              snapfilename + ' -Pfile=" ' + gdalsourcefile + '"  -t "'+ \
              outputfile + '"' )



    # Convert DIM to GEOTIFF and JPEG

    #Get *.img files in dim-folder
    (outputfilenamepath, outputfilename) = os.path.split(outputfile)
    (outputfileshortname, extension)     = os.path.splitext(outputfilename)
        

    dim_datafile = outputfilepath + '//' + outputfileshortname + \
                   '.data/Sigma*.img'
    dimlist = glob.glob(dim_datafile)
    
    #Loop through Sigma*.img files and convert to GeoTIFF and JPG
    for envifile in dimlist:
        polarisation = envifile[-9:-7]
        
        #auxfile is created automatically by SNAP, name defined to remove it       
        auxfile = outputfilepath + '//' + sarfileshortname + \
            '_Cal_Spk_reproj_' + EPSGname + '_' + polarisation + '.tif.aux.xml'
        geotifffile = outputfilepath + '//' + sarfileshortname +  \
            '_Cal_Spk_reproj_' + EPSGname + '_' + polarisation + '.tif'
        jpegfile = outputfilepath + '//' + sarfileshortname + \
            '_Cal_Spk_reproj_' + EPSGname + '_'+  polarisation + '.jpg'
        if extension == '.001':
            split = sarfilepath.split("/")
            jpegfile = outputfilepath + '//' + split[-2] + '_' + \
                 '_Cal_Spk_reproj_' + EPSGname + '_'+  polarisation + '.jpg'
            geotifffile = outputfilepath + '//' + split[-2] + '_' + \
                 '_Cal_Spk_reproj_' + EPSGname + '_'+  polarisation + '.tif'
        
        print 'Converting ', envifile, ' to GeoTIFF and jpeg.'
 
        os.system("gdal_translate -a_srs EPSG:" + EPSGnumber + \
                  " -stats -of GTiff " + envifile + " " + geotifffile)

        os.system("gdal_translate -scale -30 0 0 255 -ot Byte" + \
                       " -co WORLDFILE=YES -of JPEG " + geotifffile + \
                       " " +  jpegfile) 
        
        
        #Clean up temp files
        
        try:
            os.remove(geotifffile) #uncomment if TIF file wanted!
        except:
            pass
        
        try:
            os.remove(auxfile)
        except:
            pass

    
    #Clean up temp files
    # Dim Files removed
    dim_datafolder = outputfilepath + '//' + outputfileshortname + '.data'
    try:
        shutil.rmtree(dim_datafolder)
        os.remove(outputfile)
    except:
        pass
    os.remove(outputfile)
    
    # Sentinel files removed
    try:
        shutil.rmtree(sarfilepath + '//' + sarfileshortname + '.SAFE')
    except:
        pass
    
    #Radarsat files removed
    try:
        shutil.rmtree(sarfilepath + '//' + sarfileshortname )
    except:
        pass   
 

def ProcessSAR(sarfile, outputfilepath, location, resolution, outputEPSG, TC, crop_to_location):
    '''
    Reads sarfile and chooses SNAP / NEST xml file based on the given input
    parameters.
    
    Produces geotiff, if location given a subset with the given location
    '''
            
    #Divide filename           
    (sarfilenamepath, sarfilename) = os.path.split(sarfile)
    (sarfileshortname, extension)  = os.path.splitext(sarfilename)
       
    # Filename for Sentinel or Radarsat to be processed
    if "RS2" in sarfileshortname:  # RADARSAT-2
        gdalsourcefile = outputfilepath + '//' + sarfileshortname + '//product.xml'
        
    if "S1A" in sarfileshortname:   # SENTINEL-1
        gdalsourcefile = outputfilepath + '//' + sarfileshortname + '.SAFE' + \
             '//' + 'manifest.safe'
    if extension == '.001':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + \
             '//VDF_DAT.001' 
    if extension == '.E1':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + sarfileshortname + '.E1'
    if extension == '.E2':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + sarfileshortname + '.E2'
    if extension == '.N1':   # ERS
        gdalsourcefile = sarfilepath  +  '//'   + sarfileshortname + '.N1'
    if 'TSX' in sarfile:
        gdalsourcefile = sarfile
    
    # Extracting the SAR file
    print "Decompressing " + sarfileshortname       
    if extension == ".zip":    
        try:
            zfile = zipfile.ZipFile(sarfile, "r")    
            zfile.extractall(outputfilepath)
            zfile.close()
        except:
            return
    
    #Call SNAP routine, xml file depending on sensor type and resolution
    print "Process ", sarfilename, " with SNAP."
    
    ### Get parameters to create output file name ###    
    # EPSG to add in filename, different length of number
    if len(outputEPSG) == 10:
        EPSGnumber = outputEPSG[5:10]
    elif len (outputEPSG) == 9:
        EPSGnumber = outputEPSG[5:9]    
    
    # Terrain Correction with resolution or reprojection not needing resolution
    if TC == True:
        projection = 'TC'
        pixelsize = str(resolution) + 'm_'
    else:
        projection = 'reproj_'
        pixelsize = ''
    
    # If an SLC image do multilooking
    if 'SLC' in sarfile:
        multilook = 'ML_'
        #multilook = ''
    else:
        multilook = ''
        
    if 'S1A' in sarfile:
        #apporb = 'AppOrb_'
        apporb = ''
    else:
        apporb = ''
        
    # This string indicating the processing applied will be appended to the 
    # created fileshortnames. It is also the name of the SNAP file
    filename_append = apporb + multilook + 'Calib_Spk_' + projection + pixelsize +  \
               'LinDB_' + 'EPSG' + EPSGnumber
               
    snapfile = filename_append + '.xml'
    outputfile = outputfilepath + '//' + sarfileshortname + '_' + \
                 filename_append +'.dim'
    if extension == '.001':
            split = sarfilepath.split("/")
            outputfile = outputfilepath + '//' + split[-2] + '_' + \
                 filename_append +'.dim'
            print "outputfile ", outputfile
        
     
    os.system(r'gpt //home//max//Documents//PythonProjects//SNAP//' + \
              snapfile + ' -Pfile=" '\
              + gdalsourcefile + '"  -t "'+ outputfile + '"' )
    
    #Remove folder where extracted and temporary files are stored
    if sarfileshortname[0:3] == 'RS2':
        try:
            shutil.rmtree(outputfilepath + '//' + sarfileshortname )
        except:
            pass
    if sarfileshortname[0:2] == 'S1':
        shutil.rmtree(outputfilepath + '//' + sarfileshortname + ".SAFE")
    
    
    ### Convert DIM to GEOTIFF and JPEG ###
    #Get *.img files in dim-folder
    (outputfilenamepath, outputfilename) = os.path.split(outputfile)
    (outputfileshortname, extension2)     = os.path.splitext(outputfilename)
    
    dim_datafolder = outputfilepath + '//' + outputfileshortname + '.data'
    dim_datafile   = outputfilepath + '//' + outputfileshortname + \
                     '.data/Sigma*.img'
    dimlist = glob.glob(dim_datafile)
    
    # Loop through dim-files and convert to geotiff jpeg
    for envifile in dimlist:
        polarisation = envifile[-9:-7]

        geotifffile = outputfilepath + '//' + sarfileshortname + '_' \
                      + filename_append + '_' + polarisation + '.tif'
        jpegfile   =  outputfilepath + '//' + sarfileshortname + '_' \
                      + filename_append + '_' + polarisation + '.jpg'
        if extension == '.001':
            print "aplitting", 
            split = sarfilepath.split("/")
            jpegfile = outputfilepath + '//' + split[-2] + '_' + \
                 filename_append +'.jpg'
            geotifffile = outputfilepath + '//' + split[-2] + '_' + \
                 filename_append +'.tif'
        print jpegfile
        print 'Converting: ', envifile
        if location != [] and crop_to_location == True:       
            upperleft_x  = str(location[0])        
            upperleft_y  = str(location[1])     
            lowerright_x = str(location[2])    
            lowerright_y = str(location[3])   
            print "Create ", geotifffile     
            os.system("gdal_translate -a_srs EPSG:" + EPSGnumber + \
                      " -stats -of GTiff -projwin " + upperleft_x + " " + \
                      upperleft_y  + " " + lowerright_x  + " " + \
                      lowerright_y  + " " + envifile + " " +  geotifffile)
        else:
            os.system("gdal_translate -a_srs EPSG:" + EPSGnumber + \
                      " -stats -of GTiff " + " " +  \
                      envifile + " " +  geotifffile) 
        print "Create ", jpegfile
        os.system("gdal_translate -scale -ot Byte -co WORLDFILE=YES -of JPEG " \
                + geotifffile + " " +  jpegfile) 
      
    try:
        shutil.rmtree(dim_datafolder) 
        os.remove(outputfile)
    except:
        pass
    

    
 

##############################################################################
#  CORE OF PROGRAMS FOLLOWS HERE
##############################################################################

#############################
# SET PATH AND VARIABLES HERE
#############################

# Map projection of output files
#outputEPSG = 'EPSG:32633'  #UTM 33N WGS 84 Svalbard mainland
#outputEPSG = 'EPSG:3575'  # Barents Sea and Framstrait
outputEPSG = 'EPSG:3031'  #Dronning Maud Land

# Map projection of Quicklooks
#quicklookEPSG = 'EPSG:3575'
quicklookEPSG = 'EPSG:3031'
#quicklookEPSG = 'EPSG:32633'

# Do you want Terrain Correction?
TC = True
#TC = False

# Define Area of interest in outputEPSG
# Austfonna EPSG32633 Surge
upperleft_x  =  651500.0
upperleft_y  = 8891000.0
lowerright_x =  740000.0
lowerright_y = 8800881.0

#Holtedalfonne
#upperleft_x = 419726.0
#upperleft_y =  8812000.0       
#lowerright_x = 475000.0        
#lowerright_y = 8737956.0

#Framstrait EPSG32633
#upperleft_x = -100000.0
#upperleft_y =  9080000.0       
#lowerright_x = 212705.0        
#lowerright_y = 8231907.0    

#Linne
#upperleft_x = 466181.17
#upperleft_y = 8660365.398 
#lowerright_x = 477193.43
#lowerright_y = 8668288.24

# DO YOU WANT OUTPUT TO BE CROPPED TO LOCATION?
crop_to_location = False
# OR DO YOU JUST WANT TO  HAVE SCENE CONTAINING location PROCESSED
#crop_to_location = True

# If location is set to [], all scenes will be processed
#location = [upperleft_x, upperleft_y, lowerright_x, lowerright_y]
location = []

# SCWA output resolution 50m
#outputresolution = 50
#outputresolution = 25
outputresolution = 4
#outputresolution = 20


# to mount Windows server type
#  sudo mount -t cifs //berner/satellittdata  /mnt/satellittdata -o  \
#        username=max,domain=NP,rw,iocharset=utf8,file_mode=0644,    \
#        dir_mode=0755,uid=max,gid=max


#inputfolder = "//media//max//DATADRIVE1//Radarsat//Flerbruksavtale//ArcticOcean_Svalbard//2016" 
#inputfolder = "//mnt//satellittdata//Sentinel-1//ArcticOceanSvalbard//2016" 
inputfolder = "//mnt//satellittdata//Radarsat//Flerbruksavtale//Antarctica" 
#inputfolder = "//mnt//satellittdata//Radarsat//Flerbruksavtale//Antarctica//2013"
#inputfolder = "//mnt//max//JitterTest"
#outputfolder = "//mnt//glaciology//processedSARimages//HoltedalsfonnaKongsfjorden_50_meter//2010"
outputfolder = "//mnt//glaciology//processedSARimages//Antarctica"
#outputfolder = "///media//max//DATADRIVE1//Jean"
#outputfolder = "//mnt//max//Quarctic//Basemap//Imagery"

##############################
# END OF VARIABLES TO BE SET
##############################

# Create list containing all zip files to be processed
filelist = []    
for root, dirnames, filenames in os.walk(inputfolder):
    for filename in fnmatch.filter(filenames, 'RS2_*.zip'):
        filelist.append(os.path.join(root, filename))
        
# This one grabs anyunzipped TerraSAR-X files in the folder   
for root, dirnames, filenames in os.walk(inputfolder):
    for filename in fnmatch.filter(filenames, "TSX*.xml"):
        filelist.append(os.path.join(root, filename))
for root, dirnames, filenames in os.walk(inputfolder):
    for filename in fnmatch.filter(filenames, 'VDF_DAT.001'):
        filelist.append(os.path.join(root, filename))
for root, dirnames, filenames in os.walk(inputfolder):
    for filename in fnmatch.filter(filenames, '*.E1'):
        filelist.append(os.path.join(root, filename))      
for root, dirnames, filenames in os.walk(inputfolder):
    for filename in fnmatch.filter(filenames, '*.E2'):
        filelist.append(os.path.join(root, filename))  
for root, dirnames, filenames in os.walk(inputfolder):
    for filename in fnmatch.filter(filenames, '*.N1'):
        filelist.append(os.path.join(root, filename))         
    
print "Number of Scenes Found: ", len(filelist)
# Loop through each file in file list and do processing
for sarfile in filelist:
    print
    print "Scene ", filelist.index(sarfile) + 1 , "of ", len(filelist)
    
    (sarfilepath, sarfilename)     = os.path.split(sarfile)
    (sarfileshortname, extension)  = os.path.splitext(sarfilename)
    
    #CreateQuicklook(sarfile, sarfilepath, quicklookEPSG)
    
            # Check if AOI extract is wanted       
    
  
    # If location is given, check if contained, if not skip scene
    if location != []:
       contained = CheckLocation(sarfile, location, outputEPSG, outputfolder)
       print sarfilename, " is contained: ", contained
       if contained == False:
           continue
    
    ProcessSAR(sarfile, outputfolder, location, outputresolution,\
                    outputEPSG, TC, crop_to_location)
        

        

        
