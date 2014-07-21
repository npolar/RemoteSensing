# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 07:19:33 2014

@author: max
Reads AMSR2 files into the NSIDC raster


"""
import xml.etree.cElementTree as ET
import gdal, glob, gzip, os, shutil, sys, pyproj, datetime


def UnzipAMSR(AMSRzipfile):
    '''
    unzips the AMSRzipfile
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



def AMSRtoCSV(csv_filename, AMSRzipfile):
    '''
    converts AMSR raster to csv
    '''
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename)
    
    
    #Open the hdf file and get subdatasets
    HDFfile = gdal.Open(AMSRzipfilepath + '\\' + AMSRzipfileshortname )
    HDF_bands = HDFfile.GetSubDatasets()
    
    #Open the needed subdatasets, are opened just like a file, are not bands
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
    
    #Get cols rows -- OBS, WILL VARY FOR OTHER CHANNELS!
    cols = HDF_Br89AH.RasterXSize
    rows = HDF_Br89AH.RasterYSize
    
    print 'Convert  ', AMSRzipfileshortname, ' to csv.'    
    
    #Check if csv-file exists    
    if os.path.isfile(csv_filename):
        exists = 1
    else:
        exists = 0
    
    #Open the csv-file, will be created if not exist
    textfile = open( csv_filename, 'a')
    
    #If csv just was created, a header line will be added, otherwise not
    if exists == 0:
        textfile.write("lon,lat,brightness\n")
    
    #Loop through each pixel and write lon, lat, brightness in csv file (converted to EPSG3411) 
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
            
            # only consider this latitude
            if 40 < latA < 90:
                textfile.write(str(lonA_3411) + ',' + str(latA_3411) + ',' + str(brightnessA) + '\n')

            if 40 < latB < 90:
                textfile.write(str(lonB_3411) + ',' + str(latB_3411) + ',' + str(brightnessB) + '\n')
            
    textfile.close()
    
    
    
def CSVtoRaster(csv_filename):
    '''
    converts CSV raster to raster
    
    
    
    
    '''
    
    (csv_filenamepath, filename) = os.path.split(csv_filename)             
    (csv_filename_shortname, extension) = os.path.splitext(filename)

         
    AMSRcsv_vrt = csv_filenamepath + '\\' + csv_filename_shortname + '.vrt'    
    ##############################
    #Create the necessary XML file
    ##############################
    root = ET.Element("OGRVRTDataSource")
    OGRVRTLayer  = ET.SubElement(root, "OGRVRTLayer")
    OGRVRTLayer.set("name", csv_filename_shortname)
    
    SrcDataSource = ET.SubElement(OGRVRTLayer, "SrcDataSource")
    SrcDataSource.text = csv_filename
    
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
    
    
    AMSR_tif = outfilepath + csv_filename_shortname + '.tif'
    
    AMSR_quart1_3411_tif = outfilepath + 'quart1_3411.tif'
    AMSR_quart2_3411_tif = outfilepath + 'quart2_3411.tif'
    AMSR_quart3_3411_tif = outfilepath + 'quart3_3411.tif'
    AMSR_quart4_3411_tif = outfilepath + 'quart4_3411.tif'
    
    # Extent of NSIDC grid, outsize determines resolution
    #  5km => -outsize 1520 2240
    # 10km =>
    #os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=4000:radius2=4000:min_points=1 -txe -3850000 3750000 -tye -5350000 5850000 -outsize 1520 2240 -l ' + csv_filename_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_tif)
    
    
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=4000:radius2=4000:min_points=1 -txe -3850000 0 -tye 0 5850000 -outsize 1520 2240 -l ' + csv_filename_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_quart1_3411_tif)
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=4000:radius2=4000:min_points=1 -txe 0 3750000 -tye 0 5850000 -outsize 1520 2240 -l ' + csv_filename_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_quart1_3411_tif)
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=4000:radius2=4000:min_points=1 -txe -3850000 0 -tye -5350000 0 -outsize 1520 2240 -l ' + csv_filename_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_quart1_3411_tif)
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=4000:radius2=4000:min_points=1 -txe -0 3750000 -tye -5350000 0 -outsize 1520 2240 -l ' + csv_filename_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_quart1_3411_tif)
    
    os.system('gdal_merge.py -tap -n 0 -o ' + AMSR_tif + ' ' + AMSR_quart1_3411_tif + ' ' + AMSR_quart2_3411_tif + ' ' + AMSR_quart3_3411_tif + ' ' + AMSR_quart4_3411_tif)


    
##############################################################################

###   Core of Program follows here ###

##############################################################################
outfilepath = 'C:\\Users\\max\\Documents\\AMSR\\'

startyear = 2013
endyear = 2013

startday = 1
startmonth = 1

endday = 31
endmonth = 1

startdate =  datetime.date(startyear, startmonth, startday)
enddate =  datetime.date(endyear, endmonth, endday)
diff = datetime.timedelta(days = 1)

#initiate workingdate
workingdate = startdate


while workingdate != (enddate + diff):
    #Create filelist with all files having the same date, e.g. 20130101
    searchstring = 'C:\Users\max\Documents\AMSR\GW1AM2_' + str(workingdate.strftime("%Y%m%d")) + '*.gz'
    filelist = glob.glob(searchstring)
    
    #Process AMSR with this filelist
    for AMSRzipfile in filelist:
    
        UnzipAMSR(AMSRzipfile)
        csv_filename = 'C:\Users\max\Documents\AMSR\GW1AM2_' + str(workingdate.strftime("%Y%m%d")) + '.csv'
        # AMSR is converted to csv and appended to one csv file from the same month
        # make sure that "a" is selected in AMSRtoCSV
        AMSRtoCSV(csv_filename, AMSRzipfile)
    
    # csv is rasterized for all files from one month
    CSVtoRaster(csv_filename) 
    #os.remove(csv_filename) #Remove the very big csv-file
    # Go to next day and repeat while loop
    workingdate = workingdate + diff
    print ' Now processing ', workingdate
    
     
print 'Done ReadAMSR.py'

      
    

    