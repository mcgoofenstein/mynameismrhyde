__author__ = 'michael'

"""
INPUT: file containing URLs and save locations from the ArticleFinder, in json format, eg:

{"url": "http://us.rd.yahoo.com/finance/news/rss/story/*http://sg.finance.yahoo.com/
news/russian-researchers-expose-breakthrough-u-025503337.html",
"price": "156.89", "time": "Tue 17 04:32:49 UTC-05:00 2015", "symbol": "IBM",
"title": "Russian researchers expose breakthrough in U.S. spying program"}

OUPUT: saves web pages from each URL to the provided sub-directory within Article Base (sys.argv[1])
"""


import sys
import os.path
import requests
from bs4 import BeautifulSoup
import json
import datetime

ALL_SYMBOLS = []
ARTICLE_BASE_DIRECTORY = sys.argv[1]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'From': 'mdgough12@gmail.com'}
inputFilePath = sys.argv[2]
logPath = ARTICLE_BASE_DIRECTORY + "/fetcher.log"
logFile = open(logPath, "a")

def newArticlesFound():
    return True

def getTime():
    #TODO: daylight savings time detector...
    timeNow = datetime.datetime.now()
    day = datetime.datetime.now().weekday()
    return timeNow.strftime("%a %d %b %H:%M:%S %Y ") + "UTC-4:00 2015" #Tue Mar 17 15:59:00 UTC-04:00 2015

def fetch(article):
    pages = []
    url = article["url"]
    try:
        print "fetching url: " + url
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).content, "lxml")
        if "View All" in soup.text and url[-9:] != "&page=all":
            article["url"] += "&page=all"
            fetch(article)
    except:
        print "error fetching url: " + url + " - skipping..."
        logFile.write("error fetching url: " + url + " - skipping...\n")
    return article, soup


def save(articleSoup): #takes a single json object and saves the webpage from its url to disk
    articleObject = articleSoup[0]
    soup = articleSoup[1]
    path = str(os.path.join(ARTICLE_BASE_DIRECTORY + "/" + articleObject["symbol"] + "/").replace("//","/"))
    if not os.path.exists(path):
        os.makedirs(path)
    outputFile = open(path + articleObject["title"].replace(" ", "_").replace("/", "-") +".html", 'w')
    timeString = "Published Time: " + articleObject["time"] + "\n" + "Fetched Time: " + getTime() + "\n"
    outputFile.write(timeString)
    outputFile.write(soup.encode('utf8'))
    print "saved page to " + path
    logFile.write("saved page to " + path + "\n")
    outputFile.close()


def parseInput(inputFileLines):
    articles = []
    for line in inputFileLines:
        article = json.loads(line)
        print "found article for " + article["symbol"] + ": " + article["title"]
        logFile.write("found article for " + article["symbol"] + ": " + article["title"] + "\n")
        articles.append(article)
    return articles


def readInputFile(inputFilePath):
    inputFile = open(inputFilePath, 'r')
    inputLines = inputFile.readlines()
    inputFile.close()
    return inputLines

while(True):
    if newArticlesFound():
        try:
            print "Running Article Downloader at " + getTime() + " on input directory " + inputFilePath + " and output path " + ARTICLE_BASE_DIRECTORY
            logFile.write("Running Article Downloader at " + getTime() + " on input directory " + inputFilePath + " and output path " + ARTICLE_BASE_DIRECTORY + "\n")
            inputFileLines = readInputFile(inputFilePath) #inputFileLines is JSON from file
            articles = parseInput(inputFileLines) #articles is list of JSON objects

            for article in articles:
                save(fetch(article))

            print "- " + getTime() + " - Article Downloader finished downloading " + str(len(articles)) + " news pages."
            logFile.write("- " + getTime() + " - Article Downloader finished downloading " + str(len(articles)) + " news pages.\n")

        except IOError:
            print "Article Fetcher at " + getTime() + ": IOError! There's nothing here..."
            logFile.write("Article Fetcher at " + getTime() + ": IOError! There's nothing here...")
    else:
        print "no new articles found to download"
        logFile.write(getTime() + ": no new articles found to download")
