import requests
from bs4 import BeautifulSoup
import re
import time
import orjson
import ast
import datetime
import pandas as pd
#import csv
from linebot import (LineBotApi, WebhookHandler, exceptions)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
import schedule
import logging
from fake_headers import Headers
import json
import os
from flask import Flask, request, abort

app = Flask(__name__)

count = 0
data = []

datetime = datetime.datetime.now()
datetimeStr = datetime.strftime("%H%M")
datatimeStr2 = datetime.strftime("%H:%M")
print(datetimeStr)
closePrice = []
highPrice = []
lowPrice = []
closePriceTmp = []
highPriceTmp = []
lowPriceTmp = []
pastK = 20.32
pastD = 34.55
num = 0
filename = datetimeStr + '.csv'

# 必須放上自己的Channel Access Token
line_bot_api = LineBotApi('6QUFBIE7QynL2wqsA+yOGDEP/PVzU6/I1M1gp62Q19rQuEDrVVgOmWwWZnBwxRDDb8YKLDTr72+03oqvNXYe+BWEPl0tCAj7MMlADJt+693H6/NVN+MPkb2IscY0dhm70S4+tf6M0slXVyDAFMyAkwdB04t89/1O/w1cDnyilFU=')
# 必須放上自己的Channel Secret
handler = WebhookHandler('a60ee4b634af158191dbbef6e0a85eb0')
#your id
yourid='U5012644ffad238c08dc547a96050214d'

def rsvCal(dateTime, closePrice=[], highPrice=[], lowPrice=[], closePriceTmp=[], highPriceTmp=[], lowPriceTmp=[]):
    global pastK, pastD
    global num
    num = num + 1
    length = 9
    minStockPrice = 9999999.00
    maxStockPrice = 0.00
    stockPriceCurrent = float(closePrice[0])

    for i in range(10):
        if (minStockPrice > (float)(lowPrice[length - 1 - i])):
            minStockPrice = (float)(lowPrice[length - 1 - i])
            # print("min = " + str(minStockPrice))
        if (maxStockPrice < (float)(highPrice[length - 1 - i])):
            maxStockPrice = (float)(highPrice[length - 1 - i])
            # print("max = " + str(maxStockPrice))

    # minStockPrice = 17081.89
    # stockPriceCurrent = 17158.81
    # maxStockPrice = 17158.81
    print("stockPriceCurrent = " + str(stockPriceCurrent))
    print("minStockPrice = " + str(minStockPrice))
    print("maxStockPrice = " + str(maxStockPrice))
    if ((maxStockPrice - minStockPrice) == 0):
        rsv = 100
    else:
        rsv = (stockPriceCurrent - minStockPrice) / \
            (maxStockPrice - minStockPrice) * 100

    k = (2 / 3) * pastK + (1 / 3) * rsv
    d = (2 / 3) * pastD + (1 / 3) * k

    #斜率計算 & buyCall buyPut
    buy = ""
    kSlope = abs((k - pastK) / 5)
    dSlope = abs((d - pastD) / 5)
    if (kSlope >= 1.068 and pastK >= 75):
        if (k == d or k < d):
            buy = "buyPut"
            print("buy put !!!")
            line_bot_api.push_message(yourid, TextSendMessage(text=buy))

    if (kSlope >= 1.068 and pastK <= 26):
        if(k == d or k > d):
            buy = "buyCall"
            print("buy call !!!")
            line_bot_api.push_message(yourid, TextSendMessage(text=buy))

    pastK = k
    pastD = d
    print("K = " + str(k) + " D = " + str(d) + " rsv = " + str(rsv))
    kdVal = "K = " + str(k) + " D = " + str(d)
    line_bot_api.push_message(yourid, TextSendMessage(text=kdVal))

    stockData = {'dateTime': dateTime,
                 'stockPrice': stockPriceCurrent, 'K': k, 'D': d, 'buy': buy, "close": closePrice, "high": highPrice, "low": lowPrice, "closePriceTmp": closePriceTmp, "highPriceTmp": highPriceTmp, "lowPriceTmp": lowPriceTmp}

    # df = pd.DataFrame.from_dict(stockData, orient='index').T
    # path = filename
    # with open(path, 'a+', newline='') as f:
    #     fieldName = ['dateTime', 'stockPrice', 'K', 'D', 'buy', 'close', 'high', 'low', 'closePriceTmp', 'highPriceTmp', 'lowPriceTmp']
    #     csv_write = csv.DictWriter(f, fieldnames=fieldName)
    #     # csv_write = csv.writer(f)
    #     if (num == 1):
    #         csv_write.writeheader()
    #     csv_write.writerow(stockData)

while (int(datetimeStr) > 900 and int(datetimeStr) > 1335):
    header = Headers(
        browser="chrome",  # Generate only Chrome UA
        os="win",  # Generate ony Windows platform
        headers=True  # generate misc headers
    )

    headerGen = header.generate()
    #headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36', 'Connection':'keep-alive'}

    # now = datetime.today()
    # nowStr = now.strftime("%H%M")
    strTime = "現在時間 : " + datetimeStr
    line_bot_api.push_message(yourid, TextSendMessage(text=strTime))

    restart = False
    count = 0
    while(restart == True or count == 0):
        dateTime = datetime.now().timestamp()
        dateTimeStr = str(dateTime)
        dateTimeStrFix = dateTimeStr[:10] + '000'

        stockUrl = 'https://www.wantgoo.com/investrue/0000/historical-five-minutes-candlesticks?before=' + dateTimeStrFix
        print(stockUrl)
        response = requests.get(stockUrl, headers=headerGen) 
        print("status code = " + str(response.status_code))
        #print("response text = " + str(response))
        
        if (response.status_code == 200):    
            try :
                responseJson = json.loads(response.text)
                firstTimestamp = responseJson[0]["time"]
                # dateTimeStrFix = 1618734589
                for i in range(0, 9):
                    highPrice.append(responseJson[i]["high"])
                    highPriceTmp.append(responseJson[i]["high"])
                    lowPrice.append(responseJson[i]["low"])
                    lowPriceTmp.append(responseJson[i]["low"])
                    closePrice.append(responseJson[i]["close"])
                    closePriceTmp.append(responseJson[i]["close"])   
                rsvCal(datatimeStr2, closePrice, highPrice, lowPrice, closePriceTmp, highPriceTmp, lowPriceTmp)

                count = count + 1
                restart = False
            except:
                print("json loads fail")
                print("reload again")
                restart = True
            
            # print("responseJson = " + str(responseJson))
            # logging.debug(responseJson)       

        highPrice.clear()
        lowPrice.clear()
        closePrice.clear()

        now = datetime.now()
        datetimeStr = now.strftime("%H%M")
        datatimeStr2 = now.strftime("%H:%M")

        time.sleep(60)

if __name__ == "__main__":
    print("here")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# schedule.every(1).minutes.days.at("15:10").do(job)
#schedule.every().day.at("16:37").do(job)

# while(True):
    # schedule.run_pending()
    # time.sleep(1)
    # print(responseJson[1]["time"])

    # soup = BeautifulSoup(response.text, "lxml")
    # # print(soup)

    # table = soup.find_all('p')
    # # print(table)
    # change = str(table[30])
    # # print(change)
    # stockPrice = re.split('>|<', change)
    # # stockPrice = str(stockPrice[2]).split('+')
    # # print(stockPrice)
    # # print(len(stockPrice))
    # stockPriceConvert = stockPrice[2].replace(',', '')
    # # print(stockPriceConvert)
    # if (count == 9):
    #     data.append(stockPriceConvert)
    #     rsvCal(data)
    #     count = 9
    # else:
    #     data.append(stockPriceConvert)
    #     count = count + 1

    # time.sleep(12000)

    # if len(stockNotFound) == 0:
    #     title = soup.find_all('div', class_='main_title')
    #     change = str(title)
    #     stockNum = re.split('>|<', change)
    #     print(stockNum[2])
    #     subTitle = soup.find_all('div', class_='main_subTitle')
    #     change = str(subTitle)
    #     stockName = re.split('>|<', change)
    #     print(stockName[2])

    #     table = soup.find_all('span')
    #         # print(table)

    #         # for i in range(30, 33):
    #         #     change = str(table[i])
    #         #     splited = re.split('>|<', change)
    #         #     print(splited[2])

    #         change = str(table[30])
    #         stockPrice = re.split('>|<', change)
    #         print(stockPrice[2])

    #         change = str(table[31])
    #         stockUpDn = re.split('>|<', change)
    #         print(stockUpDn[2])

    #         change = str(table[32])
    #         stockPercent = re.split('>|<', change)
    #         print(stockPercent[2])

    #         data['stock'].append({
    #             'stockNum': stockNum[2],
    #             'stockName': stockName[2],
    #             'stockPrice': stockPrice[2],
    #             'stockUpDn': stockUpDn[2],
    #             'stockPercent': stockPercent[2]
    #         })

    #         # data["stockNum"] = stockNum[2]
    #         # data["stockName"] = stockName[2]
    #         # data["stockPrice"] = stockPrice[2]
    #         # data["stockUpDn"] = stockUpDn[2]
    #         # data["stockPercent"] = stockPercent[2]

    #         # data = {'stockNum': stockNum[2], 'stockName': stockName[2],
    #         #         'stockPrice': stockPrice[2], 'stockUpDn': stockUpDn[2], 'stockPercent': stockPercent[2]}
    #         output = json.dumps(data)
    #         # print(output)

    #         # if(stockNum != 9998):
    #         #     str_json += (str(data) + ",")
    #         #     print(str_json)
    #         #     f = open('stockInfo.json', 'w')
    #         #     f.write(str_json)
    #         # else:
    #         #     str_json += "]"
    #         #     f.close()
    #         # if count != 1:
    #         #     data = data + data
    #         # print(data)

    #     time.sleep(5)

    # # f = open('stockInfo.json', 'w')
    # # f.write(str_json)
    # # f.close()
    # with open('stockInfo.json', 'w', encoding='utf-8') as outfile:
    #     json.dump(data, outfile, ensure_ascii=False, indent=4)

    # # stockUrl = 'https://invest.cnyes.com/twstock/tws/1109'
    # # https://pchome.megatime.com.tw/stock/sid1109.html

    # # stockUrl = 'https://invest.cnyes.com/twstock/tws/9909'
    # # response = requests.get(stockUrl, headers=headers)
    # # soup = BeautifulSoup(response.text, "lxml")

    # # stockNotFound = soup.find_all('div', class_='notfound')
    # # print(stockNotFound)
