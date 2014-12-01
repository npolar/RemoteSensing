# -*- coding: utf-8 -*-
"""
Creates Quicklooks from zipped Sentinel-1 or Radarsat-2 files
"""

import zipfile, glob, os, shutil, gdal, fnmatch, pyproj, gdalconst, osr
import Tkinter, tkFileDialog


    
def CreateQuicklook(radarsatfile, outputfilepath):
    '''

    '''
            
    #Various file paths and names:    
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)             
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)        
        
    #Define names of input and outputfile
    #Check if file is Sentinel or Radarsat and use correct NEST file
    if radarsatfileshortname[0:3] == 'RS2':  # RADARSAT-2
        gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
        nestfilename = 'Calib_Spk_reproj_LinDB_Barents.xml'
    if radarsatfileshortname[0:2] == 'S1':   # SENTINEL-1
        gdalsourcefile = radarsatfilepath  +  '\\' + radarsatfileshortname + '.safe' + '\\' + 'manifest.safe'
        nestfilename = 'Spk_reproj_Barents.xml'
  
    outputfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575.dim'

    #Extract the zipfile, skip if corrupt
    try:
        zfile = zipfile.ZipFile(radarsatfile, 'r')
    except:
        return
    print    
    print "Decompressing image for " + radarsatfilename + " on " + radarsatfilepath    
    
    zfile.extractall(radarsatfilepath)
    
    #Call NEST routine
    print
    print "NEST Processing"
    print
    print "inputfile " + radarsatfileshortname
    print "outputfile " + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575.dim'
    print
      
    #check that xml file is correct!
    
    #Process using NEST
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\\' + nestfilename + ' -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
    #Close zipfile
    zfile.close()
    
    #############################################
    # Convert DIM to GEOTIFF and JPEG
    #############################################

    #Get *.img files in dim-folder
    (outputfilenamepath, outputfilename) =  os.path.split(outputfile)
    (outputfileshortname, extension) = os.path.splitext(outputfilename)
    dim_datafolder = outputfilenamepath + '//' + outputfileshortname + '.data'
    if radarsatfileshortname[0:3] == 'RS2':
        dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/Sigma*.img'
    if radarsatfileshortname[0:2] == 'S1':  #Once Sentinel can be calibrated, both will be Sigma*.img
        dim_datafile = outputfilenamepath + '//' + outputfileshortname + '.data/Amplitude*.img'
    dimlist = glob.glob(dim_datafile)
    
    #Loop through Sigma*.img files and convert to GeoTIFF and JPG
    for envifile in dimlist:
        if radarsatfileshortname[0:3] == 'RS2':
            polarisation = envifile[-9:-7]
        if radarsatfileshortname[0:2] == 'S1':    
            polarisation = envifile[-6:-4]
        
        #auxfile is created automatically by NEST, name defined to remove it       
        auxfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif.aux.xml'
        destinationfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        jpegfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.jpg'


        print
        print 'Converting to GeoTIFF: '
        print '\nfrom ' + envifile
        print '\nto ' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        
 
        os.system("gdal_translate -a_srs EPSG:3575 -stats -of GTiff  " + envifile + " " +  destinationfile)
                    
        

            
        #Convert to JPG
        #SCALING MAY NEED TO BE ADJUSTED WHEN NEST FILE CHANGES
        print
        print "create jpeg scene"
        print
        if radarsatfileshortname[0:3] == 'RS2':
             os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile + " " +  jpegfile) 
        
        if radarsatfileshortname[0:2] == 'S1': 
            os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile + " " +  jpegfile) 
        
        #Clean up temp files
        try:
            os.remove(destinationfile)
        except:
            pass
        
        try:
            os.remove(auxfile)
        except:
            pass

    #Clean up temp files    
    
    try:
        shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname + '.SAFE')
    except:
        pass

    try:
        shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname )
    except:
        pass   
    
    shutil.rmtree(dim_datafolder)
    os.remove(outputfile)
    
    print   
       


#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################


# Define filelist to be processed (radarsat zip files)

root = Tkinter.Tk()
root.attributes("-topmost", True)  #puts window on top of Spyder
root.withdraw() #use to hide tkinter window

currdir = os.getcwd()
inputfilepath = tkFileDialog.askdirectory(parent=root, initialdir=currdir, title='Please select a input directory')
outputfilepath = tkFileDialog.askdirectory(parent=root, initialdir=currdir, title='Please select a output directory')
    
#inputfilepath =  'G:\\satellittdata\\flerbrukBarents'
#outputfilepath = 'G:\\satellittdata\\flerbrukBarents'

filelist = []
for root, dirnames, filenames in os.walk(inputfilepath):
  for filename in fnmatch.filter(filenames, '*.zip'):
      filelist.append(os.path.join(root, filename))


#Loop through filelist and process
for radarsatfile in filelist:
    
    #Check if quicklook exists and contains area
    #Get Filename of corresponding quicklook for radarsatfile
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)   
   
    
    print 
    print 'Processing ', radarsatfile 
    print 
    
    #Process image
    CreateQuicklook(radarsatfile, outputfilepath)
    

print 'finished Creating Quicklooks'

#Done