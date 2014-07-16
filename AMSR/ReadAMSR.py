# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 07:19:33 2014

@author: max
"""
import xml.etree.cElementTree as ET
import gdal, glob, gzip, os, shutil, sys

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
    textfile.write('lon, lat, brightness\n')
    for i in range(rows):
        for j in range(cols):
            lonA = HDF_Lon89A_array[i,j]
            latA = HDF_Lat89A_array[i,j]
            brightnessA = HDF_Br89AH_array[i,j]
            
            lonB = HDF_Lon89B_array[i,j]
            latB = HDF_Lat89B_array[i,j]
            brightnessB = HDF_Br89BH_array[i,j]
            
            if 40 < latA < 90:
                textfile.write(str(lonA) + ', ' + str(latA) + ', ' + str(brightnessA) + '\n')

            if 40 < latB < 90:
                textfile.write(str(lonB) + ', ' + str(latB) + ', ' + str(brightnessB) + '\n')
            
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
    os.system('gdal_grid -a average -l ' + AMSRcsv_shortname + ' '  + AMSRcsv_vrt + ' ' + AMSRcsv_tif)

    
    
    
    


    
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

      
    

    