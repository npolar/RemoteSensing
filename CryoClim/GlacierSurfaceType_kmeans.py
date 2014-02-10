# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 09:04:29 2013

@author: max

Classification into Glacier Surface Types

    Steps:        
    #Make Raster from shapefile
    RasterizeMask(inshapefile)
    
    #Crop SAR file to extents of shapefile
    CropGlacier(inshapefile, inSARfile)

    #Masks Area outside glacier with no data value -999.0    
    MaskGlacier(inshapefile, inSARfile)
    
    #Convert image values to range 0 to 1 for Otsu input
    scaleimage(inSARcrop)
    
    #Call Otsu's method
    (thresh1, thresh2) = otsu3(inSARcrop)
    
    #Apply the thresholds gotten by Otsu
    classify_image(inSARcrop, thresh1, thresh2)
    
    #Apply Sieve filter to remove noise
    ApplySieve(inSARcrop)
    
    #Convert GST raster to GST shapefile
    PolygonizeGST(inSARcrop)

"""

#import modules

import ogr, os, gdal, numpy, glob, shutil
import matplotlib.pyplot as plt
from scipy.cluster.vq import kmeans,vq


# Define Functions

def RasterizeMask(infile):
    '''
    Takes infile and creates raster from shapefile
    '''
    
    # Define filenames
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    outraster = infilepath + '/' + infileshortname + '.tif'    
        
    # Rasterize mask and at same time create file -- call gdal_rasterize commandline
    print '\n Rasterize ', infilename
    os.system('gdal_rasterize -burn 2 -l ' + infileshortname +' -tr 20.0 -20.0 ' +  infile + ' ' + outraster)
    



def CropGlacier(inshapefile, inSARfile):
    '''
    Crops SAR image to extent of Mask, i.e. glacier extent
    
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    outraster = inSARfilepath + '/' + inSARfileshortname + '_GST.tif'
    outraster2 = inSARfilepath + '/' + inSARfileshortname + '_SAR.tif'
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    #Register driver and open file
    shapedriver = ogr.GetDriverByName('ESRI Shapefile')   
    maskshape = shapedriver.Open(inshapefile, 0)
    if maskshape is None:
        print 'Could not open ', inshapefilename
        return
        
    #Get Extension of Layer
    masklayer = maskshape.GetLayer()
    maskextent = masklayer.GetExtent()
    print 'Extent of ', inshapefilename, ': '
    print maskextent
    print 'UL: ', maskextent[0], maskextent[3]
    print 'LR: ', maskextent[1], maskextent[2]

    # crop image with gdal_translate -- call gdal_rasterize commandline
    print '\n Subsetting maskfile ', inSARfilename, ' to glacier extent'
    os.system('gdal_translate -projwin ' + str(maskextent[0]) + ' ' + str(maskextent[3]) + ' ' + str(maskextent[1]) + ' ' + str(maskextent[2]) + ' ' + inSARfile + ' ' + outraster)
    
    # crop second image to keep with gdal_translate -- call gdal_rasterize commandline
    print '\n Subsetting SARfile ', inSARfilename, ' to glacier extent'
    os.system('gdal_translate -projwin ' + str(maskextent[0]) + ' ' + str(maskextent[3]) + ' ' + str(maskextent[1]) + ' ' + str(maskextent[2]) + ' ' + inSARfile + ' ' + outraster2)
    
    #Close files 
    maskshape = None
    
def MaskGlacier(inshapefile, inSARfile):
    '''
    Masks Cropped SARfile
    
    Sets all values outside mask to -999.0 no data value. The same file will receive classification
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '/' + inSARfileshortname + '_GST.tif'
    
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    inshapeasraster = inshapefilepath + '/' + inshapefileshortname + '.tif'
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(inSARcrop, gdal.GA_Update)
    mask = gdal.Open(inshapeasraster, gdal.GA_ReadOnly)
    dsband = ds.GetRasterBand(1)
  
    #Read input raster into array
    glacierraster = ds.ReadAsArray()
    maskraster = mask.ReadAsArray()
        
    #get image size
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    
    #Process the image
    print 'Masking ', inSARcrop
    for i in range(rows):
        for j in range(cols):
            if maskraster[i,j] == 2.0:
                glacierraster[i,j] = glacierraster[i,j]
            else:
                glacierraster[i,j] = -999.0
    
    # Set NoData Value
    dsband.SetNoDataValue(-999.0)
           
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()        
    
    #make a copy to keep the masked SAR
    maskedSAR = inSARfilepath + '/' + inSARfileshortname + '_SARmask.tif'
    shutil.copyfile(inSARcrop, maskedSAR)    
    
    #Close file
    mask = None
    ds = None

def scaleimage(infile):
    '''
    scale values from 0 to 1, needed by Otsu input requirement
    '''
      
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    
    #Read input raster into array
    glacierraster = ds.ReadAsArray()
    
    #get image max and min and calculate new range
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    stats = dsband.GetStatistics(0,1)
    
    
    OldMin = stats[0]
    OldMax = stats[1]
  
    NewMin = 0.0
    NewMax = 1.0
    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)
    
    #Process the image
    print 'Converting Range to 0-1 for ', infile
    for i in range(rows):
        for j in range(cols):
            if glacierraster[i,j] == -999.0:
                pass
            else:
                glacierraster[i,j] = (((glacierraster[i,j] - OldMin) * NewRange) / OldRange) + NewMin
    
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()        
    
    #Close file
    dsband = None
    glacierraster = None
    ds = None  

    #Load infile again and calculate new stats (not sure how to get from raster)    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    stats = dsband.GetStatistics(0,1)
    (newmin, newmax)= dsband.ComputeRasterMinMax(0)
    (newmean, newstdv) = dsband.ComputeBandStats(1)
    dsband.SetStatistics(newmin, newmax,newmean, newstdv)
    dsband.FlushCache()       
    dsband = None  
    ds = None
    return OldMin, OldMax
          
    
def classify_kmeans(infile, clusternumber):
    '''
    apply kmeans
    '''
    
    #Load infile in data array    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    databand = ds.GetRasterBand(1)
    
    #Read input raster into array
    data = ds.ReadAsArray() 
    #replace no data value with numpy.nan
    #data[data==-999.0]=numpy.nan 
    
    pixel = numpy.reshape(data,(data.shape[0]*data.shape[1]))
    centroids, variance = kmeans(pixel, clusternumber)
    code, distance = vq(pixel,centroids)
    centers_idx = numpy.reshape(code,(data.shape[0],data.shape[1]))
    clustered = centroids[centers_idx]
    
    # Write outraster to file
    databand.WriteArray(clustered)
    databand.FlushCache()        
    
    #Close file
    databand = None
    clustered = None
    ds = None  
    
   
     
     

def classify_image(infile, thresh1):
    '''
    classify image with kmeans thresholds
    '''
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    
    #Read input raster into array
    glacierraster = ds.ReadAsArray()
    
    
    #get image max and min and calculate new range
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    
    #Process the image
    print 'Classifying ', infile
    for i in range(rows):
        for j in range(cols):
            if 0.0 <= glacierraster[i,j] < thresh1:
                glacierraster[i,j] = 1.0
            elif thresh1 <= glacierraster[i,j] <= 1.0:
                glacierraster[i,j] = 3.0
            else:
                glacierraster[i,j] = -999.0
    
   
    # Write outraster to file
    dsband.WriteArray(glacierraster)
    dsband.FlushCache()
    dsband.GetStatistics(0,1)
    
    
    #Close file
    dsband = None
    glacierraster = None
    ds = None  
    
    #Load infile again and calculate new stats (not sure how to get from raster)    
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(infile, gdal.GA_Update)
    dsband = ds.GetRasterBand(1)
    (newmin, newmax)= dsband.ComputeRasterMinMax(0)
    (newmean, newstdv) = dsband.ComputeBandStats(1)
    dsband.SetStatistics(newmin, newmax,newmean, newstdv)
    dsband.FlushCache()       
    dsband = None  
    ds = None


def ApplySieve(infile):
    '''
    applies gdal_sieve
        * 4-connectedness seemed best, 8 removes too muc
        * 60 filter seemed ok
    
    '''    
    
    print '\n Apply gdal_sieve'
    #os.system('gdal_rasterize -a ICE_TYPE -where \"ICE_TYPE=\'Open Water\'\" -burn 2 -l ' + shapefileshortname +' -tr 1000 -1000 ' +  shapefile + ' ' + outraster)
    os.system('gdal_sieve.py -st 60 -4 -of GTiff ' + infile)
            
    

def PolygonizeGST(infile):
    '''
    creates shapefile out of GST raster
    '''
    (infilepath, infilename) = os.path.split(infile)             #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    outfile = infilepath + '/' + infileshortname + '.shp'    
    
    print '\n Convert ', infile, ' to shapefile.'
    os.system('gdal_polygonize.py ' + infile + ' -f "ESRI Shapefile" ' + outfile)    
    
def PlotHistogram(infile, thresh1):
    ''' plots histogram '''
    
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '/' + inSARfileshortname + '_SARmask.tif'
    histfilename = inSARfilepath + '/' + inSARfileshortname + '_hist.jpg'
    
    #Open Rasterfile and Mask
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    ds = gdal.Open(inSARcrop, gdal.GA_Update)
    raster = ds.ReadAsArray()
    
    plt.figure()
    plt.hist(raster.flatten(), 128, range = (-25.0, 10.0))
    plt.axvline(x=thresh1, ymin=0, ymax=6000, linewidth=1, color='r')
    plt.title(inSARfileshortname)
    
    plt.savefig(histfilename)

def RenameFiles(inshapefile):
    '''
    rename all files produced
    works for mosaicXXXX.tif in F:\SvalbardSARbyYear\*.tif
    very simple, no universal method -- dependent on file location as given
    '''
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
        
    (inshapefilepath, inshapefilename) = os.path.split(inshapefile)             #get path and filename seperately
    (inshapefileshortname, inshapeextension) = os.path.splitext(inshapefilename)
    
    glaciername = inshapefileshortname[0:-11]
       
    print 'renaming files'
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.tif')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)        
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.tif'
        os.rename(oldname, newname )
        
    filelist = glob.glob('F:\SvalbardSARbyYear\*SAR.tif')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_SAR.tif'
        os.rename(oldname, newname )

    filelist = glob.glob('F:\SvalbardSARbyYear\*SARmask.tif')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_SARmask.tif'
        os.rename(oldname, newname )
        
    filelist = glob.glob('F:\SvalbardSARbyYear\*hist.jpg')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_hist.jpg'
        os.rename(oldname, newname )
    
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.dbf')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.dbf'
        os.rename(oldname, newname )   
        
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.prj')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.prj'
        os.rename(oldname, newname ) 
    
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.shx')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.shx'
        os.rename(oldname, newname ) 
     
    filelist = glob.glob('F:\SvalbardSARbyYear\*GST.shp')
    for processfile in filelist:
        year = processfile[27:31]
        oldname = str(processfile)
        newname = inSARfilepath + '//'+ glaciername + str(year) + '_GST.shp'
        os.rename(oldname, newname )
        
        
#Core of Program follows

#Define location and name of glaciermask
inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\KongsvegenBuffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Monacobreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Lilliehookbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Fjortendejulibreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\AustreBroggerbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Hansbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Hayesbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Ulvebreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Uversbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Comfortlessbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Etonbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Holtedalfonna2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Aavatsmarkbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Osbornebreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Wahlenbergbreen2000_Buffer.shp'
#inshapefile = 'C:\Users\max\Documents\Svalbard\glaciermasks\Kuhrbreen2000_Buffer.shp'




# Define location and name of GeoTIFF containing SAR image
# Convert from BEAM-DIMAP with Nest>Graphs>Batch Processing 

filelist = glob.glob('F:\SvalbardSARbyYear\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\Kongsfjorden\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\SouthSpitsbergen\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\CentralSpitsbergen\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')
#filelist = glob.glob('S:\CryoClimValidation\Nordaustlandet\AppOrb_Calib_Spk_SarsimTC_LinDB\GeoTIFF\*.tif')


#Iterate through filelist with SAR files
for inSARfile in filelist:
    
    # Define filenames
    (inSARfilepath, inSARfilename) = os.path.split(inSARfile)             #get path and filename seperately
    (inSARfileshortname, inSARextension) = os.path.splitext(inSARfilename)
    inSARcrop = inSARfilepath + '\\' + inSARfileshortname + '_GST.tif'
    
    #Make Raster from shapefile
    RasterizeMask(inshapefile)
    
    #Crop SAR file to extents of shapefile
    CropGlacier(inshapefile, inSARfile)

    #Masks Area outside glacier with no data value -999.0    
    MaskGlacier(inshapefile, inSARfile)
    
    
    #Call Otsu's method
    clusternumber = 4
    classify_kmeans(inSARcrop, clusternumber)
    print 'Calculate kmeans '
    print
       
    #Apply Sieve filter to remove noise
    ApplySieve(inSARcrop)
    
    #Convert GST raster to GST shapefile
    PolygonizeGST(inSARcrop)
    
#end for

#rename files
RenameFiles(inshapefile)


print
print "Done"


