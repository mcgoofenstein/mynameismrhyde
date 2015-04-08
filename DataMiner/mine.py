__author__ = 'michael'

import sys
import os
import json
import datetime
from datetime import timedelta
import requests
from dateutil.parser import parse
import bisect

"""
INPUT: prices_* files, /articles/SYM/* article text files, symbols.csv
DEPENDENCIES: call to sentiment extractor
OUTPUT: csv file for data analysis
"""

class Article:
    def __init__(self, symbol, filepath, title, priceDictionary, sortedDates):
        self.title = title
        self.symbol = symbol
        with open("/".join(filepath.split("/")[:-3] + ["ArticleFinder"] + ["prices_" + self.symbol.upper()]), "r") as pricesFile:
            self.priceLines = pricesFile.readlines()
        with open(filepath, "r") as inputFile:
            self.contents = inputFile.readlines()
            self.text = self.getText(self.contents)
            self.pubTime = getTime(self.contents[0])
        self.price = self.getPrice(self.pubTime, priceDictionary, sortedDates)
        self.laterPrice = self.getPrice(self.pubTime + timedelta(minutes=20), priceDictionary, sortedDates, when="after")
        self.sentiment = self.getSentiment(self.text, filepath, self.contents)

    def getPrice(self, pubTime, priceDictionary, sortedDates, when="before"):
        if not marketOpen(pubTime):
            pubTime = adjustToMarketOpen(pubTime, sortedDates, when)
        matchingTimes = [date for date in sortedDates if abs((pubTime - date).days) == 0 and abs((pubTime - date).seconds) < 90]
        prices = [priceDictionary[time]["LastPrice"] for time in matchingTimes]
        if not prices:
            return "NA"
        if len(prices) == 1:
            return prices[0]
        if len(prices) > 1:
            return str(sum(prices)/float(len(prices)))

    def getSentiment(self, text, filepath, contents): #returns sentiment, and also writes sentiment info to original file
        try:
            text = text.replace("#", "").replace("%","")
            data = {"text":text ,"apikey":"0dac1111-f576-4f78-8a17-b7fbe3725959"}
            url = "https://api.idolondemand.com/1/api/sync/analyzesentiment/v1"
            if "\nsentiment:\n" in contents[2]:
                return json.loads(contents[2][contents[2].index("\nsentiment:\n"):])
            elif len(text) > 10 and not "var" in text.lstrip("\n")[:6] and not "=" in text.lstrip("\n")[:10] and not "()" in text.lstrip("\n")[:10]:
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


def adjustToMarketOpen(time, list, when): #changes a time to the the closest past time in the list when the market was open
    if time >= max(list): #if the time is beyond the list of times to check, return latest open time
        return max([moment for moment in list if marketOpen(moment)])
    if time <= min(list):
        return min([moment for moment in list if marketOpen(moment)])
    # time must fit into the list somewhere in this case:
    if when == "before":
        return list[bisect.bisect_left([moment for moment in list if marketOpen(moment)], time) - 1]
    if when == "after":
        return list[bisect.bisect_left([moment for moment in list if marketOpen(moment)], time)]


def marketOpen(time):
    if time.hour in [10, 11, 12, 13, 14, 15] and time.weekday in [0,1,2,3,4]: #majority case first for performance
        return True
    if time.weekday() not in range(0,5):
        return False
    if time.hour == 9 and time.minute < 30:
        return False
    if time.hour in range(0, 9) + range(16, 25):
        return False
    return True


def getTime(timeString):
        try:
            timeString = timeString.replace("-", "", 1).lstrip("Published Time: ")
            #timeString = timeString.lstrip("Published Time: ").strip().replace("UTC-04:00 ", "").replace("-","")
            timeString = parse(timeString)
            return timeString
        except:
            return datetime.datetime.min


def getPrices(prices_dir): #returns {symbol: ( { date : price_json_obj }, [ sorted dates ] ) }
    pricesDict = {}
    for fileName in [file for file in os.listdir(prices_dir) if "prices" in file and not "~" in file]:
        symbol = fileName[fileName.index("_")+1:]
        file_ = open(prices_dir + fileName, "r")
        priceLines = [json.loads(line) for line in [line.strip() for line in file_.readlines()]] #json representations for each line
        file_.close()
        timePriceHash = {parse(entry["Timestamp"]) : entry for entry in priceLines} # dictionary of datetime -> json obj of price
        chronology = sorted(timePriceHash.keys()) # chronologically-sorted dates of all prices in the above dictionary
        pricesDict[symbol] = (timePriceHash, chronology)
    return pricesDict



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
pricesDict = getPrices(PRICES_DIR)

if __name__ == "__main__":
    with open(OUTPUT_PATH, "w") as outputFile:
        for symbol in articlesDict.keys():
            for path in articlesDict[symbol][0]:
                i = articlesDict[symbol][0].index(path)
                outputFile.write(Article(symbol, path, articlesDict[symbol][1][i], pricesDict[symbol][0], pricesDict[symbol][1]).writeCSV() + "\n")





