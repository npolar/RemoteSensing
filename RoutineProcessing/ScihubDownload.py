# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 09:57:19 2015

@author: max
"""

import urllib2, urllib
import xml.etree.ElementTree as etree

# Hard coded link returning list of matching scenes
# https://scihub.esa.int/twiki/do/view/SciHubUserGuide/5APIsAndBatchScripting#Open_Search
url = urllib.quote('https://scihub.esa.int/dhus/search?q=productType:GRD AND ingestionDate:[2015-09-30T00:00:00.000Z TO 2015-09-30T23:59:59.999Z] AND footprint:"Intersects(POLYGON((-16.11154750824 69.190260085686,-2.7521725082398 69.190260085686,-2.7521725082398 76.370271635301,-16.11154750824 76.370271635301,-16.11154750824 69.190260085686)))"&rows=10000&start=0', ':()[]/?=,&')
url2 =  'https://scihub.esa.int/dhus/'

# Download matching images, described here http://stackoverflow.com/a/11162326/2341961
username = 'username'
password = 'password'
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

password_mgr.add_password(None, url2, username, password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)

page = urllib2.urlopen(url).read()

# Write returned xml list to textfile
textfile = open('/home/max/Documents/test.xml', 'w')
textfile.write(page)
textfile.close()


tree = etree.parse('/home/max/Documents/test.xml')
entries = tree.findall('{http://www.w3.org/2005/Atom}entry')
for entry in range(len(entries)):
    uuid_element = entries[entry].find('{http://www.w3.org/2005/Atom}id')
    sentinel_link = "https://scihub.esa.int/dhus/odata/v1/Products('" + uuid_element.text + "')/$value"
    title_element = entries[entry].find('{http://www.w3.org/2005/Atom}title')
    destinationpath =  "/home/max/Documents/SentinelDownloads/" +    title_element.text + '.zip'
    print uuid_element
    print sentinel_link
    print "Downloading ", title_element.text
    downloadfile = urllib2.urlopen(sentinel_link)
    data =  downloadfile.read()
    with open(destinationpath, "wb") as code:
        code.write(data)
    #destinationfile.open(destinationpath, wb)
    #destinationfile.write(data)
    
    #sentinelimage.retrieve(Sentinel_link, "/home/max/Documents/SentinelDownloads/")
    

    
    