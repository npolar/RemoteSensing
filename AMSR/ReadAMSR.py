# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 07:19:33 2014

@author: max
"""
import xml.etree.cElementTree as ET
import gdal, gdalconst, glob, gzip, numpy, os, osr, shutil, sys, pyproj, datetime

def UnzipAMSR(AMSRzipfile, outfilepath):
    '''
    Extracts gzip files (*.gz file ending)
    '''
    
    #Various file paths and names:    
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename) 
    
    print 'extracting ', AMSRzipfile
    AMSRzipfile = gzip.open(AMSRzipfile)
    AMSRopened = AMSRzipfile.read()
    AMSRzipfile.close()
    
    AMSRfile = file((outfilepath + AMSRzipfileshortname), 'wb')
    AMSRfile.write(AMSRopened)
    AMSRfile.close()



def AMSRtoCSV_Br89(AMSRzipfile, outfilepath, channelA, channelB, polarization):
    '''
    converts AMSR raster to csv
    '''
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename)
    
    AMSRcsv = outfilepath + AMSRzipfileshortname[:-3] + '_channel89' + polarization +'.csv'
    
    HDFfile = gdal.Open(outfilepath + '\\' + AMSRzipfileshortname )
    HDF_bands = HDFfile.GetSubDatasets()
    #HDF Subdatasets are opened just as files are opened:
    HDF_Br89AH = gdal.Open(HDF_bands[channelA][0])
    HDF_Br89AH_array = HDF_Br89AH.ReadAsArray()
    
    HDF_Br89BH = gdal.Open(HDF_bands[channelB][0])
    HDF_Br89BH_array = HDF_Br89BH.ReadAsArray()
    
    HDF_Lat89A = gdal.Open(HDF_bands[46][0])
    HDF_Lat89A_array = HDF_Lat89A.ReadAsArray()
    
    HDF_Lat89B = gdal.Open(HDF_bands[47][0])
    HDF_Lat89B_array = HDF_Lat89B.ReadAsArray()
    
    HDF_Lon89A = gdal.Open(HDF_bands[48][0])
    HDF_Lon89A_array = HDF_Lon89A.ReadAsArray()
    
    HDF_Lon89B = gdal.Open(HDF_bands[49][0])
    HDF_Lon89B_array = HDF_Lon89B.ReadAsArray()
    
    # Get columns and rows, needed to loop through each pixel 
    cols = HDF_Br89AH.RasterXSize
    rows = HDF_Br89AH.RasterYSize
    
    ###########################################
    ## Write lon/lat/brightness to txt=csv file
    ###########################################
    
    print 'Convert  ', AMSRzipfileshortname, ' to csv.'    
    #Add header line to textfile
    textfile = open( AMSRcsv, 'w')
    textfile.write('lon,lat,brightness\n')
    ## Loop through each pixel and write lon/lat/brightness to csv file
    for i in range(rows):
        for j in range(cols):
            
            wgs84=pyproj.Proj("+init=EPSG:4326")
            EPSG3411=pyproj.Proj("+init=EPSG:3411")
            
            lonA = HDF_Lon89A_array[i,j]
            latA = HDF_Lat89A_array[i,j]
            # lon/lat written to file already projected to EPSG:3411
            (lonA_3411, latA_3411) = pyproj.transform(wgs84, EPSG3411, lonA, latA)
            brightnessA = HDF_Br89AH_array[i,j]* 0.01 #APPLYING SCALING FACTOR!
            
            lonB = HDF_Lon89B_array[i,j]
            latB = HDF_Lat89B_array[i,j]
            # lon/lat written to file already projected to EPSG:3411
            (lonB_3411, latB_3411) = pyproj.transform(wgs84, EPSG3411, lonB, latB)
            brightnessB = HDF_Br89BH_array[i,j]* 0.01 #APPLYING SCALING FACTOR!
            
            if 35 < latA < 90:
                textfile.write(str(lonA_3411) + ',' + str(latA_3411) + ',' + str(brightnessA) + '\n')

            if 35 < latB < 90:
                textfile.write(str(lonB_3411) + ',' + str(latB_3411) + ',' + str(brightnessB) + '\n')
            
    textfile.close()
    HDFfile = None
    HDF_SubDataset = None
    try:
        os.remove(AMSRzipfile[0:-3]) #remove unzipped file
    except:
        pass

def AMSRtoCSV_lowres(AMSRzipfile, outfilepath, channel, frequency, polarization):
    '''
    converts AMSR raster to csv
    
    THIS ONE FOR THE LOW RESOLUTION CHANNELS
    '''
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename)
    
    AMSRcsv = outfilepath + AMSRzipfileshortname[:-3] + '_channel' + frequency + polarization + '.csv'
    
    HDFfile = gdal.Open(outfilepath + '\\' + AMSRzipfileshortname )
    HDF_bands = HDFfile.GetSubDatasets()
    #HDF Subdatasets are opened just as files are opened:
    HDF_SubDataset = gdal.Open(HDF_bands[channel][0])
    HDF_SubDataset_array = HDF_SubDataset.ReadAsArray()
        
    HDF_Lat89A = gdal.Open(HDF_bands[46][0])
    HDF_Lat89A_array = HDF_Lat89A.ReadAsArray()
    
    HDF_Lon89A = gdal.Open(HDF_bands[48][0])
    HDF_Lon89A_array = HDF_Lon89A.ReadAsArray()
    
    # Get columns and rows, needed to loop through each pixel 
    cols = HDF_SubDataset.RasterXSize
    rows = HDF_SubDataset.RasterYSize
    
    ###########################################
    ## Write lon/lat/brightness to txt=csv file
    ###########################################
    
    print 'Convert  ', AMSRzipfileshortname, ' to csv.'    
    #Add header line to textfile
    textfile = open( AMSRcsv, 'w')
    textfile.write('lon,lat,brightness\n')
    ## Loop through each pixel and write lon/lat/brightness to csv file
    for i in range(rows):
        for j in range(cols):
            
            wgs84=pyproj.Proj("+init=EPSG:4326")
            EPSG3411=pyproj.Proj("+init=EPSG:3411")
            
            #For low resolution the odd columns of Lon/Lat89 array to be taken!
            lonA = HDF_Lon89A_array[(i) ,(j*2+1)]
            latA = HDF_Lat89A_array[(i) ,(j*2+1)]
            # lon/lat written to file already projected to EPSG:3411
            (lonA_3411, latA_3411) = pyproj.transform(wgs84, EPSG3411, lonA, latA)
            brightnessA = HDF_SubDataset_array[i,j]* 0.01 #APPLYING SCALING FACTOR!
            
            
            if 35 < latA < 90:
                textfile.write(str(lonA_3411) + ',' + str(latA_3411) + ',' + str(brightnessA) + '\n')
            
    textfile.close()
    
    HDFfile = None
    HDF_SubDataset = None
    try:
        os.remove(AMSRzipfile[0:-3])  #remove unzipped file
    except:
        pass    
    
def CSVtoRaster(AMSRzipfile, outfilepath, frequency, polarization):
    '''
    converts CSV raster to raster
    '''
    
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename)
         
    AMSRcsv_shortname = AMSRzipfileshortname[:-3] + '_channel' + str(frequency) + polarization
    AMSRcsv = outfilepath + AMSRzipfileshortname[:-3] + '_channel' + str(frequency) + polarization + '.csv'
    
    AMSRcsv_vrt = outfilepath + AMSRzipfileshortname[:-3] + '_channel' + str(frequency) + polarization + '.vrt'
    
    AMSR_tif = outfilepath + AMSRzipfileshortname[:-3] + '_channel' + str(frequency) + polarization + '.tif'
    ##############################
    #Create the necessary XML file
    ##############################
    root = ET.Element("OGRVRTDataSource")
    OGRVRTLayer  = ET.SubElement(root, "OGRVRTLayer")
    OGRVRTLayer.set("name", AMSRcsv_shortname)
    
    SrcDataSource = ET.SubElement(OGRVRTLayer, "SrcDataSource")
    SrcDataSource.text = AMSRcsv
    
    GeometryType = ET.SubElement(OGRVRTLayer, "GeometryType")
    GeometryType.text = "wkbPoint"
    
    GeometryField = ET.SubElement(OGRVRTLayer,"GeometryField")
    GeometryField.set("encoding", "PointFromColumns")
    GeometryField.set("x", "lon")
    GeometryField.set("y", "lat")
    GeometryField.set("z", "brightness")
    
    tree = ET.ElementTree(root)
    tree.write(AMSRcsv_vrt)
    
    ##########################
    # Gdal_grid
    ##########################
    
    print "Convert csv to raster."
    
    
    
    
    # First version gives X: 3168 Y: 1550 Bands: 1 with Pixel Size 0.113478,-0.113405
    # for all world
    # For 89A and 89B double resolution, so try 0.056739
    # (90-0) / 0.056739 = 1586 -- 
    # 10km = outsize 760 1120
    #gdal_grid performance issue see http://trac.osgeo.org/gdal/ticket/2411
    
    # Adjust search radius for frequency and resolution, if too low empty pixels
    # if too large smoothed too much    
    if frequency == "36_5":
        radius1 = 7000
        radius2 = 7000
        xsize = 760 
        ysize = 1120
    elif frequency == "6_9":
        radius1 = 7000
        radius2 = 7000
        xsize = 760 
        ysize = 1120
    elif frequency == "7_3":
        radius1 = 7000
        radius2 = 7000
        xsize = 760 
        ysize = 1120
    elif frequency == "10_7":
        radius1 = 7000
        radius2 = 7000
        xsize = 760 
        ysize = 1120
    elif frequency == "18_7":
        radius1 = 7000
        radius2 = 7000
        xsize = 760 
        ysize = 1120
    elif frequency == "23_8": 
        radius1 = 7000
        radius2 = 7000
        xsize = 760 
        ysize = 1120
    elif frequency == "89":
        radius1 = 4000
        radius2 = 4000
        xsize = 1520 
        ysize = 2240
    else:
        radius1 = 4000
        radius2 = 4000
        xsize = 1520 
        ysize = 2240
    
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=' + str(radius1) + ':radius2=' + str(radius2) + ':min_points=1 -txe -3850000 3750000 -tye -5350000 5850000 -outsize '+  xsize + ' ' + ysize + ' -l ' + AMSRcsv_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_tif)
    
    # Set Projection -- was not in file with gdal_grid    
    outfile = gdal.Open(AMSR_tif, gdalconst.GA_Update)
    proj = osr.SpatialReference()  
    proj.SetWellKnownGeogCS( "EPSG:3411" )  
    outfile.SetProjection(proj.ExportToWkt()) 
    outfile = None
    
    AMSRcsv_shortname = None
    AMSRcsv = None
    AMSRcsv_vrt = None
    AMSR_tif = None
    
    
    try:
        os.remove(AMSRcsv)
    except:
        pass

    
def AverageDaily(startdate, enddate, diff, outfilepath, frequency, polarization):
    '''
    Take all files from one day and create an average file
    '''

    
    #initiate workingdate
    workingdate = startdate
    
    
    while workingdate != (enddate + diff):
        #Create filelist with all files having the same date, e.g. 20130101
        searchstring = outfilepath + 'GW1AM2_' + str(workingdate.strftime("%Y%m%d")) + '*_channel' + str(frequency) + polarization + '.tif'
        AMSR_dailyaverage_name = outfilepath + 'GW1AM2_dailyaverage_' + str(workingdate.strftime("%Y%m%d")) + '_channel' + str(frequency) + polarization + '.tif'
        filelist = glob.glob(searchstring)
        
        #open the first file in list -- since NSIDC raster, all are on same raster
        firstfile = gdal.Open(filelist[0], gdalconst.GA_ReadOnly)
        if firstfile is None:
            print 'Could not open ', firstfilename
            return
        
        #get image size
        rows = firstfile.RasterYSize
        cols = firstfile.RasterXSize    
        #create output images
        driver = firstfile.GetDriver()
        outraster = driver.Create(AMSR_dailyaverage_name, cols, rows, 1, gdal.GDT_Float64 )
        if outraster is None: 
            print 'Could not create ', outfile
            return
    
        # Set Geotransform and projection for outraster
        outraster.SetGeoTransform(firstfile.GetGeoTransform())
        proj = osr.SpatialReference()  
        proj.SetWellKnownGeogCS( "EPSG:3411" )  
        outraster.SetProjection(proj.ExportToWkt())  
    
        rows = outraster.RasterYSize
        cols = outraster.RasterXSize
        outarray = numpy.zeros((rows, cols), numpy.float)
        countingarray = outarray
        outraster.GetRasterBand(1).WriteArray( outarray )
        
        firstfile = None

        print ' length filelist ', len(filelist)
        
        ### CHECK IF STATS RIGHT !!!!!!!!!!!!!!!!!!!!!!!!!!!#
        #Process AMSR with this filelist
        for i in range(0, len(filelist)):
            print 'adding ', filelist[i]
            nextfile = gdal.Open(filelist[i], gdalconst.GA_ReadOnly)
            nextarray = nextfile.ReadAsArray()
            countingarray = numpy.where(nextarray == 0, countingarray, countingarray + 1)
            outarray = outarray + nextarray 
            nextarray = None            
            nextfile = None
        # csv is rasterized for all files from one month
        
        outarray = numpy.where(countingarray != 0, (outarray / countingarray), 0)
        
        AMSR_band = outraster.GetRasterBand(1)
        AMSR_band.WriteArray( outarray )
        AMSR_band.FlushCache() 
        
        nextfile = None
        nextarray = None
        coutingarray = None
        
        workingdate = workingdate + diff
        print ' Now processing ', workingdate    
        
        
outraster = None


    
##############################################################################

###   Core of Program follows here ###

##############################################################################

outfilepath = 'G:\\AMSR\\'
inputfilepath = 'U:\\AMSR2\\L1R\\'

startyear = 2013
endyear = 2013

startday = 1
startmonth = 1

endday = 2
endmonth = 1

startdate =  datetime.date(startyear, startmonth, startday)
enddate =  datetime.date(endyear, endmonth, endday)
diff = datetime.timedelta(days = 1)
    
    
#Create filelist including all files for the given month between startyear and stopyear inclusive
#initiate workingdate
filelist = []
workingdate = startdate

while workingdate != (enddate + diff):
    file_searchstring = 'GW1AM2_' + str(workingdate.strftime("%Y%m%d"))  + '*.gz'
    foldersearchstring = inputfilepath + file_searchstring
    filelist.extend(glob.glob(foldersearchstring))
    workingdate = workingdate + diff




#########################################
## Calculate 89GHz
#########################################
    
for AMSRzipfile in filelist:
    print 'AMSRzipfile'
    UnzipAMSR(AMSRzipfile, outfilepath)
    polarization = 'H'
    channelA=2
    channelB=4
    AMSRtoCSV_Br89(AMSRzipfile, outfilepath, channelA, channelB, polarization)
    
    polarization = 'V'
    channelA=3
    channelB=5
    AMSRtoCSV_Br89(AMSRzipfile, outfilepath, channelA, channelB, polarization)
    
    frequency=89
    polarization = 'H'
    CSVtoRaster(AMSRzipfile, outfilepath, frequency, polarization)
    
    frequency=89
    polarization = 'V'
    CSVtoRaster(AMSRzipfile, outfilepath, frequency, polarization)

#Create average daily file for 89GHz and both polarizations    
AverageDaily(startdate, enddate, diff, outfilepath, frequency='89', polarization='H') 
AverageDaily(startdate, enddate, diff, outfilepath, frequency='89', polarization='V') 

#######################################
## Calculate low res channels
#######################################

channellistH = {"6_9": 14, "7_3": 16, "10_7": 20, "18_7": 22, "23_8": 32, "36_5": 38  }
channellistV = {"6_9": 15, "7_3": 17, "10_7": 21, "18_7": 23, "23_8": 33, "36_5": 39  } 

###### Low Res for H pol ##############
polarization = 'H'
for AMSRzipfile in filelist:
    for key in channellistH:
        if not os.path.exists(AMSRzipfile[0:-3]):
            
            UnzipAMSR(AMSRzipfile, outfilepath)
        print 'Process ', AMSRzipfile, key, channellistH[key]
        frequency = key
        channel = channellistH[key]
        AMSRtoCSV_lowres(AMSRzipfile, outfilepath, channel, frequency, polarization)
        CSVtoRaster(AMSRzipfile, outfilepath, frequency, polarization)
for key in channellistH:
    frequency = key
    channel = channellistH[key]
    AverageDaily(startdate, enddate, diff, outfilepath, frequency, polarization) 

        
###### Low Res for V pol ##############
polarization = 'V'
for AMSRzipfile in filelist:
    for key in channellistV:
        if not os.path.exists(AMSRzipfile[0:-3]):
            UnzipAMSR(AMSRzipfile, outfilepath)
        print 'Process ', AMSRzipfile, key, channellistV[key]
        frequency = key
        channel = channellistV[key]
        AMSRtoCSV_lowres(AMSRzipfile, outfilepath, channel, frequency, polarization)
        CSVtoRaster(AMSRzipfile, outfilepath, frequency, polarization)
                
for key in channellistV:
    frequency = key
    channel = channellistV[key]
    AverageDaily(startdate, enddate, diff, outfilepath, frequency, polarization) 


        
print 'Done ReadAMSR.py'