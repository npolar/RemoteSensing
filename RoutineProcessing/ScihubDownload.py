# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 09:57:19 2015

@author: max
"""

import urllib2, urllib
import xml.etree.ElementTree as etree

# Hard coded link returning list of matching scenes
# https://scihub.esa.int/twiki/do/view/SciHubUserGuide/5APIsAndBatchScripting#Open_Search

# Authenticate at scihub webpage
url =  'https://scihub.esa.int/dhus/'
username = 'your_username'
password = 'your_password'
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

password_mgr.add_password(None, url, username, password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)

# The request query
urlrequest = urllib.quote('https://scihub.esa.int/dhus/search?q=productType:GRD AND ingestionDate:[2015-09-30T00:00:00.000Z TO 2015-09-30T23:59:59.999Z] AND footprint:"Intersects(POLYGON((-16.11154750824 69.190260085686,-2.7521725082398 69.190260085686,-2.7521725082398 76.370271635301,-16.11154750824 76.370271635301,-16.11154750824 69.190260085686)))"&rows=10000&start=0', ':()[]/?=,&')
# Read the response into page and write it to a xml-file
page = urllib2.urlopen(urlrequest).read()
textfile = open('/home/max/Documents/test.xml', 'w')
textfile.write(page)
textfile.close()

#Parsing the xml-file, the entry tag contains the results
tree = etree.parse('/home/max/Documents/test.xml')
entries = tree.findall('{http://www.w3.org/2005/Atom}entry')
for entry in range(len(entries)):
    #The uuid element allows to create the path to the file
    uuid_element = entries[entry].find('{http://www.w3.org/2005/Atom}id')
    sentinel_link = "https://scihub.esa.int/dhus/odata/v1/Products('" + uuid_element.text + "')/$value"
    
    #the title element contains the corresponding file name
    title_element = entries[entry].find('{http://www.w3.org/2005/Atom}title')
    
    #Destinationpath with filename where download to be stored
    destinationpath =  "/home/max/Documents/SentinelDownloads/" +    title_element.text + '.zip'

    #Download file and read
    print "Downloading ", title_element.text
    downloadfile = urllib2.urlopen(sentinel_link)
    data =  downloadfile.read()
    
    # Write the download into the destination zipfile
    with open(destinationpath, "wb") as code:
        code.write(data)

Print "Done downloading"

    
    