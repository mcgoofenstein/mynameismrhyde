__author__ = 'michael'

import sys
import os
import json
import datetime
from datetime import timedelta
import requests

"""
INPUT: prices_* files, /articles/SYM/* article text files, symbols.csv
DEPENDENCIES: call to sentiment extractor
OUTPUT: csv file for data analysis
"""

class Article:
    API1 = "https://api.idolondemand.com/1/api/sync/analyzesentiment/v1?text=%22"
    API2 = "%22&apikey=0dac1111-f576-4f78-8a17-b7fbe3725959"

    def __init__(self, symbol, filepath, title):
        self.title = title
        self.symbol = symbol
        self.pricesFile = "/".join(filepath.split("/")[:-3] + ["ArticleFinder"]  + ["prices_" + self.symbol.upper()])
        with open(filepath, "r") as inputFile:
            self.contents = inputFile.readlines()
            self.text = self.getText(self.contents)
            self.pubTime = ":".join(self.contents[0].lstrip("Published Time: ").split(":")[:2])
        self.price = self.getPrice(self.pricesFile, self.pubTime)
        self.laterPrice = self.getPrice(self.pricesFile, datetime.datetime.strptime(self.pubTime, "%a %b %d %H:%M:%S UTC-04:00 %Y") + timedelta(minutes=20))
        self.sentiment = self.getSentiment(self.text)

    def getPrice(self, pricePath, time):
        with open(pricePath, "r") as priceFile:
            priceLines = priceFile.readlines()
            price = [(json.loads(line))["LastPrice"] for line in priceFile if time in json.loads(line)["Timestamp"]]
            if not price:
                return " "
            if len(price) == 1:
                return price[0]
            if len(price > 1):
                return str(sum(price)/float(len(price)))

    def getSentiment(self, text):
        return json.loads(requests.get(Article.API1 + text + Article.API2).content)["aggregate"]


    def getText(self, contents):
        if "Close the Sharing and Personal Tools window Close" in contents[2] and "Smartlinks" in contents[2]: #markers for Noodls article format
            return contents[2][contents[2].index("Close the Sharing and Personal Tools window Close")+48:contents[2].index("Smartlinks")]
        else:
            texts = contents[-1].split("\xe2\x80\xa2")
            return max(texts, key=len)

    def writeCSV(self):
        return "\t".join([self.symbol, self.pubTime, self.sentiment, self.price, self.laterPrice])


def getArticles(articlesDir): #retuns {symbol:([articlePaths], [articleTitles])}
    articles = {}
    for symbolPath in [symbolPath for symbolPath in os.walk(articlesDir) if not symbolPath[1]]: #comprehension which yields all base-level directories in the given path
        symbol = symbolPath[0].split("/")[-1].upper()
        articlePaths = [os.path.join(symbolPath[0], articleFile) for articleFile in symbolPath[2]]
        articleTitles = [title.rstrip(".txt") for title in symbolPath[2]]
        articles[symbol] = (articlePaths, articleTitles)
    return articles

BASE_DIR = os.path.split(os.path.split(sys.argv[0])[0])[0] + "/"
PRICES_DIR = BASE_DIR + "ArticleFinder/"
ARTICLES_DIR = BASE_DIR + "articles/"
OUTPUT_PATH = BASE_DIR + "data.csv"

articlesDict = getArticles(ARTICLES_DIR)

with open(OUTPUT_PATH, "w") as outputFile:
    for symbol in articlesDict.keys():
        for path in articlesDict[symbol][0]:
            i = articlesDict[symbol][0].index(path)
            outputFile.write(Article(symbol, path, articlesDict[symbol][1][i]).writeCSV() + "\n")





