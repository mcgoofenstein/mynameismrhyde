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
import time

ALL_SYMBOLS = []
ARTICLE_BASE_DIRECTORY = sys.argv[1]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'From': 'mdgough12@gmail.com'}
inputFilePath = sys.argv[2]
logPath = ARTICLE_BASE_DIRECTORY + "fetcher.log"
TEXT_EXTRACTION_API = "https://api.idolondemand.com/1/api/sync/extracttext/v1?url="
API_KEY = "&extract_metadata=false&additional_metadata=&reference_prefix=&password=&apikey=0dac1111-f576-4f78-8a17-b7fbe3725959"


def newArticlesFound(): #check to see if the newslist has things to download
    try:
        with open(inputFilePath, "r") as newsListFile:
            newsListItems = [line for line in newsListFile.readlines() if len(line) > 1]
            if len(newsListItems) > 0:
                logFile.write(getTime() + ": Article Downloader found " + str(len(newsListItems)) + " new articles to retrieve")
                print getTime() + ": Article Downloader found " + str(len(newsListItems)) + " new articles to retrieve"
                return True
            else:
                return False
    except:
        print getTime() + ": news file is locked or does not exist - retrying"
        logFile.write(getTime() + ": news file is locked or does not exist - retrying")
        time.sleep(30)



def getTime():
    #TODO: daylight savings time detector...
    timeNow = datetime.datetime.now()
    day = datetime.datetime.now().weekday()
    return timeNow.strftime("%a %d %b %H:%M:%S %Y ") + "UTC-4:00 2015" #Tue Mar 17 15:59:00 UTC-04:00 2015

def extractText(url, original):

    try:
        text = json.loads(requests.get(TEXT_EXTRACTION_API + url + API_KEY, headers=HEADERS).content)["document"][0]["content"]
        text = text[text.index(article["title"]):] #optimize: eliminate up to the title to get rid of bs before article starts
        #specific optimizations
        if "noodls" in url:
            pass # TODO: optimize text extraction from noodls pages
        elif " (ANI)" in text:
            text = text[:text.rindex(" (ANI)")]
        elif "View All Comments" in text:
            text = text[:text.rindex("View All Comments")]
        text = text.replace("\\", "")
        return text
    except:
        return original #just give up and return the raw page text


def fetch(article):
    pages = []
    url = article["url"]
    try:
        print "fetching url: " + url
        logFile.write("fetching url: " + url)
        soup = BeautifulSoup(requests.get(url, headers=HEADERS).content, "lxml").text #get the raw webpage text
        if "View All" in soup and url[-9:] != "&page=all": #if need be, go back and get the full page
            article["url"] += "&page=all"
            fetch(article)
        soup = extractText(url, soup) #now try to refine and filter text using black magic
    except:
        print "error extracting text at url: " + url + " - skipping..."
        soup = ""
        logFile.write("error extracting text at url: " + url + " - skipping...\n")
    return article, soup #json, string


def saveArticle(articleSoup): #takes a single json object and saves the webpage from its url to disk
    articleObject = articleSoup[0]
    soup = articleSoup[1]
    path = str(os.path.join(ARTICLE_BASE_DIRECTORY + "/" + articleObject["symbol"] + "/").replace("//","/"))
    if not os.path.exists(path):
        os.makedirs(path)
    outputFile = open(path + articleObject["title"].replace(" ", "_").replace("/", "-") +".txt", 'w')
    timeString = "Published Time: " + articleObject["time"] + "\n" + "Fetched Time: " + getTime() + "\n"
    outputFile.write(timeString)
    outputFile.write(soup.encode('utf8'))
    print "saved page to " + path
    logFile.write("saved page to " + path + "\n")
    outputFile.close()


def parseInput(inputFileLines, log):
    articles = []
    for line in [line.strip() for line in inputFileLines if len(line)>2]:
        article = json.loads(line)
        if log:
            print "found article for " + article["symbol"] + ": " + article["title"]
            logFile.write("found article for " + article["symbol"] + ": " + article["title"] + "\n")
        articles.append(article)
    return articles


def readInputFile(inputFilePath):
    with open(inputFilePath, 'r') as inputFile:
        inputLines = [line + "}" for line in inputFile.read().split("}")]
        return inputLines

def saveNewsList(articles):
    with open(inputFilePath, "w") as newsList:
        for article in articles:
            newsList.write(json.dumps(article) + "\n")


def removeFromNewsList(article): #takes a JSON article object and removes that entry from the newsList.txt file
    articlesInFile = parseInput(readInputFile(inputFilePath), log=False)
    if article in articlesInFile or article["title"] in [article["title"] for article in articlesInFile]: #matches entire article or just title
        articlesInFile.remove(article) # remove the one we just downloaded
    saveNewsList(articlesInFile) #save the remaining



while(True):
    logFile = open(logPath, "a+")
    if newArticlesFound(): # check the newsList for any articles
        try:
            print "Running Article Downloader at " + getTime() + " on input directory " + inputFilePath + " and output path " + ARTICLE_BASE_DIRECTORY
            logFile.write("Running Article Downloader at " + getTime() + " on input directory " + inputFilePath + " and output path " + ARTICLE_BASE_DIRECTORY + "\n")
            inputFileLines = readInputFile(inputFilePath) #inputFileLines is JSON from file
            articles = parseInput(inputFileLines, log=True) #articles is list of JSON objects

            for article in articles:
                saveArticle(fetch(article)) #fetch and save each article
                removeFromNewsList(article) #remove that article from the list of articles to download so we can check for new ones next time

            print "- " + getTime() + " - Article Downloader finished downloading " + str(len(articles)) + " news pages."
            logFile.write("- " + getTime() + " - Article Downloader finished downloading " + str(len(articles)) + " news pages.\n")

        except IOError:
            print "Article Fetcher at " + getTime() + ": IOError! There's nothing here..."
            logFile.write("Article Fetcher at " + getTime() + ": IOError! There's nothing here...")
    else:
        print getTime() + ": no new articles found to download"
        #logFile.write(getTime() + ": no new articles found to download")
    logFile.close()
    time.sleep(60)

