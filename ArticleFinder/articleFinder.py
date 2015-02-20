import requests
from lxml import etree
from bs4 import BeautifulSoup
import sys
import json
import datetime
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'From': 'mdgough@indiana.edu'}
inputFilePath = sys.argv[1]
outputFilePath = sys.argv[2]
rssFileName = "/".join(inputFilePath.split("/")[0:-1]) + "/rssCache_"
priceFileName = "/".join(inputFilePath.split("/")[0:-1]) + "/prices_"


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


def convertToEST(time):
    #Fri, 20 Feb 2015 19:26:45 GMT -> Fri Feb 20 14:26:45 UTC-05:00 2015
    hour = str(int(time.split(":")[0].split(" ")[-1]) - 5).zfill(2)
    min = time.split(":")[1]
    sec = time.split(":")[2].split(" ")[0]
    hms = ":".join([hour,min,sec])
    year = time.split(" ")[3]
    dm = " ".join(time.split(" ")[:2]).replace(",", "")
    return dm + " " + hms + " UTC-05:00 " + year


def waitSeconds(timeNow, openClose):
    if openClose[0] == "o":
        print "waiting 60 seconds before checking servers..."
        return 60
    else:
        timeToWait = 9 + (24 - timeNow.hour) * 3600
        print "I'll check again in " + str(timeToWait) + " seconds..."
        return timeToWait

def marketOpen(): #returns true if the market is open and it has been more than a minute since the last time the script ran
    timeNow = datetime.datetime.now()
    day = datetime.datetime.now().weekday()
    if day < 5 and (timeNow.hour < 17 or (timeNow.hour == 16 and timeNow.minute < 31)):
        openClose = "open!"
        rv = True
    else:
        openClose = "closed!"
        rv = False
    print "It's " + timeNow.strftime("%A, %B %d, %Y, at %H:%M:%S - The markets are ") + openClose
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

def save(rss, file): #saves the given rss into the given rssCache file
    file.close()
    file = open(file.name, "w")
    for line in rss:
        file.write(line)
    file.close()

def getPrice(symbol):
    print "fetching price for " + symbol + "..."
    try:
        api = "http://dev.markitondemand.com/Api/v2/Quote/json?symbol=" + symbol
        apiReturn = json.loads(requests.get(api, headers=HEADERS).content)
        price = apiReturn["LastPrice"]
        changePct = apiReturn["ChangePercent"]
        time = apiReturn["Timestamp"]
        volume = apiReturn["Volume"]
        changeYTD = apiReturn["ChangePercentYTD"]
        high,low,openPrice = apiReturn["High"], apiReturn["Low"], apiReturn["Open"]
        priceFile = open(priceFileName+symbol, "a")
        priceFile.write(json.dumps({"LastPrice":price,"ChangePercent":changePct,"Timestamp":time,"Volume":volume,"ChangePercentYTD":changeYTD,"High":high,"Low":low,"Open":openPrice})+"\n")
        priceFile.close()
        print "price saved: " + str(price)
        return str(price)
    except:
        print "error saving price... re-trying"
        time.sleep(3)
        return getPrice(symbol)

def readSymbols(inputFilePath): #read the input file
    print "reading input file at: " + inputFilePath
    symbolsFile = open(inputFilePath, 'r')
    symbols = [line.strip().split(",") for line in symbolsFile.readlines()]
    symbolsFile.close()
    return symbols

def addURLs(symbol): #add the fetched urls to the dictionary of symbol -> urls
    if len(symbol) < 1:
        print "skipping invalid symbol: " + symbol
        return
    print "finding URLs for " + symbol
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
            save(rss, rssCache)
            for headline in [item.contents for item in newFeed["new"]]: #for every new url in the newsFeed
                description = headline[3].text
                time = convertToEST(headline[5].text)
                title = headline[0].text
                print "found article: " + title + " - " + time + " - "+ description
                url = headline[2]
                urls.append(Headline(url, title, time, price))
            if urls:
                return urls
        else:
            print "no new articles found since last search"
            return []
    except:
        print "ERROR :-( no urls found for: " + symbol
        return []


def writeJSON(symbol, headlines):
    outputString = ""
    for headline in headlines:
        headline.addSymbol(symbol)
        output = json.dumps(headline.__dict__) + "\n"
        outputString += output
    return outputString


def printCsv(symbol, headlines, file): #print a SYMBOL, url... to the file argument
    writeThis = writeJSON(symbol, headlines)
    #writeThis = writeThis.encode("ascii", "ignore")
    if writeThis:
        print "writing urls for " + symbol + " to output file..."
        file.write(writeThis)
    else:
        print symbol + " - nothing to write!"

def writeToOutput(file): #call the printCsv function to write each dictionary entry to the output file
    for symbol in outputURLs:
        printCsv(symbol, outputURLs[symbol], file)
    print "output written to: " + outputFilePath



while(marketOpen()):
    outputURLs = {} #dictionary of symbol->url
    symbols = readSymbols(inputFilePath)
    for symbolLine in symbols:
        for symbol in symbolLine:
            print "parsed symbol: " + symbol
            addURLs(symbol) #populates the outputURLs dictionary and the priceQueue
    outputFile = open(outputFilePath, 'a')
    writeToOutput(outputFile) #writes the outputURLs dictionary to the output file
    outputFile.close()

