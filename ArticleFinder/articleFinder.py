import requests
from bs4 import BeautifulSoup
import sys
import json

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'From': 'mdgough12@gmail.com'}
inputFilePath = sys.argv[1]
outputFilePath = sys.argv[2]
outputURLs = {} #dictionary of symbol->urls

class Headline:
    def __init__(self, url, title, time):
        self.title = title
        self.url = url
        self.time = time
    def addSymbol(self, symbol):
        self.symbol = symbol


def readSymbols(inputFilePath): #read the input file
    print "reading input file at: " + inputFilePath
    symbolsFile = open(inputFilePath, 'r')
    symbols = [line.strip().split(",") for line in symbolsFile.readlines()]
    symbolsFile.close()
    return symbols

def addURLs(symbol): #add the fetched urls to the dictionary of symbol -> urls
    print "finding URLs for " + symbol
    if outputURLs.has_key(symbol):
        urls = outputURLs[symbol]
    else:
        urls = []
    for url in fetchURLs(symbol):
        urls.append(url)
    outputURLs[symbol] = urls

def fetchURLs(symbol): #the hard part - given a symbol, scrape Yahoo! finance headlines page and return all the URLs for that symbol
    try:
        urls = []
        yahoo = "http://finance.yahoo.com/q?s=" + symbol.lower()
        soup = BeautifulSoup(requests.get(yahoo, headers=HEADERS).content, "lxml")
        headlines = soup.find(id="yfi_headlines").find_all("div")[1].find("ul").find_all("li")
        for headline in headlines:
            text = headline.text
            time = text[text.index("(")+1:text.index(")")]
            title = text[:text.index("(")]
            print "found article: " + title
            url = headline.a.attrs['href']
            urls.append(Headline(url, title, time))
        return urls
    except:
        print "error parsing symbol: " + symbol
        return []

def writeJSON(symbol, headlines):
    outputString = ""
    for headline in headlines:
        headline.addSymbol(symbol)
        output = json.dumps(headline.__dict__) + "\n"
        outputString += output
    return outputString



def printCsv(symbol, headlines, file): #print a SYMBOL, url... to the file argument
    print "writing urls for " + symbol + " to output file..."
    writeThis = writeJSON(symbol, headlines)
    #writeThis = writeThis.encode("ascii", "ignore")
    file.write(writeThis)

def writeToOutput(file): #call the printCsv function to write each dictionary entry to the output file
    for symbol in outputURLs:
        printCsv(symbol, outputURLs[symbol], file)

symbols = readSymbols(inputFilePath)
for symbolLine in symbols:
    for symbol in symbolLine:
        print "found symbol: " + symbol
        addURLs(symbol)
outputFile = open(outputFilePath, 'w')
writeToOutput(outputFile)
print "output written to: " + outputFilePath
outputFile.close()
