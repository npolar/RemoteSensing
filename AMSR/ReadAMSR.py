# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 07:19:33 2014

@author: max
"""
import xml.etree.cElementTree as ET
import gdal, gdalconst, glob, gzip, numpy, os, shutil, sys, pyproj, datetime

def UnzipAMSR(AMSRzipfile):
        
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



def AMSRtoCSV(AMSRzipfile):
    '''
    converts AMSR raster to csv
    '''
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename)
    
    AMSRcsv = outfilepath + AMSRzipfileshortname[:-3] + '.csv'
    
    HDFfile = gdal.Open(AMSRzipfilepath + '\\' + AMSRzipfileshortname )
    HDF_bands = HDFfile.GetSubDatasets()
    
    HDF_Br89AH = gdal.Open(HDF_bands[13][0])
    HDF_Br89AH_array = HDF_Br89AH.ReadAsArray()
    
    HDF_Br89BH = gdal.Open(HDF_bands[15][0])
    HDF_Br89BH_array = HDF_Br89BH.ReadAsArray()
    
    HDF_Lat89A = gdal.Open(HDF_bands[27][0])
    HDF_Lat89A_array = HDF_Lat89A.ReadAsArray()
    
    HDF_Lat89B = gdal.Open(HDF_bands[28][0])
    HDF_Lat89B_array = HDF_Lat89B.ReadAsArray()
    
    HDF_Lon89A = gdal.Open(HDF_bands[29][0])
    HDF_Lon89A_array = HDF_Lon89A.ReadAsArray()
    
    HDF_Lon89B = gdal.Open(HDF_bands[30][0])
    HDF_Lon89B_array = HDF_Lon89B.ReadAsArray()
    
    
    cols = HDF_Br89AH.RasterXSize
    rows = HDF_Br89AH.RasterYSize
    
    print 'Convert  ', AMSRzipfileshortname, ' to csv.'    
    
    textfile = open( AMSRcsv, 'w')
    textfile.write('lon,lat,brightness\n')
    for i in range(rows):
        for j in range(cols):
            
            wgs84=pyproj.Proj("+init=EPSG:4326")
            EPSG3411=pyproj.Proj("+init=EPSG:3411")
            
            lonA = HDF_Lon89A_array[i,j]
            latA = HDF_Lat89A_array[i,j]
            (lonA_3411, latA_3411) = pyproj.transform(wgs84, EPSG3411, lonA, latA)
            brightnessA = HDF_Br89AH_array[i,j]* 0.01 #APPLYING SCALING FACTOR!
            
            lonB = HDF_Lon89B_array[i,j]
            latB = HDF_Lat89B_array[i,j]
            (lonB_3411, latB_3411) = pyproj.transform(wgs84, EPSG3411, lonB, latB)
            brightnessB = HDF_Br89BH_array[i,j]* 0.01 #APPLYING SCALING FACTOR!
            
            if 35 < latA < 90:
                textfile.write(str(lonA_3411) + ',' + str(latA_3411) + ',' + str(brightnessA) + '\n')

            if 35 < latB < 90:
                textfile.write(str(lonB_3411) + ',' + str(latB_3411) + ',' + str(brightnessB) + '\n')
            
    textfile.close()
    
    
    
def CSVtoRaster(AMSRzipfile):
    '''
    converts CSV raster to raster
    '''
    
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename)
         
    AMSRcsv_shortname = AMSRzipfileshortname[:-3]
    AMSRcsv = outfilepath + AMSRzipfileshortname[:-3] + '.csv'
    
    AMSRcsv_vrt = outfilepath + AMSRzipfileshortname[:-3] + '.vrt'
    AMSRcsv_tif = outfilepath + AMSRzipfileshortname[:-3] + '.tif'
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
    
    
    AMSR_tif = outfilepath + AMSRzipfileshortname[:-3] + '.tif'
    
    # First version gives X: 3168 Y: 1550 Bands: 1 with Pixel Size 0.113478,-0.113405
    # for all world
    # For 89A and 89B double resolution, so try 0.056739
    # (90-0) / 0.056739 = 1586 -- 
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=4000:radius2=4000:min_points=1 -txe -3850000 3750000 -tye -5350000 5850000 -outsize 1520 2240 -l ' + AMSRcsv_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_tif)
    
#    

    
def AverageDaily(startdate, enddate, diff):


    
    #initiate workingdate
    workingdate = startdate
    
    
    while workingdate != (enddate + diff):
        #Create filelist with all files having the same date, e.g. 20130101
        searchstring = 'C:\Users\max\Documents\AMSR\GW1AM2_' + str(workingdate.strftime("%Y%m%d")) + '*.tif'
        AMSR_dailyaverage_name = 'C:\Users\max\Documents\AMSR\GW1AM2_dailyaverage_' + str(workingdate.strftime("%Y%m%d")) + '.tif'
        filelist = glob.glob(searchstring)
        
        #open the IceChart
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
        outraster.SetProjection(firstfile.GetProjection())
    
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

outfilepath = 'C:\\Users\\max\\Documents\\AMSR\\'
filelist = glob.glob(r'C:\Users\max\Documents\AMSR\*.gz')

startyear = 2013
endyear = 2013

startday = 1
startmonth = 1

endday = 4
endmonth = 1

startdate =  datetime.date(startyear, startmonth, startday)
enddate =  datetime.date(endyear, endmonth, endday)
diff = datetime.timedelta(days = 1)
    

for AMSRzipfile in filelist:
    print 'AMSRzipfile'
    #UnzipAMSR(AMSRzipfile)
    #AMSRtoCSV(AMSRzipfile)
    #CSVtoRaster(AMSRzipfile)
    
AverageDaily(startdate, enddate, diff)    
print 'Done ReadAMSR.py'