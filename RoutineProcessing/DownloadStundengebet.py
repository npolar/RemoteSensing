# -*- coding: utf-8 -*-
"""
Created on Sun Jan 31 13:14:57 2016

@author: max

Downloads Stundengebet mp3 files from mp3.erzabtei.de
"""


import urllib2, datetime, os

#Define start and stop of download
startdate = datetime.datetime(2016, 1, 26)
stopdate = datetime.datetime(2016, 3, 30)

#define one-day difference in timedelta
nextday = datetime.timedelta(days = 1)

#set the downloaddate to start with startdate
downloaddate = startdate

#weekday list in order to get weekdays from date into filename
weekdays = { 0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5:\
'Sat', 6: 'Sun'}

#Loop through all dates, stopdate + nextday since you want to include stopdate
while downloaddate != (stopdate + nextday):

    #All possible filenames at a given day (regular and feastdays)
    laudes = 'http://mp3.erzabtei.de/' +\
downloaddate.strftime("%Y-%m-%d") + '-' + weekdays[downloaddate.weekday()] + \
'-0540-laudes.mp3'
    laudes0630 = 'http://mp3.erzabtei.de/' +\
downloaddate.strftime("%Y-%m-%d") + '-' + weekdays[downloaddate.weekday()] +\
'-0630-laudes.mp3'
    mittagshore = 'http://mp3.erzabtei.de/' +\
downloaddate.strftime("%Y-%m-%d") + '-' + weekdays[downloaddate.weekday()] +\
'-1200-mittagsgebet.mp3'
    vesper = 'http://mp3.erzabtei.de/' +\
downloaddate.strftime("%Y-%m-%d") + '-' + weekdays[downloaddate.weekday()] +\
'-1800-vesper.mp3'
    vesper1730 = 'http://mp3.erzabtei.de/' +\
downloaddate.strftime("%Y-%m-%d") + '-' + weekdays[downloaddate.weekday()] +\
'-1730-vesper.mp3'
    komplet = 'http://mp3.erzabtei.de/' +\
downloaddate.strftime("%Y-%m-%d") + '-' + weekdays[downloaddate.weekday()] +\
'-2000-komplet.mp3'
    vigil = 'http://mp3.erzabtei.de/' + downloaddate.strftime("%Y-%m-%d")\
+ '-' + weekdays[downloaddate.weekday()] + '-2000-vigil.mp3'

    #List of these possible filenames and loop through this list
    stundengebetlist = {1: laudes, 2: laudes0630, 3:\
mittagshore,4:vesper , 5: vesper1730, 6: komplet, 7: vigil}
    for i in stundengebetlist:
            destinationpath = '//home//max//Music//Erzabtei St. \
Ottilien//201601_Stundengebet//' + stundengebetlist[i].split('/')[-1]   

            if os.path.exists(destinationpath):
                print stundengebetlist[i].split('/')[-1] + " already downloaded."
                continue
            else:
                print "Downloading ", stundengebetlist[i].split('/')[-1]
            

            
            # check if filename exists on web and download if it does
            try:
                downloadfile = urllib2.urlopen(stundengebetlist[i])
                data =  downloadfile.read()
            except:
                print stundengebetlist[i] + " does not exist."
                continue
            # Destination to save the files to
            destinationpath = '//home//max//Music//Erzabtei St. \
Ottilien//201601_Stundengebet//' + stundengebetlist[i].split('/')[-1]
            # Write the download into the destination zipfile
            with open(destinationpath, "wb") as code:
                code.write(data)

    #Add on day to continue with next while loop
    downloaddate = downloaddate + nextday

print "Done downloading"