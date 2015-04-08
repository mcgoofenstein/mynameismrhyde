import requests
#from lxml import etree
from bs4 import BeautifulSoup
import sys
import json
import datetime
from datetime import timedelta
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'From': 'mdgough@indiana.edu'}
inputFilePath = "/".join(sys.argv[0].split("/")[:-1]) + "/symbols.csv"  #symbols
outputFilePath = "/".join(sys.argv[0].split("/")[:-1]) + "/newsList.txt" #news list
rssFileName = "/".join(inputFilePath.split("/")[:-1]) + "/rssCache_"
priceFileName = "/".join(inputFilePath.split("/")[:-1]) + "/prices_"

if "debug" in sys.argv:
    DEBUG = True
else:
    DEBUG = False


class Headline:
    def __init__(self, url, title, time, price):
        self.title = title
        self.url = url
        self.time = time
        self.price = price
    def addSymbol(self, symbol):
        self.symbol = symbol

def onlyNewURLs(fetched, existing):
    return list(set(fetched) - set(existing))

def getTime():
    #TODO: daylight savings time detector...
    timeNow = datetime.datetime.now()
    day = datetime.datetime.now().weekday()
    return timeNow.strftime("%a %d %b %H:%M:%S %Y ") + "UTC-4:00 2015" #Tue Mar 17 15:59:00 UTC-04:00 2015

def convertToEST(time):
    #Fri, 20 Feb 2015 19:26:45 GMT -> Fri Feb 20 14:26:45 UTC-04:00 2015
    hour = str(int(time.split(":")[0].split(" ")[-1]) - 5).zfill(2)
    month = time.split(" ")[2]
    day = time.split(" ")[1]
    weekday = time.split(" ")[0][:-1]
    min = time.split(":")[1]
    sec = time.split(":")[2].split(" ")[0]
    hms = ":".join([hour,min,sec])
    year = time.split(" ")[3]
    dm = " ".join(time.split(" ")[:2]).replace(",", "")
    return weekday + " " + day + " " + month + " " + hms + " UTC-04:00 " + year

def waitSeconds(timeNow, openClose):
    if openClose[0] == "o":
        print "waiting 60 seconds before checking servers again..."
        logFile.write("waiting 60 seconds before checking servers again...\n")
        return 60
    else:
        nextOpen = datetime.datetime.combine(timeNow.today() + datetime.timedelta(days=1), datetime.time(9,30,0))
        timeToWait = timeNow - nextOpen
        print "I'll check again in like " + str(timeToWait.seconds/3600) + " hours..."
        logFile.write("I'll check again in like " + str(timeToWait.seconds/3600) + " hours...\n")
        return timeToWait.seconds

def marketOpen(FIRST_TIME): #returns true if the market is open and it has been more than a minute since the last time the script ran
    """this is the regulator/driver function"""
    if DEBUG:
        return True
    timeNow = datetime.datetime.now()
    day = datetime.datetime.now().weekday()
    if day < 5 and (timeNow.hour < 15 and (timeNow.hour >= 6 and timeNow.minute <= 30)):
        openClose = "open!"
        rv = True
    else:
        openClose = "closed!"
        rv = False
    print "It's " + timeNow.strftime("%A, %B %d, %Y, at %H:%M:%S - The markets are ") + openClose
    logFile.write("It's " + timeNow.strftime("%A, %B %d, %Y, at %H:%M:%S - The markets are ") + openClose + "\n")
    if not FIRST_TIME:
        time.sleep(waitSeconds(timeNow, openClose))
    return rv



def markNewRss(rss, file): #returns a dictionary object which has keys to lists of all old and new rss items
    r = {}
    newItemsList = []
    oldRss = file.readlines()
    if oldRss:
        oldRss = oldRss[1]
        oldItems = BeautifulSoup(oldRss, "lxml").findAll("item")
    else:
        oldItems = []
    newItems = BeautifulSoup(rss, "lxml").findAll("item")
    for newItem in newItems:
        itemIsNew = True
        newDate = newItem.find("pubdate").text
        newLink = newItem.contents[2]
        for oldItem in oldItems:
            if oldItem.find("pubdate").text == newDate or oldItem.contents[2] == newLink:
                itemIsNew = False
        if itemIsNew:
            newItemsList.append(newItem)
    r["old"] = rss
    r["new"] = newItemsList
    if newItemsList:
        r["isNew"] = True
    else:
        r["isNew"] = False
    return r

def saveRSS(rss, file): #saves the given rss into the given rssCache file
    file.close()
    file = open(file.name, "w")
    for line in rss:
        file.write(line)
    file.close()

def getPrice(symbol):
    print "fetching price for " + symbol + "..."
    logFile.write("fetching price for " + symbol + "...\n")
    try:
        api = "http://dev.markitondemand.com/Api/v2/Quote/json?symbol=" + symbol
        apiReturn = json.loads(requests.get(api, headers=HEADERS).content)
        price = apiReturn["LastPrice"]
        changePct = apiReturn["ChangePercent"]
        time = apiReturn["Timestamp"]
        volume = apiReturn["Volume"]
        changeYTD = apiReturn["ChangePercentYTD"]
        high,low,openPrice = apiReturn["High"], apiReturn["Low"], apiReturn["Open"]
        logFile.write(getTime() + " attempting to write price for " + symbol + " to price file at base directory " + priceFileName + "\n")
        priceFile = open(priceFileName+symbol, "a+")
        priceFile.write(json.dumps({"LastPrice":price,"ChangePercent":changePct,"Timestamp":time,"Volume":volume,"ChangePercentYTD":changeYTD,"High":high,"Low":low,"Open":openPrice})+"\n")
        priceFile.close()
        print "price saved: " + str(price)
        logFile.write(getTime() + " - price saved: " + str(price) + "\n")
        return str(price)
    except:
        print "error saving price... re-trying"
        logFile.write(getTime() + " - error saving price... re-trying\n")
        time.sleep(3)
        return getPrice(symbol)

def readSymbols(inputFilePath): #read the input file
    print "reading input file at: " + inputFilePath
    logFile.write("reading input file at: " + inputFilePath + "\n")
    symbolsFile = open(inputFilePath, 'r')
    symbols = [line.strip().split(",") for line in symbolsFile.readlines()]
    symbolsFile.close()
    return symbols

def addURLs(symbol): #add the fetched urls to the dictionary of symbol -> urls
    if len(symbol) < 1:
        print "skipping invalid symbol: " + symbol
        logFile.write("skipping invalid symbol: " + symbol + "\n")
        return
    print "finding URLs for " + symbol
    logFile.write("finding URLs for " + symbol + "\n")
    if not outputURLs.has_key(symbol): #initialize symbol -> url entry if it doesn't exist
        urls = []
        outputURLs[symbol] = urls
    fetchedURLs = fetchURLs(symbol) #returns a list of the newest Headlines
    if fetchedURLs:
        #fetchedURLs += onlyNewURLs(fetchedURLs, outputURLs[symbol]) why would there be redundancies? i think this adds duplicates
        outputURLs[symbol] = fetchedURLs

def fetchURLs(symbol): #given a symbol, scrape yahoo rss news feed. return list of new Headlines found WRT RSS cache file
    open(rssFileName+symbol+".xml", "a").close()
    price = getPrice(symbol)
    try:
        rssCache = open(rssFileName+symbol+".xml", 'r')
        urls = []
        feed = "http://feeds.finance.yahoo.com/rss/2.0/headline?s=" + symbol.lower() + "&region=US&lang=en-US"
        rss = requests.get(feed, headers=HEADERS).content
        newFeed = markNewRss(rss, rssCache) #check to see if this rss feed has anything new
        if newFeed["isNew"]: #if the rss has new things, save it to disk and then add the new things to the url download list
            saveRSS(rss, rssCache)
            for headline in [item.contents for item in newFeed["new"]]: #for every new url in the newsFeed
                description = headline[3].text.encode("ascii", "ignore")
                time = convertToEST(headline[5].text).encode("ascii", "ignore")
                title = headline[0].text.encode("ascii", "ignore")
                print "found article: " + title + " - " + time + " - "+ description
                logFile.write("found article: " + title + " - " + time + " - "+ description + "\n")
                url = headline[2]
                urls.append(Headline(url, title, time, price))
            if urls:
                return urls
        else:
            print "no new articles found since last search"
            logFile.write("no new articles found since last search\n")
            return []
    except:
        print "ERROR :-( no urls found for: " + symbol
        logFile.write("ERROR :-( no urls found for: " + symbol + "\n")
        return []


def writeJSON(symbol, headlines):
    outputString = ""
    for headline in headlines:
        headline.addSymbol(symbol)
        output = json.dumps(headline.__dict__) + "\n"
        outputString += output
    return outputString


def printJSON(symbol, headlines, file): #print a SYMBOL, url... to the file argument
    writeThis = writeJSON(symbol, headlines)
    #writeThis = writeThis.encode("ascii", "ignore")
    if writeThis:
        print "writing urls for " + symbol + " to output file..."
        logFile.write("writing urls for " + symbol + " to output file...\n")
        file.write(writeThis)
    else:
        print symbol + " - nothing to write!"

def writeToOutput(file): #call the printCsv function to write each dictionary entry to the output file
    for symbol in outputURLs:
        printJSON(symbol, outputURLs[symbol], file)
    print "output written to: " + outputFilePath
    logFile.write("output written to: " + outputFilePath + "\n")

def openOutputFile(outputFilePath):
    try:
        print getTime() + " attempting to open news list output file: " + outputFilePath
        logFile.write(getTime() + " attempting to open news list output file: " + outputFilePath)
        return open(outputFilePath, 'a')
    except:
        print getTime() + " failed to open news list output file; retrying..."
        logFile.write(getTime() + " failed to open news list output file; retrying...")
        time.sleep(30)
        openOutputFile(outputFilePath)


FIRST_TIME = True #signifies the program is being started up, bypasses initial 60-sec wait
while(True):
    logFile = open("/".join(sys.argv[0].split("/")[:-1]) + "/finder.log", "a")
    if marketOpen(FIRST_TIME):
        print "Running Article Finder at " + getTime() + " on input directory " + inputFilePath + " and output saved to " + outputFilePath
        logFile.write("Running Article Finder at " + getTime() + " on input directory " + inputFilePath + " and output saved to " + outputFilePath + "\n")
        outputURLs = {} #dictionary of symbol->url
        symbols = readSymbols(inputFilePath)
        for symbolLine in symbols:
            for symbol in symbolLine:
                print "parsed symbol: " + symbol
                logFile.write("parsed symbol: " + symbol + "\n")
                addURLs(symbol) #populates the outputURLs dictionary and the priceQueue
        outputFile = openOutputFile(outputFilePath)
        writeToOutput(outputFile) #writes the outputURLs json object to the output file
        outputFile.close()
    FIRST_TIME = False
    logFile.write("Article Finder sill running at: " + getTime() + "\n")
    logFile.close()
    time.sleep(60)

