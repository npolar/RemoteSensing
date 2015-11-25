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
#FramStrait
#urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:GRD AND ingestionDate:[2015-11-21T00:00:00.000Z TO 2015-11-24T23:59:59.999Z ] AND footprint:"Intersects(POLYGON((-16.11154750824 69.190260085686,-2.7521725082398 69.190260085686,-2.7521725082398 76.370271635301,-16.11154750824 76.370271635301,-16.11154750824 69.190260085686)))"&rows=10000&start=0', ':()[]/?=,&')
#BarentsSvalbard
urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:GRD AND ingestionDate:[2015-11-21T00:00:00.000Z TO 2015-11-24T23:59:59.999Z ] AND footprint:"Intersects(POLYGON((-14.35373500824 76.534976168565,56.66188999176 76.534976168565,56.66188999176 82.906616272972,-14.35373500824 82.906616272972,-14.35373500824 76.534976168565)))"&rows=10000&start=0', ':()[]/?=,&')

# ALL ARCTIC IN ONE -- NOT WORKING APPARENTLY
#urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:GRD AND ingestionDate:[2015-11-14T00:00:00.000Z TO 2015-11-20T23:59:59.999Z ] AND footprint:"Intersects(POLYGON ((-71.241460739808176 80.340969951906786,92.163737048911415 79.475593855342041,50.618640667872718 71.160665525114453,10.782519656074411 74.393495752619629,0.955325106817933 67.918358919248419,-24.119047706953769 66.992588159203436,-18.721562453186497 77.310802620742379,-20.602865477320265 82.972497890203911,-71.241460739808176 80.340969951906786))"&rows=10000&start=0', ':()[]/?=,&')

#Svalbard only
#urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:"SLC"  AND ingestionDate:[2015-07-21T00:00:00.000Z TO 2015-07-25T23:59:59.999Z ]   AND  footprint:"Intersects(POLYGON((-20.330297508241 -84.533943139968,60.529077491759 -84.533943139968,60.529077491759 -60.548674886326,-20.330297508241 -60.548674886326,-20.330297508241 -84.533943139968)))" &rows=10000&start=0', ':()[]/?=,&')
#urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:"SLC"  AND ingestionDate:[2015-09-22T00:00:00.000Z TO 2015-10-22T23:59:59.999Z ]   AND  footprint:"Intersects(POLYGON((-20.330297508241 -84.533943139968,60.529077491759 -84.533943139968,60.529077491759 -60.548674886326,-20.330297508241 -60.548674886326,-20.330297508241 -84.533943139968)))" &rows=10000&start=0', ':()[]/?=,&')

#Antarctica
#urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:"GRD"  AND ingestionDate:[2015-07-16T00:00:00.000Z TO 2015-11-20T23:59:59.999Z ]  AND footprint:"Intersects(POLYGON ((-20.330297508240999 -84.533943139968002, -20.330297508240996 -69.131229094284279,-12.192357891561894 -66.326972473723544,-6.113224248938504 -65.21647912061043,53.634480872362694 -63.064386966250794,60.307181311604374 -64.007506141197638,60.529077491758997 -84.533943139968002,-20.330297508240999 -84.533943139968002)))"&rows=10000&start=0', ':()[]/?=,&')
#urlrequest = urllib.quote('https://scihub.esa.int/apihub/search?q=productType:"SLC"  AND ingestionDate:[2015-07-16T00:00:00.000Z TO 2015-11-20T23:59:59.999Z ]  AND footprint:"Intersects(POLYGON ((-20.330297508240999 -84.533943139968002, -20.330297508240996 -69.131229094284279,-12.192357891561894 -66.326972473723544,-6.113224248938504 -65.21647912061043,53.634480872362694 -63.064386966250794,60.307181311604374 -64.007506141197638,60.529077491758997 -84.533943139968002,-20.330297508240999 -84.533943139968002)))"&rows=10000&start=0', ':()[]/?=,&')


# Read the response into page and write it to a xml-fil
page = urllib2.urlopen(urlrequest).read()
textfile = open('C:\\Users\\max\\Documents\\test.xml', 'w')
textfile.write(page)
textfile.close()

#Parsing the xml-file, the entry tag contains the results
tree = etree.parse('C:\\Users\\max\\Documents\\test.xml')
entries = tree.findall('{http://www.w3.org/2005/Atom}entry')
print "Number of Scenes Found: ", len(entries)
for entry in range(len(entries)):
    #The uuid element allows to create the path to the file
    uuid_element = entries[entry].find('{http://www.w3.org/2005/Atom}id')
    sentinel_link = "https://scihub.esa.int/apihub/odata/v1/Products('" + uuid_element.text + "')/$value"
    
    #the title element contains the corresponding file name
    title_element = entries[entry].find('{http://www.w3.org/2005/Atom}title')
    
    #Destinationpath with filename where download to be stored
    destinationpath =  "G:\\satellittdata\\flerbrukBarents\\" +  title_element.text + '.zip'
    #destinationpath =  "G:\\satellittdata\\DML\\" +  title_element.text + '.zip'
    
    print
    print "Scene ", entry + 1 , "of ", len(entries)
    #Check if file already was downloaded
    print sentinel_link
    if os.path.exists(destinationpath):
        print title_element.text, ' already downloaded'
        
        continue
    
    
    #Download file and read
    print "Downloading ", title_element.text
       
    try:    
        downloadfile = urllib2.urlopen(sentinel_link)
    except:
        print title_element.text, ' not available'
        continue
    data =  downloadfile.read()
    
    # Write the download into the destination zipfile
    with open(destinationpath, "wb") as code:
        code.write(data)

print "Done downloading"
    