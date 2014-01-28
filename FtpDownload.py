# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 08:30:13 2014

@author: max
"""

import ftplib, os


#DEFINE FTP SERVER PARAMETERS
ftpserver = 'ftp3.ksat.no'
username = "delivery"
password = "9Wqm8ZhWMnE2"
workingfolder = '//customers/cache/sathav/'

#ftpserver = 'ftp.npolar.no'
#username = 'anonymous'
#password = 'guest'
#workingfolder = '/Out/max/'

#temporary file storing location info from quicklook
output_tempfile = 'C:\Users\max\Desktop\\test.txt'
#destinationfolder for download
destination_folder = 'C:\Users\max\Documents\\'

#Open ftp
ftp = ftplib.FTP(ftpserver, username , password)
ftp.cwd(workingfolder)

#Create a file list of all quicklooks
filelist = []

try:
    filelist = ftp.nlst('*.tif')
except ftplib.error_perm, resp:
    if str(resp) == "550 No files found":
        print "No files in this directory"
    else:
        raise

for file in filelist:
    
    #get quicklook file info and save in temporary file
    os.system(r'gdalinfo /vsicurl/ftp://' + username + ':' + password + "@" + ftpserver + workingfolder + file + ' > ' + output_tempfile)
    
    #Read from temporary file the centre coordinates of the quicklook    
    search = open(output_tempfile)

    for line in search:
        if "Center" in line:
            longitude_quicklook =  float(line[15:25])
        
            latitude_quicklook =  float(line[28:38])
        
        
    search.close()

    print 'Longitude ', longitude_quicklook
    print 'Latitude ', latitude_quicklook       


    #Check if scene is contained in area of interest, divided in two areas since not rectangular
    if ((-23.0 < longitude_quicklook < 67.0) and (71.0 < latitude_quicklook < 90.0)):
        contained = True
        print 'true'
    elif ((-33.0 < longitude_quicklook < 14.0) and (66.0 < latitude_quicklook < 71.0)):
        contained = True
        print 'true'
    else:
        contained = False

 
    zipfile = file[:-7] + '.zip'
    zipsavefile = destination_folder + file[:-7] + '.zip'
    
    print zipfile
    print zipsavefile
    
    #If file contained in area of interest, download the file
    if contained == True:
        print 'transferring ', zipfile
        ftp.cwd(workingfolder)
        ftp.retrbinary('RETR ' + zipfile, open(zipsavefile, 'wb').write)
        print 'transferred ', zipfile
        
    ftp.quit()
        
#Remove temporary file
os.remove(r'C:\Users\max\Desktop\test.txt')

#End




















