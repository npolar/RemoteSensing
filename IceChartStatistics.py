# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 10:30:16 2013

@author: max
"""

# Import Modules
import  os, sys, glob, gdal, gdalconst


#Defining Functions

def CountIcetype(infile):
    '''
    Count pixels of a given number=days of fast ice
    '''
    
    #Define filenames
    (infilepath, infilename) =  os.path.split(infile)       #get path and filename seperately
    (infileshortname, extension) = os.path.splitext(infilename)
    
    (outputfilepath, directory)  = os.path.split(infilepath)
    outputtextfile = outputfilepath + '\\' + infileshortname + '_Count.txt'
    
    # register all of the GDAL drivers
    gdal.AllRegister()
    
    # open the image
    ds = gdal.Open(infile, gdalconst.GA_ReadOnly)
    if ds is None:
        print 'Could not open ', infileshortname
        sys.exit(1)

    # get image size
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    totalpixels = rows * cols

    #Read input raster into array
    iceraster = ds.ReadAsArray()
    
    # initialize variable
    noice = 0
    oneweek = 0
    twoweek = 0
    threeweek = 0
    fourweek = 0
    fiveweek = 0
    sixweek = 0
    sevenweek = 0
    eightweek = 0
    land = 0
    
       
    #Process the image
    print 'stats for ', infile    
    
    for i in range(rows):
        for j in range(cols):
            if iceraster[i,j] == 0:
                noice = noice + 1
            elif 0 < iceraster[i,j] < 8:
                oneweek = oneweek + 1
            elif 7 < iceraster[i,j] < 15:
                twoweek = twoweek + 1
            elif 14 < iceraster[i,j] < 22:
                threeweek = threeweek + 1
            elif 21 < iceraster[i,j] < 29:
                fourweek = fourweek + 1
            elif 28 < iceraster[i,j] < 36:
                fiveweek = fiveweek + 1
            elif 35 < iceraster[i,j] < 43:
                sixweek = sixweek + 1
            elif 42 < iceraster[i,j] < 50:
                sevenweek = sevenweek + 1
            elif 49 < iceraster[i,j] < 57:
                eightweek = eightweek + 1
            elif iceraster[i,j] == 999:
                land = land + 1
            else:
                pass
            
    #Write Results to textfile
    print 'Writing to ', outputtextfile 
    textfile = open( outputtextfile, 'w')
    textfile.write('Number of pixels, Resolution 100m = 10000m2 \n')
    textfile.write( 'rows: ' + str(rows) + ' cols: '+ str(cols) + ' \n\n' )
    textfile.write('    0 days: \t' + str(noice) + '\n')
    textfile.write('  1-7 days: \t' + str(oneweek) + '\n')
    textfile.write(' 8-14 days: \t' + str(twoweek) + '\n')
    textfile.write('15-21 days: \t' + str(threeweek) + '\n')
    textfile.write('22-28 days: \t' + str(fourweek) + '\n')
    textfile.write('29-35 days: \t' + str(fiveweek) + '\n')
    textfile.write('36-42 days: \t' + str(sixweek) + '\n')
    textfile.write('43-49 days: \t' + str(sevenweek) + '\n')
    textfile.write('50-57 days: \t' + str(eightweek) + '\n')
    textfile.write(' land area: \t' + str(land) + '\n\n ')
    textfile.write('Total Pixels: \t' + str(totalpixels) + '\n')
    
    textfile.close()

    #Close files
    ds = None
    

    
#Core of Program

infilepath = 'G:\Icecharts\Data\\Kit'
outfilepath = 'G:\Icecharts\Data'

# Iterate through all shapefiles
filelist = glob.glob('G:\Icecharts\Data\*\icechart_processed*.tif')

for icechart in filelist:
    
    CountIcetype(icechart)
    
    