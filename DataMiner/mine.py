__author__ = 'michael'

import sys
import os
import json
import datetime
from datetime import timedelta
import requests
from dateutil.parser import parse

"""
INPUT: prices_* files, /articles/SYM/* article text files, symbols.csv
DEPENDENCIES: call to sentiment extractor
OUTPUT: csv file for data analysis
"""

class Article:
    def __init__(self, symbol, filepath, title):
        self.title = title
        self.symbol = symbol
        with open("/".join(filepath.split("/")[:-3] + ["ArticleFinder"] + ["prices_" + self.symbol.upper()]), "r") as pricesFile:
            self.priceLines = pricesFile.readlines()
        with open(filepath, "r") as inputFile:
            self.contents = inputFile.readlines()
            self.text = self.getText(self.contents)
            self.pubTime = getTime(self.contents[0])
        self.price = self.getPrice(self.priceLines, self.pubTime)
        self.laterPrice = self.getPrice(self.priceLines, self.pubTime + timedelta(minutes=20))
        self.sentiment = self.getSentiment(self.text, filepath)

    def getPrice(self, priceLines, time):
        price = [(json.loads(line))["LastPrice"] for line in priceLines if sameTime(json.loads(line)["Timestamp"], time)]
        if not price:
            return "NA"
        if len(price) == 1:
            return price[0]
        if len(price) > 1:
            return str(sum(price)/float(len(price)))

    def getSentiment(self, text, filepath): #returns sentiment, and also writes sentiment info to original file
        try:
            text = text.replace("#", "").replace("%","")
            data = {"text":text ,"apikey":"0dac1111-f576-4f78-8a17-b7fbe3725959"}
            url = "https://api.idolondemand.com/1/api/sync/analyzesentiment/v1"
            if len(text) > 10 and not "var" in text.lstrip("\n")[:6] and not "=" in text.lstrip("\n")[:10] and not "()" in text.lstrip("\n")[:10]:
                request = requests.post(url, data=data).content
                json_ = json.loads(request)
            with open(filepath, 'a') as articleFile:
                articleFile.write("\nsentiment:\n")
                json.dump(request, articleFile)
            return json_["aggregate"]
        except:
            return {"sentiment":"error", "score":0}


    def getText(self, contents):
        if "\nsentiment:\n" in contents[2]:
            contents[2] = contents[2][:contents[2].index("\nsentiment:")]
        if "Close the Sharing and Personal Tools window Close" in contents[2] and "Smartlinks" in contents[2]: #markers for Noodls article format
            return contents[2][contents[2].index("Close the Sharing and Personal Tools window Close")+48:contents[2].index("Smartlinks")]
        else:
            texts = contents[-1].split("\xe2\x80\xa2")
            return max(texts, key=len)

    def writeCSV(self):
        return "\t".join([self.symbol, self.title, str(self.pubTime), str(self.sentiment["score"]), self.sentiment["sentiment"], str(self.price), str(self.laterPrice)])


def getTime(timeString):
        try:
            timeString = timeString.lstrip("Published Time: ").strip().replace("UTC-04:00 ", "").replace("-","")
            return parse(timeString)
        except:
            return datetime.datetime.min

def sameTime(timeStamp, time): #compares two timestamps for approximate equality
    timeStamp = getTime(timeStamp)
    if (timeStamp - time).seconds < 120:
        return True
    else:
        return False




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





