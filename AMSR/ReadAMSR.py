# -*- coding: utf-8 -*-
"""
Created on Mon Jul 14 07:19:33 2014

@author: max
"""

import xml.etree.cElementTree as ET
import glob, gzip

def CreateXML(outfilepath, AMSRzipfile):
    '''
    Creates an XML for every AMSR file
    http://stackoverflow.com/questions/3605680/creating-a-simple-xml-file-using-python
    '''
    
    #Various file paths and names:    
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename) 
    
    Brigthness89 = 'HDF5:'+ AMSRzipfileshortname + '://Brightness_Temperature_(89.0GHz-A,H)'
    Brightness_vrt = outfilepath + AMSRzipfileshortname[:-3] + '.vrt'
    lonfile = 'HDF5:'+ AMSRzipfileshortname + '://Longitude_of_Observation_Point_for_89A'
    latfile = 'HDF5:'+ AMSRzipfileshortname + '://Latitude_of_Observation_Point_for_89A'
    
    
    root = ET.Element("VRTDataset")
    
    root.set("rasterXSize", "486")
    root.set("rasterYSize", "2017")
    
    Metadata = ET.SubElement(root, "Metadata")
    Metadata.set("domain", "GEOLOCATION")
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "X_DATASET")
    MDI.text = outfilepath + AMSRzipfileshortname[:-3] + '_lon.vrt'
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "X_BAND")
    MDI.text = '1'
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "Y_DATASET")
    MDI.text = outfilepath + AMSRzipfileshortname[:-3] + '_lat.vrt'
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "Y_BAND")
    MDI.text = '1'

    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "PIXEL_OFFSET")
    MDI.text = '0'
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "LINE_OFFSET")
    MDI.text = '0'
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "PIXEL_STEP")
    MDI.text = '1'
    
    MDI =  ET.SubElement(Metadata, "MDI")
    MDI.set("key", "LINE_STEP")
    MDI.text = '1'
    
    
    VRTRasterBand = ET.SubElement(root, "VRTRasterBand" )
    VRTRasterBand.set("datatype", "UInt16")
    VRTRasterBand.set("band", "1")
    
    Metadata = ET.SubElement(root, "Metadata")
    
    SimpleSource = ET.SubElement(VRTRasterBand, "SimpleSource")
    
    SourceFilename = ET.SubElement(SimpleSource, "SourceFilename")
    SourceFilename.set("relativeToVRT", "1")
    
    SourceFilename.text = Brigthness89
    SourceBand = ET.SubElement(SimpleSource, "SourceBand")
    SourceBand.text = "1"
    
    SourceProperties = ET.SubElement(SimpleSource, "SourceProperties")
    SourceProperties.set("RasterXSize", "486")
    SourceProperties.set("RasterYSize", "2017")
    SourceProperties.set("DataType", "UInt16")
    SourceProperties.set("BlockXSize", "486")
    SourceProperties.set("BlockYSize", "1")
    
    SrcRect = ET.SubElement(SimpleSource, "SrcRect")
    SrcRect.set("xOff", "0")
    SrcRect.set("yOff", "0")
    SrcRect.set("xSize", "486")
    SrcRect.set("ySize", "2017")
    
    DstRect = ET.SubElement(SimpleSource, "DstRect")
    DstRect.set("xOff", "0")
    DstRect.set("yOff", "0")
    DstRect.set("xSize", "486")
    DstRect.set("ySize", "2017")
    
    tree = ET.ElementTree(root)
    tree.write(Brightness_vrt)

    
    
    
    
    
    
    
    
    
    
    
    
    
    ###Create lon.vrt
    
    root = ET.Element("VRTDataset")
    
    root.set("rasterXSize", "486")
    root.set("rasterYSize", "2017")
    
    VRTRasterBand = ET.SubElement(root, "VRTRasterBand" )
    VRTRasterBand.set("datatype", "Float32")
    VRTRasterBand.set("band", "1")
    
    Metadata = ET.SubElement(VRTRasterBand, "Metadata")
    SimpleSource = ET.SubElement(VRTRasterBand, "SimpleSource")
    
    SourceFilename = ET.SubElement(SimpleSource, "SourceFilename")
    SourceFilename.set("relativeToVRT", "1")
    SourceFilename.text = lonfile
    SourceBand = ET.SubElement(SimpleSource, "SourceBand")
    SourceBand.text = "1"
    
    SourceProperties = ET.SubElement(SimpleSource, "SourceProperties")
    SourceProperties.set("RasterXSize", "486")
    SourceProperties.set("RasterYSize", "2017")
    SourceProperties.set("DataType", "Float32")
    SourceProperties.set("BlockXSize", "486")
    SourceProperties.set("BlockYSize", "1")
    
    SrcRect = ET.SubElement(SimpleSource, "SrcRect")
    SrcRect.set("xOff", "0")
    SrcRect.set("yOff", "0")
    SrcRect.set("xSize", "486")
    SrcRect.set("ySize", "2017")
    
    DstRect = ET.SubElement(SimpleSource, "DstRect")
    DstRect.set("xOff", "0")
    DstRect.set("yOff", "0")
    DstRect.set("xSize", "486")
    DstRect.set("ySize", "2017")
    
    tree = ET.ElementTree(root)
    tree.write(outfilepath + AMSRzipfileshortname[:-3] + '_lon.vrt')
    
    
    
    
    
    
    root = ET.Element("VRTDataset")
    
    root.set("rasterXSize", "486")
    root.set("rasterYSize", "2017")
    
    VRTRasterBand = ET.SubElement(root, "VRTRasterBand" )
    VRTRasterBand.set("datatype", "Float32")
    VRTRasterBand.set("band", "1")
    
    Metadata = ET.SubElement(VRTRasterBand, "Metadata")
    SimpleSource = ET.SubElement(VRTRasterBand, "SimpleSource")
    
    SourceFilename = ET.SubElement(SimpleSource, "SourceFilename")
    SourceFilename.set("relativeToVRT", "1")
    SourceFilename.text = latfile
    SourceBand = ET.SubElement(SimpleSource, "SourceBand")
    SourceBand.text = "1"
    
    SourceProperties = ET.SubElement(SimpleSource, "SourceProperties")
    SourceProperties.set("RasterXSize", "486")
    SourceProperties.set("RasterYSize", "2017")
    SourceProperties.set("DataType", "Float32")
    SourceProperties.set("BlockXSize", "486")
    SourceProperties.set("BlockYSize", "1")
    
    SrcRect = ET.SubElement(SimpleSource, "SrcRect")
    SrcRect.set("xOff", "0")
    SrcRect.set("yOff", "0")
    SrcRect.set("xSize", "486")
    SrcRect.set("ySize", "2017")
    
    DstRect = ET.SubElement(SimpleSource, "DstRect")
    DstRect.set("xOff", "0")
    DstRect.set("yOff", "0")
    DstRect.set("xSize", "486")
    DstRect.set("ySize", "2017")
    
    tree = ET.ElementTree(root)
    tree.write(outfilepath + AMSRzipfileshortname[:-3] + '_lat.vrt')
    
    print "created XML"
    print outfilepath + AMSRzipfileshortname[:-3] + '_lat.vrt'
    print Brightness_vrt
    ###Create lon.vrt
    
def ConvertAMSR(outfilepath, AMSRzipfile):

    #Various file paths and names:    
    (AMSRzipfilepath, AMSRzipfilename) = os.path.split(AMSRzipfile)             
    (AMSRzipfileshortname, extension) = os.path.splitext(AMSRzipfilename) 
    
    print AMSRzipfile
    AMSRzipfile = gzip.open(AMSRzipfile)
    AMSRopened = AMSRzipfile.read()
    AMSRzipfile.close()
    
    AMSRfile = file((outfilepath + AMSRzipfileshortname), 'wb')
    AMSRfile.write(AMSRopened)
    AMSRfile.close()
    
    
    AMSR_vrt = outfilepath + AMSRzipfileshortname[:-3] + '.vrt'
    AMSR_temp_tif = outfilepath + 'temp.tif'
    AMSR_temp2_tif = outfilepath + 'temp2.tif'
    AMSR_tif = outfilepath + AMSRzipfileshortname[:-3] + '.tif'
    
    print AMSR_vrt
    
    print "gdalwarp"
    os.system('gdalwarp -geoloc -t_srs EPSG:4326 ' + AMSR_vrt + ' ' +  AMSR_temp_tif)
    print "gdal_translate"
    os.system('gdal_translate -projwin -94 90 40 35 ' + AMSR_temp_tif + ' ' +   AMSR_temp2_tif)  
    os.system('gdalwarp -s_srs EPSG:4326 -t_srs EPSG:3411 ' + AMSR_temp2_tif + ' ' + AMSR_tif)
    
    #os.remove(AMSR_temp_tif)
    #os.remove(AMSR_temp2_tif)
    
    AMSRfile.close()
    
    
    
    





    
##############################################################################

###   Core of Program follows here ###

##############################################################################

outfilepath = 'C:\\Users\\max\\Documents\\AMSR\\'
filelist = glob.glob(r'C:\Users\max\Documents\AMSR\*.gz')

for AMSRzipfile in filelist:
    
    
    CreateXML(outfilepath, AMSRzipfile)
    ConvertAMSR(outfilepath, AMSRzipfile)

      
    

    