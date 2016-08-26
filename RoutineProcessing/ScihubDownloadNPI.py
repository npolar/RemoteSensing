# -*- coding: utf-8 -*- 
""" 
Created on Thu Oct 22 09:57:19 2015 
 
Downloads Sentinel Images from ESA scihub 
See http://geoinformaticstutorial.blogspot.no/2015/10/batch-downloading-sentinel-images-from.html 
for documentation 
 
@author: max 
""" 
 
import urllib2, urllib, os 
import xml.etree.ElementTree as etree 
 
# Hard coded link returning list of matching scenes 
# https://scihub.esa.int/twiki/do/view/SciHubUserGuide/5APIsAndBatchScripting#Open_Search 
 
# Authenticate at scihub webpage 
#!!DO NOT USE AT PRESENT OTHER ACCOUNT SINCE APIHUB DOES NOT TAKE NEW REGISTRATIONS!! 
url =  'https://scihub.copernicus.eu/apihub/' 
username = 'yourusername' 
password = 'yourpassword' 
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm() 
 
password_mgr.add_password(None, url, username, password) 
handler = urllib2.HTTPBasicAuthHandler(password_mgr) 
opener = urllib2.build_opener(handler) 
urllib2.install_opener(opener) 
 
# The request query -- Framstrait and Barents Sea separately since at time of writing only rectangular polygons were working 
#FramStrait 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:GRD AND ingestionDate:[2016-08-01T00:00:00.000Z TO 2016-08-25T23:59:59.999Z] AND footprint:"Intersects(POLYGON((-16.11154750824 69.190260085686,-2.7521725082398 69.190260085686,-2.7521725082398 76.370271635301,-16.11154750824 76.370271635301,-16.11154750824 69.190260085686)))"&rows=10000&start=0', ':()[]/?=,&') 
#BarentsSvalbard 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:GRD AND ingestionDate:[2016-08-01T00:00:00.000Z TO 2016-08-25T23:59:59.999Z] AND footprint:"Intersects(POLYGON((-14.35373500824 76.534976168565,56.66188999176 76.534976168565,56.66188999176 82.906616272972,-14.35373500824 82.906616272972,-14.35373500824 76.534976168565)))"&rows=10000&start=0', ':()[]/?=,&') 
 
#FRAMSTRAIT ONLY 
urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:GRD AND ingestionDate:[2016-08-25T00:00:00.000Z TO 2016-08-26T23:59:59.999Z] AND footprint:"Intersects(POLYGON((-14.612211600955582 75.1224087829817,22.47763214904441 75.1224087829817,22.47763214904441 81.67478527660691,-14.612211600955582 81.67478527660691,-14.612211600955582 75.1224087829817)))"&rows=10000&start=0', ':()[]/?=,&') 
 
#Svalbard only SLC scenes 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:"SLC"  AND ingestionDate:[2016-07-01T00:00:00.000Z TO 2016-07-25T23:59:59.999Z ]   AND  footprint:"Intersects(POLYGON((9.353024432390429 80.64929496391707,9.353024432390429 75.45656456361343,38.00536818239041 75.54458510149797,38.00536818239041 80.67781220422691,9.353024432390429 80.64929496391707)))" &rows=10000&start=0', ':()[]/?=,&') 
 
#Svalbard only Sentinel-2 scenes 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=(ingestionDate:[2016-05-01T00:00:00.000Z TO 2016-06-01T23:59:59.999Z ]) AND ( footprint:"Intersects(POLYGON((9.353024432390429 80.64929496391707,9.353024432390429 75.45656456361343,38.00536818239041 75.54458510149797,38.00536818239041 80.67781220422691,9.353024432390429 80.64929496391707)))") AND (platformname:Sentinel-2) &rows=10000&start=0', ':()[]/?=,&') 
 
#Antarctica SLC scenes 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:"GRD"  AND ingestionDate:[2016-04-10T00:00:00.000Z TO 2016-06-05T23:59:59.999Z ]  AND footprint:"Intersects(POLYGON ((-20.330297508240999 -84.533943139968002, -20.330297508240996 -69.131229094284279,-12.192357891561894 -66.326972473723544,-6.113224248938504 -65.21647912061043,53.634480872362694 -63.064386966250794,60.307181311604374 -64.007506141197638,60.529077491758997 -84.533943139968002,-20.330297508240999 -84.533943139968002)))"&rows=10000&start=0', ':()[]/?=,&') 
 
#Antarctica GRD scenes 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:"SLC"  AND ingestionDate:[2016-04-10T00:00:00.000Z TO 2016-04-17T23:59:59.999Z ]  AND footprint:"Intersects(POLYGON ((-20.330297508240999 -84.533943139968002, -20.330297508240996 -69.131229094284279,-12.192357891561894 -66.326972473723544,-6.113224248938504 -65.21647912061043,53.634480872362694 -63.064386966250794,60.307181311604374 -64.007506141197638,60.529077491758997 -84.533943139968002,-20.330297508240999 -84.533943139968002)))"&rows=10000&start=0', ':()[]/?=,&') 
 
 
#SLC Kongsvegen/Kronebreen for Jack 
#urlrequest = urllib.quote('https://scihub.copernicus.eu/apihub/search?q=productType:SLC AND ingestionDate:[2016-01-01T00:00:00.000Z TO 2016-05-12T23:59:59.999Z] AND footprint:"Intersects(POLYGON((12.38352315187863 78.81810325868608,12.981409132106672 78.81810325868608,12.981409132106672 78.93345641703195,12.38352315187863 78.93345641703195,12.38352315187863 78.81810325868608)))"&rows=10000&start=0', ':()[]/?=,&') 
 
 
# Read the response into page and write it to a xml-fil 
page = urllib2.urlopen(urlrequest).read() 
textfile = open('//home//max//Documents//scihub_results.xml', 'w') 
textfile.write(page) 
textfile.close() 
 
#Parsing the xml-file, the entry tag contains the results 
tree = etree.parse('//home//max//Documents//scihub_results.xml') 
entries = tree.findall('{http://www.w3.org/2005/Atom}entry') 
 
print "Number of Scenes Found: ", len(entries) 
for entry in range(len(entries)): 
    #The uuid element allows to create the path to the file 
    uuid_element = entries[entry].find('{http://www.w3.org/2005/Atom}id') 
    sentinel_link = "https://scihub.copernicus.eu/apihub/odata/v1/Products('" + uuid_element.text + "')/$value" 
     
    #the title element contains the corresponding file name 
    title_element = entries[entry].find('{http://www.w3.org/2005/Atom}title') 
     
    #Destinationpath with filename where download to be stored 
    #destinationpath =  "//media//max//DATADRIVE1//satellittdata//flerbrukBarents//" +  title_element.text + '.zip' 
    #destinationpath =  "//media//max//DATADRIVE1//satellittdata//DML//" +  title_element.text + '.zip' 
    destinationpath = "//mnt//satellittdata//Sentinel-1//ArcticOceanSvalbard//2016//08_August//" +  title_element.text + '.zip' 
    #destinationpath = "//mnt//satellittdata//Sentinel-1//Svalbard_SLC//2016//" +  title_element.text + '.zip' 
    #destinationpath = "//mnt//satellittdata//Sentinel-2//ArcticOcean_Svalbard//" +  title_element.text + '.zip' 
    #destinationpath = "//mnt//glaciology//processedSARimages//KronebreenSLC//" +  title_element.text + '.zip' 
     
     
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