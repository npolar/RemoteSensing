# -*- coding: utf-8 -*-
"""
Created on Tue Oct 21 09:18:01 2014

@author: max
"""

# -*- coding: utf-8 -*-
"""
Created on August 2013

Extracts Radarsat and Sentinel scenes.
Then calibrate and project image to EPSG:3575 as GeoTIFF and JPG


"""

import zipfile, glob, os, shutil, gdal, fnmatch, pyproj, gdalconst, osr
from Tkinter import *
from tkFileDialog import *

  
def ProcessNest(radarsatfile, outputfilepath):
    '''
    Calls Nest SAR Toolbox to calibrate, map project and if wanted 
    terraincorrect images
    see http://nest.array.ca/
    
    needed Nest files at https://github.com/npolar/RemoteSensing/tree/master/Nest
    
    converts afterwards to GeoTIFF and JPEG clipped to extents of Svalbard DEM
    
    Map projection Svalbard EPSG:32633 UTM 33N
    Map Projection Barents Sea EPSG:3575
    '''
            
    #Various file paths and names:    
    (radarsatfilepath, radarsatfilename) = os.path.split(radarsatfile)             
    (radarsatfileshortname, extension) = os.path.splitext(radarsatfilename)        
        
    #Define names of input and outputfile
        
    if radarsatfileshortname[0:3] == 'RS2':  # RADARSAT-2
        gdalsourcefile = radarsatfilepath + '\\' + radarsatfileshortname + '\\product.xml'
        nestfilename = 'Calib_Spk_TC_LinDB_Barents.xml'
    if radarsatfileshortname[0:2] == 'S1':   # SENTINEL-1
        gdalsourcefile = radarsatfilepath  +  '\\' + radarsatfileshortname + '.safe' + '\\' + 'manifest.safe'
        nestfilename = 'Calib_Spk_TC_LinDB_Sentinel.xml'
  
    outputfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575.dim'

    #Extract the zipfile
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
    #os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\Calib_Spk_reproj_LinDB_Barents.xml -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    os.system(r'gpt C:\Users\max\Documents\PythonProjects\Nest\\' + nestfilename + ' -Pfile=" ' + gdalsourcefile + '"  -Tfile="'+ outputfile + '"' )
    
    #Remove folder where extracted and temporary files are stored
    #shutil.rmtree(radarsatfilepath + '\\' + radarsatfileshortname )

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
            
        destinationfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_temp.tif'
        #auxfile is created automatically by NEST, name defined to remove it       
        auxfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif.aux.xml'
        destinationfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        destinationfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_SUBSET.tif'
        jpegfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.jpg'
        jpegfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_SUBSET.jpg'
        
        jpegsmallfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_40percent.jpg'
        jpegsmallfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_10percent.jpg'
        jpegsmallfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_20percent.jpg'
        jpegsmallfile4 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_30percent.jpg'
        jpegsmallfile5 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_50percent.jpg'
        
        tiffsmallfile = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_40percent.tif'
        tiffsmallfile2 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_10percent.tif'
        tiffsmallfile3 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_20percent.tif'
        tiffsmallfile4 = outputfilepath + '\\' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '_30percent.tif'
        
        print
        print 'Converting to GeoTIFF: '
        print '\nfrom ' + envifile
        print '\nto ' + radarsatfileshortname + '_Cal_Spk_reproj_EPSG3575_' + polarisation + '.tif'
        
 
        os.system("gdal_translate -a_srs EPSG:3575 -stats -of GTiff  " + envifile + " " +  destinationfile2)
                    
        
        if location != []:
            print
            print "subsetting the scene"
            print
            
            
            upperleft_x = location[0]
            upperleft_y = location[1]
            lowerright_x = location[2]
            lowerright_y = location[3]       
            if radarsatfileshortname[0:3] == 'RS2':
                os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of GTiff -projwin " + str(upperleft_x)  + " " + str(upperleft_y)  + " " + str(lowerright_x)  + " " + str(lowerright_y)  + " " + destinationfile2 + " " +  destinationfile3)
        
            if radarsatfileshortname[0:2] == 'S1': 
                os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of GTiff -projwin " + str(upperleft_x)  + " " + str(upperleft_y)  + " " + str(lowerright_x)  + " " + str(lowerright_y)  + " " + destinationfile2 + " " +  destinationfile3)
          
            #Convert to JPG
            print
            print "create jpeg scene"
            print
            if radarsatfileshortname[0:3] == 'RS2':
                os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile3 + " " +  jpegfile3) 
        
            if radarsatfileshortname[0:2] == 'S1': 
                os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile3 + " " +  jpegfile3) 
        else:
            
            #Convert to JPG
            print
            print "create jpeg scene"
            print
            if radarsatfileshortname[0:3] == 'RS2':
                os.system("gdal_translate -scale -30 0 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
            if radarsatfileshortname[0:2] == 'S1': 
                os.system("gdal_translate -scale 0 500 0 255 -ot Byte -co WORLDFILE=YES -of JPEG " + destinationfile2 + " " +  jpegfile) 
        
        #Create small jpeg --- THESE ARE CREATED FOR FIELD WORK TRANSFER ONLY DURING FIELD WORK
        #os.system("gdal_translate -outsize 40% 40% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile)
        #os.system("gdal_translate -outsize 10% 10% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile2)
        #os.system("gdal_translate -outsize 20% 20% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile3)
        #os.system("gdal_translate -outsize 30% 30% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile4)
        #os.system("gdal_translate -outsize 50% 50% -co WORLDFILE=YES -of JPEG " + jpegfile + " " + jpegsmallfile5)
        
        #Create small jpeg --- THESE ARE CREATED FOR FIELD WORK TRANSFER ONLY DURING FIELD WORK
        #os.system("gdal_translate -ot Int16 -co COMPRESS=DEFLATE -co PREDICTOR=2 -co ZLEVEL=9 -outsize 40% 40% -of GTiff " + destinationfile2 + " " + tiffsmallfile)
        #os.system("gdal_translate -outsize 10% 10%  -of GTiff " + destinationfile2 + " " + tiffsmallfile2)
        #os.system("gdal_translate -outsize 20% 20%  -of GTiff " + destinationfile2 + " " + tiffsmallfile3)
        #os.system("gdal_translate -outsize 30% 30%  -of GTiff " + destinationfile2 + " " + tiffsmallfile4)
    
        #Remove original GeoTIFF in 3033 since we now have 3575        
        try:
            os.remove(destinationfile)
        except:
            pass
        
        #os.remove(auxfile)
    

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

    
       
class TheGui:
    def __init__(self, parent):
        #------- frmSetup ----------#

        #------- frmSetup ----------#

        sep = Frame(parent, width=1, bd=5, bg='black')
        sep.pack(fill=X, expand=1)
        
 

        #------- frmIn ----------#
        # http://effbot.org/tkinterbook/tkinter-widget-styling.htm
        self.frmIn = Frame(parent, bd=5)
        self.frmIn.pack()

        self.lblIn = Label(self.frmIn, text=' Input File Path', width=20)
        self.lblIn.pack(side=LEFT)  

        self.inFilePath = StringVar() # http://effbot.org/tkinterbook/entry.htm
        self.entIn = Entry(self.frmIn, width=60, textvariable=self.inFilePath)
        self.entIn.pack(side=LEFT)

        self.btnIn = Button(self.frmIn, text='Browse', command=self.btnInBrowseClick)
        self.btnIn.pack(side=LEFT)
        #------- frmIn ----------#

        #------- frmOut ----------#
        self.frmOut = Frame(parent, bd=5)
        self.frmOut.pack()

        self.lblOut = Label(self.frmOut, text=' Output File Path', width=20)
        self.lblOut.pack(side=LEFT) 

        self.outFilePath = StringVar()
        self.entOut = Entry(self.frmOut, width=60, textvariable=self.outFilePath)
        self.entOut.pack(side=LEFT) 

        self.btnOut = Button(self.frmOut, text='Browse', command=self.btnOutBrowseClick)
        self.btnOut.pack(side=LEFT)
        #------- frmOut ----------#

        sep = Frame(parent, width=1, bd=5, bg='black')
        sep.pack(fill=X, expand=1)

        #------- frmButtons ----------#
        self.frmOut = Frame(parent, bd=5)
        self.frmOut.pack()

        self.btnConvert = Button(self.frmOut, text='Process SAR', command=self.btnConvertClick)
        self.btnConvert.pack()  

    #------- handle commands ----------#

    def btnInBrowseClick(self):
        rFilepath = askdirectory(
            initialdir='.', parent=self.frmIn, title='select input folder RS-2 and Sent-1')
        value_dict['inputfilepath'] =  rFilepath
        self.inFilePath.set(rFilepath)
        print self.entIn.get()

    def btnOutBrowseClick(self):
        rFilepath = askdirectory(
            initialdir='.', parent=self.frmIn, title='select output folder')
        value_dict['outputfilepath'] =  rFilepath
        self.outFilePath.set(rFilepath)
        print self.entOut.get()

    def btnConvertClick(self):
        #defClr = self.btnConvert.cget("bg")
        self.btnConvert.config(relief=SUNKEN)
        self.btnConvert.update()
        #print 'Convert from %s to %s' % (self.inChoices[self.varRadio.get()], self.inChoices[(self.varRadio.get()+1)%2])
        inputfilepath = str(self.inFilePath.get())
        outputfilepath = str(self.outFilePath.get())
        #LoopFiles(inputfilepath,outputfilepath)

        #time.sleep(0.5)
        self.btnConvert.config(relief=RAISED)
        self.btnConvert.update()
        root.destroy()






#############################################################
# CORE OF PROGRAM FOLLOWS HERE
#############################################################

#Defining a dictionary whose variable ths GUI will collect
value_dict = {'inputfilepath': 'G:\\satellittdata\\flerbrukBarents', 'outputfilepath': 'G:\\satellittdata\\flerbrukBarents'}

#Start the GUI    
root = Tk()
root.title("Process Sentinel and Radarsat Files")
root.attributes("-topmost", True)

root.geometry("800x200+10+10")
gui = TheGui(root)
root.mainloop()

#Once the GUI quits continue main programm using GUI collected values in Dictionary
inputfilepath = value_dict['inputfilepath']
outputfilepath = value_dict['outputfilepath']

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
    ProcessNest(radarsatfile, outputfilepath)
    
    #Remove quicklook as jpeg no available
    #try:
    #    os.remove(outputfile)
    #except:
    #    pass

print 'finished extracting Barents images'

