# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 10:44:10 2015

@author: max
"""

import struct, numpy, gdal, gdalconst, glob, os, osr
import shutil, sys, ogr

def EPSG3411_2_EPSG3575(infile):
    '''
    reprojects the infile from NSIDC 3411 to EPSG 3575
    outputfile has 25km resolution
    '''
    
    (infilepath, infilename) = os.path.split(infile)
    (infileshortname, extension) = os.path.splitext(infilename)
    outdirectory = infilepath + '//EPSG3575//'
    if not os.path.exists(outdirectory):
        os.makedirs(outdirectory)
    outfile =  outdirectory + infileshortname + '_EPSG3575.tif'
    print ' Reproject ', infile, ' to ', outfile 
    os.system('gdalwarp -q -s_srs EPSG:3411 -tr 25000 -25000 -t_srs EPSG:3575'\
               + ' -of GTiff ' + infile + ' ' + outfile)

def EPSG3411_2_EPSG32633(infile):
    '''
    reprojects the infile from NSIDC 3411 to EPSG 3575
    outputfile has 25km resolution
    '''
    
    (infilepath, infilename) = os.path.split(infile)
    (infileshortname, extension) = os.path.splitext(infilename)
    outdirectory = infilepath + '//EPSG32633//'
    if not os.path.exists(outdirectory):
        os.makedirs(outdirectory)
    outfile =  outdirectory + infileshortname + '_EPSG32633.tif'
    print ' Reproject ', infile, ' to ', outfile 
    os.system('gdalwarp -q -s_srs EPSG:3411 -tr 25000 -25000 -t_srs EPSG:32633'\
             + ' -of GTiff ' + infile + ' ' + outfile)


def Bin2GeoTiff(infile,outfilepath ):
    '''
        This function takes the NSIDC charts, being a flat binary string,
        and converts them to GeoTiff. Some details here:
        http://geoinformaticstutorial.blogspot.no/2014/02/reading-binary-data-nsidc-sea-ice.html
        Info on the ice concentration charts: http://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html 
        Info on the map projection: http://nsidc.org/data/polar_stereo/ps_grids.html
        The GeoTiff files are map projected to EPSG:3411, being the NSIDC-
        specific projection. There also is produced a GeoTiff reprojected to 
        EPSG:3575 which is the NP-standard for Barents/Fram-Strait.
        Details on how to map project are found here:
        http://geoinformaticstutorial.blogspot.no/2014/03/geocoding-nsidc-sea-ice-concentration.html
        
    '''
    
    #Define file names 
    (infilepath, infilename) = os.path.split(infile)             
    (infileshortname, extension) = os.path.splitext(infilename)
        
    outfile = outfilepath + infileshortname + '.tif'
    #Dimensions from https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    height = 448
    width = 304
    
    #####    
    # READ FLAT BINARY INTO ARRAY
    #####
    #for this code on how to read flat binary string, inspiration found at
    # https://stevendkay.wordpress.com/category/python/
    icefile = open(infile, "rb")
    contents = icefile.read()
    icefile.close()
    
    # unpack binary data into a flat tuple z
    #offset and width/height from
    # https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    s="%dB" % (int(width*height),)
    z=struct.unpack_from(s, contents, offset = 300) 
    nsidc = numpy.array(z).reshape((448,304))
    
    ########
    #WRITE THE ARRAY TO GEOTIFF
    ########
    driver = gdal.GetDriverByName("GTiff")
    outraster = driver.Create(outfile,  width, height,1, gdal.GDT_Int16 )
    if outraster is None: 
        print 'Could not create '
        return
    
    #set geotransform, values from
    # https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
    geotransform = (-3850000.0, 25000.0 ,0.0 ,5850000.0, 0.0, -25000.0)
    outraster.SetGeoTransform(geotransform)
    outband = outraster.GetRasterBand(1)
    #Write to file     
    outband.WriteArray(nsidc)
    
    spatialRef = osr.SpatialReference()
    # spatialRef.ImportFromEPSG(3411)  --> this one does for some reason NOT 
    # work, but using proj4 does
    spatialRef.ImportFromProj4('+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 '\
           + '+k=1 +x_0=0 +y_0=0 +a=6378273 +b=6356889.449 +units=m +no_defs')
    outraster.SetProjection(spatialRef.ExportToWkt() )
    outband.FlushCache()
    
    #Clear arrays and close files
    outband = None
    outraster = None
    nsidc = None
    
    #####
    #REPROJECT GEOTIFF TO EPSG3575
    #####
    EPSG3411_2_EPSG3575(outfile)
    EPSG3411_2_EPSG32633(outfile)

def ExtractRingSection(ring, section, infile, outputfilepath):
    '''
    '''
    #Define file names 
    (infilepath, infilename) = os.path.split(infile)             
    (infileshortname, extension) = os.path.splitext(infilename)
    
    RingSectionFile = outputfilepath + infileshortname + '_ring' + str(ring) +\
                      '_section' + str(section) + '.tif'
    cutline = '//home//max//Documents//DagIskart//RingSectionsMerge.shp'    
    print "create ",  infileshortname + '_ring' + str(ring) +\
                      '_section' + str(section)  
    os.system('gdalwarp  -q -cutline ' + cutline + ' -of GTiff '\
                + '-cwhere "POLY_ID=' + str(ring) + " AND SECTION='"  \
                + str(section) +  "'\" " + infile + ' ' +  RingSectionFile)
    

def MonthlyStats(outputfilepath, filelist, year, ring, section):
    '''
    '''
    NumberOfDays = len(filelist)
    monthDict={1:'January', 2:'February', 3:'March', 4:'April', 5:'May', \
               6:'June', 7:'July', 8:'August', 9:'September', 10:'October', \
               11:'November', 12:'December'}    
    outputtextfile = outputfilepath + "MonthlyStatistics" + str(year) + ".txt"
    cumulativepermonth = 0
    cumulativeperday = 0 
    
    for ringsectionfile in filelist:
        (ringsectionfilenamepath, ringsectionfilename) = os.path.split(ringsectionfile)
        year = int(ringsectionfilename[3:7])
        monthAsNumber = int(ringsectionfilename[7:9])
        month = monthDict[int(ringsectionfilename[7:9])]
        
        gdal.AllRegister()
        
        # open the image
        ds = gdal.Open(ringsectionfile, gdalconst.GA_ReadOnly)
        if ds is None:
            print 'Could not open '
            sys.exit(1)
        referencefilename = '//home//max//Documents//DagIskart//Rasterize' + section + '.tif'
        referencefile = gdal.Open(referencefilename, gdalconst.GA_ReadOnly)
        
        # get image size
        rows = ds.RasterYSize
        cols = ds.RasterXSize

        #Read input raster into array
        ringsectionraster = ds.ReadAsArray()
        referenceraster = referencefile.ReadAsArray()
        
        percentage = 0
        cumulativeperday = 0
        count = 0
        for i in range(rows):
            for j in range(cols):
                if (referenceraster[i,j] == int(ring)) and \
                   ( 0<= ringsectionraster[i,j] <= 250):
                    percentage = ringsectionraster[i,j] *100/250.0
                    count = count + 1
                    cumulativeperday = cumulativeperday + percentage
                    
        cumulativeperday = cumulativeperday / count
        cumulativepermonth = cumulativepermonth + cumulativeperday / NumberOfDays
        ds = None
        referencefile = None

    print 'Year and month = ', str(year), month
    print 'Mean Ice Concentration = ', cumulativepermonth
    textfile = open( outputtextfile, 'a')
    textfile.write(str(year) + ', ' + month + ', ' + ring + ', ' + section + ', ' \
                      + str(cumulativepermonth) + '\n' )   
    textfile.close()
    ds = None
    CreateRingStatistics(ring, section, year, monthAsNumber, cumulativepermonth)

def CreateRingStatistics(ring, section, year, monthAsNumber, cumulativepermonth):
    '''
    '''
    driver = ogr.GetDriverByName('ESRI Shapefile')
    #datasource = driver.Open('/home/max/Documents/DagIskart/RingStatisticsTest.shp', 1)
    datasource = driver.Open('/home/max/Documents/DagIskart/RingStatistics' + str(year) + '.shp', 1)

#    if not os.path.isfile(datasource): 
#        shutil.copyfile('/home/max/Documents/DagIskart/RingStatistics.shp', datasource)
    
    layer = datasource.GetLayer()
    
    if monthAsNumber < 11:
        monthAsNumberString = '0' + str(monthAsNumber)
    elif monthAsNumber > 10:
        monthAsNumberString = str(monthAsNumber)
    
    yearmonth = str(year) + monthAsNumberString
    
    feature = layer.GetFeature(0)
    try:
        feature.GetField(yearmonth)
    except:
        fieldDef = ogr.FieldDefn(yearmonth, ogr.OFTReal)
        layer.CreateField(fieldDef)

    
    featurecount = layer.GetFeatureCount()
    for i in range(0, featurecount):
        feature = layer.GetFeature(i)

        
        featurering = str(feature.GetFieldAsInteger('RING'))
        featuresection = feature.GetFieldAsString('SECTION')
        if (featurering == ring) and (featuresection == section):
            feature.SetField(yearmonth, cumulativepermonth)
            layer.SetFeature(feature)
            layer.ResetReading()
            #feature.Destroy()
            datasource.Destroy()
            return
    layer.ResetReading()
    datasource.Destroy()
    
    
    
##############################################################################

###   Core of Program follows here ###

##############################################################################


startyear = 2002
stopyear = 2002


monthDict={1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
#monthDict = {1:'January'}
ringDict={1:'25', 2:'50', 3:'75', 4:'100', 5:'125', 6:'150', 7:'175', 8:'200',\
          9: '225', 10:'250', 11:'275', 12:'300', 13:'325', 14:'350', 15:'375',\
          16:'400'}
sectionDict={1:'NE', 2:'SE', 3:'SW', 4:'W', 5:'NW'}
#outfilepath = 'C:\\Users\\max\\Documents\\IcePersistency\\' + monthDict[month] + '\\'

    
#Create filelist including all files for the given month between startyear and stopyear inclusive
filelist = []
for year in range(startyear, stopyear + 1):
    outfilepath = '//media//max//Transcend//DagIskart//' + str(year) + '//'
    
    if os.path.exists(outfilepath):
        answer = raw_input(outfilepath + " exists, delete and overwrite folder? [Y]es?")
        if answer.lower().startswith('y'):
            print "Overwriting " + outfilepath        
            shutil.rmtree(outfilepath)
            os.makedirs(outfilepath)
        else:
            print "Ending program"
            sys.exit()
        
    elif not os.path.exists(outfilepath):
        os.makedirs(outfilepath)
    
    for month in range(1,13):
        foldername = '//media//max//Transcend//NSIDC//north//daily//' + str(year) + '//'
        if month < 10: 
            file_searchstring = 'nt_' + str(year) + '0' + str(month) + '*.bin'
        else:
            file_searchstring = 'nt_' + str(year)  + str(month) + '*.bin'
        
        foldersearchstring = foldername + file_searchstring
        filelist = []        
        filelist = glob.glob(foldersearchstring)
        # presentoutput = where in this iteration files are saved
        presentoutput = outfilepath + '//' + monthDict[month] + '//'
        os.makedirs(presentoutput)
        for icechart in filelist:
                #Convert NSIDC files to GeoTiff
                print'convert ', icechart
                Bin2GeoTiff(icechart, presentoutput)
        
        projectedlist = []
        projectedlist = glob.glob(presentoutput + '//EPSG32633//*EPSG32633.tif')
        
        #Create file for each section and ring


        for projectedfile in projectedlist:
            for i in ringDict:
                for j in sectionDict:
                    ExtractRingSection(ringDict[i], sectionDict[j], \
                               projectedfile, presentoutput + '//EPSG32633//')
        for i in ringDict:
            for j in sectionDict:
                print 'stats for ring ', i,'section', j
                ringsectionlist = glob.glob(presentoutput + 'EPSG32633//*ring' + \
                           str(ringDict[i]) + '_section' + str(sectionDict[j]) + '.tif')
                MonthlyStats(outfilepath, ringsectionlist, year, str(ringDict[i]), str(sectionDict[j]))
        
print "Done"        
    