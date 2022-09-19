import websocket, json, pprint, talib, numpy
import config
import datetime as dt
import requests
import datetime
import time
import sys
from binance.client import Client
from binance.enums import *
from binance.client import Client


#Only Change TRADE_SYMBOL [Buy/Sell]
TRADE_SYMBOL = config.symbol
TRADE_SYMBOL_lowercase = TRADE_SYMBOL.lower()
SOCKET = "wss://stream.binance.com:9443/ws/{0}@kline_1m".format(TRADE_SYMBOL_lowercase)
client = Client(config.API_KEY, config.API_SECRET)
RSI_PERIOD = config.RSI_PERIOD
RSI_OVERBOUGHT = config.RSI_OVERBOUGHT
RSI_OVERSOLD = config.RSI_OVERSOLD
#################################### Logging #################################################
import logging
logging.basicConfig(filename='null',format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
#create a file handler
handler = logging.FileHandler('logfile.log')
handler.setLevel(logging.INFO)
#create a logging format
title = logging.Formatter('%(message)s')
handler.setFormatter(title)
# add the handlers to the logger
logger.addHandler(handler)
logger.info("Date                Close             %K                 %D                 Open Profit                 Total Profit                 Pos Status                 Profit (Previous Trade)        ")
info = logging.Formatter('%(asctime)s %(message)s ','%Y-%m-%d %H:%M:%S')
handler.setFormatter(info)
logger.addHandler(handler)

################################### Telegram Bot #############################################
def telegram_bot_sendtext(bot_message):
    if config.telegram_token:
        bot_token = config.telegram_token
        bot_chatID = config.telegram_chatid
        send_text = 'https://api.telegram.org/bot' + bot_token + \
            '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
        return response.json()





############################################Order Functions################################################
#get balance of futur account wallet (usdt , bnb , busd)
def balance():
    try:
        blnc = client.balance()
        for counter in blnc:
            for value in counter:
                if value == 'asset':
                    print(value , ' >> ' , counter[value])
                if value == 'balance' :
                    print(value , ' >> ' , counter[value])
                    #Telegram Notif
                    msg = f"{value}: ${counter[value]}"
                    telegram_bot_sendtext(msg)
                if value == 'withdrawAvailable':
                    print(value , ' >> ' , counter[value])
    except Exception as Error:
        print(Error)
#create new order
def new_order(symbol , type , quantity , side , priceProtect = False ,
              closePosition = False , price = None, stopPrice = None , positionSide = None ,
              reduceonly = False , timeInForce = None):
    try:
        result = client.new_order(side=side,
                                  quantity=quantity,
                                  symbol=symbol,
                                  reduceOnly=reduceonly,
                                  positionSide=positionSide,
                                  stopPrice = stopPrice,
                                  timeInForce = timeInForce,
                                  price= price,
                                  closePosition= closePosition,
                                  priceProtect= priceProtect ,
                                orderType=type)
        print(result)
        return result
    except Exception as Error:
        print(Error)




#print history of last close position
def HPrint(history):
    for value in history[0]:
        if value == 'time':
            print('time >> ', datetime.fromtimestamp(history[0]['time'] / 1e3))
        elif value == 'realizedPnl':
            print(value, f' >> {float(history[0][value])} ')
        else:
            print(value , f' >> {history[0][value]} ')
#get history from 5 days ago until now
def history():
    dt2 = datetime.now()
    dt = datetime(dt2.year, dt2.month, dt2.day-5)
    milliseconds = int(round(dt.timestamp() * 1000))
    now = int(round(dt2.timestamp())*1000)
    his2 = client.trade_list(limit=1000 , startTime=milliseconds , endTime=now)
    HPrint(his2)
#get information of open position
def position_info():
    posInf = client.position_info()
    for counter in posInf:
        if counter['symbol'] == TRADE_SYMBOL:
            print(counter)
            return counter
#close orders function
def close_orders():
    client.cancel_all_open_orders(symbol=TRADE_SYMBOL)










####################################Variables######################################
closes = []
in_position = False
type_position = False
openLong = 0.0000
openShort = 0.0000
closeLong = 0.0000
closeShort = 0.0000
profit = 0.0000
totalProfit = 0.0000
openPositionProfit = 0.0000 
positionStatus = 'NULL'
maximumProfitLoss = -10.0000
##################################Main#############################################
def on_open(ws):
    print('opened connection')
    #Telegram Notif
    msg = f"Opened Connection"
    telegram_bot_sendtext(msg)
def on_close(ws):
    print('closed connection')
def on_message(ws, message):
    global closes, in_position, type_position
    global openLong, openShort, closeLong, closeShort, profit, totalProfit, openPositionProfit
    global positionStatus
    global maximumProfitLoss
    #Force shutdown if Total Profit below -10%
    if (totalProfit < maximumProfitLoss):
        #CLOSE ALL OPEN POSITIONS FIRST
        if config.backtesting == False:
            close_orders()
        print("Total Profit -10% so STOP the bot!")
        print("All open trades are force closed")
        #Telegram Notif
        msg = f"*Total Profit -10% so STOP the bot!\nAll open trades are force closed*"
        telegram_bot_sendtext(msg)
        sys.exit("BOT SHUTDOWN")
    try:
        

        # fig, axes = plt.subplots(2, 1, sharex=True)
        # #ax1, ax2 = axes[0], axes[1]
        #print('received message')
        json_message = json.loads(message)
        #pprint.pprint(json_message)
        messageTime = json_message['E']
        timestamp = dt.datetime.fromtimestamp(int(messageTime)/1000)
        messageSentTime = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        #print("Message Sent Time : ")
        #print(messageSentTime)
        candle = json_message['k']
        is_candle_closed = candle['x']
        close = candle['c']
        # timeOfClose = candle['T']
        # print("Original Time of Close from candle: ")
        # print(timeOfClose)
        # timestamp = dt.datetime.fromtimestamp(int(timeOfClose)/1000)
        # closingTime = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        # print("Closing Time : ")
        # print(closingTime)

        #Add close price to list only if candle is closed
        if is_candle_closed:
            print("candle closed at {}".format(close))
            closes.append(float(close))
            #print("closes")
            #print(closes)
        



            #Number of closes is greater than 14, the first 14 values cannot be used to calculate RSI or Stoch RSI
            if len(closes) > RSI_PERIOD:
                np_closes = numpy.array(closes)
                rsi = talib.RSI(np_closes, RSI_PERIOD)
                #print("all rsis calculated so far")
                #print(rsi)
                last_rsi = rsi[-1]
                print("the current rsi is {}".format(last_rsi))



                #Calculate StochRSI
                fastk, fastd = talib.STOCH(rsi, rsi, rsi, fastk_period=14,slowk_period=3,slowk_matype=0,slowd_period=3, slowd_matype=0)
                #Matplot lib (plt.show() idk where to put it)
                # axes[1].plot(fastk, 'r-')
                # axes[1].plot(fastd, 'r-')
                last_stochrsi_fastk = fastk[-1]
                print("the current STOCH rsi K is {}".format(last_stochrsi_fastk))
                last_stochrsi_fastd = fastd[-1]
                print("the current STOCH rsi D is {}".format(last_stochrsi_fastd))

                
                #Long/Short Decision
                #Go Long
                if (last_stochrsi_fastk > last_stochrsi_fastd): #The may bug occur when candle K reaches 100, if it does, don't let it exit the trade
                    #Greater than and less than are bugged, idk why they will be flipped
                    print("Fast K > Fast D")
                    if (in_position == True and type_position == False): #opened short position, so exit short position and open long position
                        #Close all orders
                        print("Close SHORT position at : $" + close)
                        closeShort = float(close)
                        positionStatus = 'Close SHORT Pos'
                        
                        profit = (openShort - closeShort)/openShort*100
                        totalProfit += profit
                        print("Current trade profit: ", format(profit,'2f'),"%")
                        print("Total trade profit: ", format(totalProfit,'2f'),"%")
                        print("")
                        in_position = False
                        #Backtesting settings
                        if (config.backtesting == False):
                            close_orders()
                            #Telegram Notif
                            msg = f"{positionStatus} : {history()}%\nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*"
                            telegram_bot_sendtext(msg)
                        else:
                            #Telegram Notif
                            msg = f"{positionStatus}\nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*"
                            telegram_bot_sendtext(msg)
                        
                    if in_position == False :
                        #Place Long Order
                        
                        type_position = True
                        positionStatus = 'LONG'
                        print("Open LONG position at : $" + close)
                        openLong = float(close)          
                        
                        #Backtesting Settings
                        if (config.backtesting == False):
                            #Place SHORT Order
                            order = new_order(symbol=TRADE_SYMBOL, type='MARKET', quantity=config.buy_quantity, side='BUY')
                            in_position = True
                            #Telegram Notif
                            msg = f"{positionStatus} : {config.buy_quantity} of {TRADE_SYMBOL} at {order} {config.alt}"
                            telegram_bot_sendtext(msg)
                        else:
                            in_position = True
                            #Telegram Notif
                            msg = f"{positionStatus} : 0 of {TRADE_SYMBOL} at {close}{config.alt}"
                            telegram_bot_sendtext(msg)
                        
                    
                #Go Short
                if (last_stochrsi_fastk < last_stochrsi_fastd): 
                    print("Fast K < Fast D")
                    if (in_position == True and type_position == True): #opened long position, so exit long position and open short position
                        
                        
                        #Close all orders
                        
                        print("Close LONG position at : $" + close)
                        positionStatus = 'Close Long Pos'
                        closeLong = float(close)
                        profit = (closeLong - openLong)/openLong*100
                        totalProfit += profit
                        print("Current trade profit: ", format(profit,'2f'),"%")
                        print("Total trade profit: ", format(totalProfit,'2f'),"%")
                        print("")
                        in_position = False
                        #Backtesting settings
                        if (config.backtesting == False):
                            close_orders()
                            #Telegram Notif
                            msg = f"{positionStatus} : {history()}%\nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*"
                            telegram_bot_sendtext(msg)
                        else:
                            #Telegram Notif
                            msg = f"{positionStatus}\nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*"
                            telegram_bot_sendtext(msg)
                        
                    if in_position == False :
                        
                        type_position = False
                        positionStatus = 'SHORT'
                        print("Open SHORT position at : $" + close)  
                        openShort = float(close)         
                        
                        #Backtesting Settings
                        if (config.backtesting == False):
                            #Place SHORT Order
                            order = new_order(symbol=TRADE_SYMBOL, type='MARKET', quantity=config.buy_quantity, side='SELL')
                            in_position = True
                            #Telegram Notif
                            msg = f"{positionStatus} : {config.buy_quantity} of {TRADE_SYMBOL} at {order} {config.alt}"
                            telegram_bot_sendtext(msg)
                        else:
                            in_position = True
                            #Telegram Notif
                            msg = f"{positionStatus} : 0 of {TRADE_SYMBOL} at {close}{config.alt}"
                            telegram_bot_sendtext(msg)
                        
                #Track profitability of open position
                if (in_position == True and type_position == True): #Long position is open
                    currentPrice = float(close)
                    openPositionProfit = (currentPrice - openLong)/openLong*100
                    print("Open trade profit: ", format(openPositionProfit,'2f'),"%")
                if (in_position == True and type_position == False): #Short position is open
                    currentPrice = float(close)
                    openPositionProfit = (openLong - currentPrice)/openLong*100
                    print("Open trade profit: ", format(openPositionProfit,'2f'),"%")
        logger.info("$" + str(close) + "     "
            + str(last_stochrsi_fastk) + "     "
            + str(last_stochrsi_fastd) + "     "
            + str(openPositionProfit) + "%     "
            + str(totalProfit) + "%    "
            + positionStatus + "       "
            + str(profit) + "%")
        
        profit = 0.0000
    
    except:
        # ping client to avoid timeout
        client = Client(config.API_KEY, config.API_SECRET)




            

                
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
