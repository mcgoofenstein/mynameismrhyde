__author__ = 'michael'

"""
INPUT: list of URLs and save locations from the ArticleFinder, in csv format where the first of every line is
the ticker symbol, and every subsequent entry in that line is a url for a news article
OUPUT: saves web pages from each URL to the provided sub-directory within Article Base
"""


import sys
import os.path
import requests
from bs4 import BeautifulSoup
import json
import re

ALL_SYMBOLS = []
ARTICLE_BASE_DIRECTORY = sys.argv[1]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'From': 'mdgough12@gmail.com'}
inputFilePath = sys.argv[2]

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
        print "error fetching url: " #+ url + " - skipping..."
    return article, soup


def save(articleSoup):
    articleObject = articleSoup[0]
    soup = articleSoup[1]
    path = str(os.path.join(ARTICLE_BASE_DIRECTORY + "/" + articleObject["symbol"] + "/").replace("//","/"))
    if not os.path.exists(path):
        os.makedirs(path)
    outputFile = open(path + articleObject["title"].replace(" ", "_").replace("/", "-") +".html", 'w')
    outputFile.write(articleObject["time"])
    outputFile.write("\n")
    outputFile.write(soup.encode('utf8'))
    print "saved page to " + path
    outputFile.close()


def parseInput(inputFileLines):
    articles = []
    for line in inputFileLines:
        article = json.loads(line)
        print "found article for " + article["symbol"] + ": " + article["title"]
        articles.append(article)
    return articles


def readInputFile(inputFilePath):
    inputFile = open(inputFilePath, 'r')
    inputLines = inputFile.readlines()
    inputFile.close()
    return inputLines


inputFileLines = readInputFile(inputFilePath)
articles = parseInput(inputFileLines)

for article in articles:
    save(fetch(article))