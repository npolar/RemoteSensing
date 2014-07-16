# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 07:19:33 2014

@author: max
"""
import xml.etree.cElementTree as ET
import gdal, glob, gzip, os, shutil, sys, pyproj

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
            brightnessA = HDF_Br89AH_array[i,j]
            
            lonB = HDF_Lon89B_array[i,j]
            latB = HDF_Lat89B_array[i,j]
            (lonB_3411, latB_3411) = pyproj.transform(wgs84, EPSG3411, lonB, latB)
            brightnessB = HDF_Br89BH_array[i,j]
            
            if 40 < latA < 90:
                textfile.write(str(lonA_3411) + ',' + str(latA_3411) + ',' + str(brightnessA) + '\n')

            if 40 < latB < 90:
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
    os.system('gdal_grid -a_srs EPSG:3411 -a average:radius1=5000:radius2=5000:min_points=1 -txe -3850000 3750000 -tye -5350000 5850000 -outsize 1520 2240 -l ' + AMSRcsv_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSR_tif)
    
#    

    
    
    
    


    
##############################################################################

###   Core of Program follows here ###

##############################################################################

outfilepath = 'C:\\Users\\max\\Documents\\AMSR\\'
filelist = glob.glob(r'C:\Users\max\Documents\AMSR\GW1AM2_201301010158_201D_L1SGBTBR_1110110*.gz')

for AMSRzipfile in filelist:
    
    UnzipAMSR(AMSRzipfile)
    AMSRtoCSV(AMSRzipfile)
    CSVtoRaster(AMSRzipfile)
    
    
print 'Done ReadAMSR.py'

      
    

    