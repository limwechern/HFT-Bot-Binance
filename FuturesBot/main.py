import websocket, json, pprint
import config
import datetime as dt
import requests
import datetime
import time
import sys
from binance.client import Client
from binance.enums import *
from binance.client import Client


import numpy 
import tulipy as ti
from getSAR import *

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *

forceShutdown = False





#Only Change TRADE_SYMBOL [Buy/Sell]
TRADE_SYMBOL = config.symbol
TRADE_SYMBOL_lowercase = TRADE_SYMBOL.lower()
SOCKET = "wss://fstream.binance.com/ws/{0}@kline_1m".format(TRADE_SYMBOL_lowercase)
client = Client(config.API_KEY, config.API_SECRET)
request_client = RequestClient(api_key=config.API_KEY, secret_key=config.API_SECRET, url= "https://fapi.binance.com")
RSI_PERIOD = config.RSI_PERIOD
RSI_OVERBOUGHT = config.RSI_OVERBOUGHT
RSI_OVERSOLD = config.RSI_OVERSOLD
leverage = config.leverage
marginType = config.marginType
backtesting = config.backtesting
alt = config.alt
type = config.type

####################################Variables######################################
closes = []
close = 0.0000
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
###############################TAAPI############################################
#STOCH RSI
chern_secret = config.chern_secret
exchange = config.exchange
taapi_symbol = config.taapi_symbol
interval = config.interval
# Define indicator
STOCHrsi_url = "stochrsi"
# Define endpoint 
endpoint = f"https://api.taapi.io/{STOCHrsi_url}"
# Define a parameters dict for the parameters to be sent to the API 
parameters = {
    'secret': chern_secret,
    'exchange': exchange,
    'symbol': taapi_symbol,
    'interval': interval,
    'kPeriod' : '3'
    } 





# #SAR
# shern_secret = config.shern_secret
# exchange = config.exchange
# taapi_symbol = config.taapi_symbol
# interval = config.interval
# # Define indicator
# SAR_url = "sar"
# # Define endpoint 
# endpoint = f"https://api.taapi.io/{SAR_url}"
# # Define a parameters dict for the parameters to be sent to the API 
# parameters = {
#     'secret': shern_secret,
#     'exchange': exchange,
#     'symbol': taapi_symbol,
#     'interval': interval,
#     } 





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
logger.info("Date                Close             SAR             %K                 %D                 Open Profit                 Total Profit                 Pos Status                 Profit (Previous Trade)        ")
info = logging.Formatter('%(asctime)s %(message)s ','%Y-%m-%d %H:%M:%S')
handler.setFormatter(info)
logger.addHandler(handler)








################################### Telegram Bot #############################################
import telebot
import os

API_TOKEN = config.telegram_token
bot = telebot.TeleBot(API_TOKEN)
myTeleChatID = config.telegram_chatid

def telegram_bot_sendtext(bot_message):
    if config.telegram_token:
        bot_token = config.telegram_token
        bot_chatID = config.telegram_chatid
        send_text = 'https://api.telegram.org/bot' + bot_token + \
            '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
        return response.json()

def tele_live_data(bot_message):
    if config.telegram_token:
        bot_token = config.live_data_telegram_token
        bot_chatID = config.telegram_chatid
        send_text = 'https://api.telegram.org/bot' + bot_token + \
            '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
        return response.json()












# ############################################Order Functions################################################
futuresBalance = 0.0000
preciseQuantity = 0.0000
roundedQty = 0.0000


#Get futures balances. We are interested in USDT by default as this is what we use as margin.
def get_futures_balance():
    balances = request_client.get_balance()
    asset_balance = 0
    for balance in balances:
        if balance.asset == alt:
            asset_balance = balance.balance
            break
    return asset_balance
    
#calculate how big a position we can open with the margin we have and the leverage we are using
def calculate_position_size():
    global futuresBalance, preciseQuantity
    price = request_client.get_symbol_price_ticker(TRADE_SYMBOL)
    price = price[0].price
    futuresBalance = get_futures_balance()
    qty = (int(futuresBalance) / price) * leverage
    qty = float(qty * 0.99)
    return qty

#Init the market we want to trade. First we change leverage type
#then we change margin type
def initialise_futures():
    try:
        request_client.change_initial_leverage(TRADE_SYMBOL, leverage)
    except Exception as e:
        print(e)
    try:
        request_client.change_margin_type(TRADE_SYMBOL, marginType)
    except Exception as e:
        print(e)


#get all of our open orders in a market
def get_orders():
    orders = request_client.get_open_orders(TRADE_SYMBOL)
    return orders, len(orders)
#get all of our open trades
def get_positions():
    positions = request_client.get_position_v2()
    return positions
#get trades we opened in the market the bot is trading in
def get_specific_positon():
    positions = get_positions()
    for position in positions:
        if position.symbol == TRADE_SYMBOL:
            break
    return position



# #get the liquidation price of the position we are in. - We don't use this - be careful!
# def get_liquidation():
#     position = get_specific_positon()
#     price = position.liquidationPrice
#     return price
# #Get the entry price of the position the bot is in
# def get_entry():
#     position = get_specific_positon()
#     price = position.entryPrice
#     return price
#Execute an order, this can open and close a trade
def execute_order(_symbol, _type, _side, _qty):
    request_client.post_order(symbol=_symbol,
                      ordertype=_type,
                      side=_side,
                      quantity = str(_qty))


#check if the position is still active, or if the trailing stop was hit.
def check_in_position():
    position = get_specific_positon()
    in_position = False
    if float(position.positionAmt) != 0.0:
        in_position = True
    return in_position

#Create a trailing stop to close our order if something goes bad, lock in profits or if the trade goes against us!
# def submit_trailing_order(client, _market="BTCUSDT", _type = "TRAILING_STOP_MARKET", _side="BUY",
#                           _qty = 1.0, _callbackRate=4):
#     client.post_order(symbol=_market,
#                       ordertype=_type,
#                       side=_side,
#                       callbackRate=_callbackRate,
#                       quantity = _qty,
#                       workingType="CONTRACT_PRICE")

# get the current market price
def get_market_price():
    price = request_client.get_symbol_price_ticker(TRADE_SYMBOL)
    price = price[0].price
    return price

#Used for limit market orders
# get the precision of the market, this is needed to avoid errors when creating orders
def get_market_precision():
    market_data = request_client.get_exchange_information()
    precision = 3
    for market in market_data.symbols:
        if market.symbol == TRADE_SYMBOL:
            precision = market.quantityPrecision
            break
    return precision
# round the position size we can open to the precision of the market
def round_to_precision(_qty, _precision):
    new_qty = "{:0.0{}f}".format(_qty , _precision)
    return float(new_qty)

def goLong():
    global preciseQuantity, roundedQty, in_position, type_position
    preciseQuantity = calculate_position_size()
    print("Calculated [LONG] position size : " + str(preciseQuantity))
    precision = get_market_precision()
    print("Calculated precision : " + str(precision))
    roundedQty = round_to_precision(preciseQuantity, precision)
    print("Rounded Quantity: " + str(roundedQty))
    order = execute_order(_symbol=TRADE_SYMBOL, _type=type, _side="BUY", _qty=roundedQty)
    in_position = True
    type_position = True
    return roundedQty
def goShort():
    global preciseQuantity, roundedQty, in_position, type_position
    preciseQuantity = calculate_position_size()
    print("Calculated [SHORT] position size : " + str(preciseQuantity))
    precision = get_market_precision()
    print("Calculated precision : " + str(precision))
    roundedQty = round_to_precision(preciseQuantity, precision)
    print("Rounded Quantity: " + str(roundedQty))
    order = execute_order(_symbol=TRADE_SYMBOL, _type=type, _side="SELL", _qty=roundedQty)
    in_position = True
    type_position = False
    return roundedQty

#close opened position
def close_position():
    global roundedQty
    global in_position 
    if in_position == True:
        if (type_position == True): #if long, close long position
            
            order = execute_order(_symbol=TRADE_SYMBOL, _type=type, _side="SELL", _qty=roundedQty)
            in_position= False
        else: #if short, close short position
            order = execute_order(_symbol=TRADE_SYMBOL, _type=type, _side="BUY", _qty=roundedQty)
            in_position = False
##################################Main#############################################
def on_open(ws):
    print('opened connection')
    #Telegram Notif
    msg = f"Opened Connection"
    telegram_bot_sendtext(msg)
def on_close(ws):
    print('Closed connection')
    #Telegram Notif
    msg = f"Closed Connection"
    telegram_bot_sendtext(msg)
def on_message(ws, message):
    global closes, in_position, type_position, close
    global openLong, openShort, closeLong, closeShort, profit, totalProfit, openPositionProfit
    global positionStatus
    global maximumProfitLoss, roundedQty
    global forceShutdown
    global futuresBalance, preciseQuantity
    if forceShutdown == True:
        sys.exit("BOT SHUTDOWN")

    #Force shutdown if Total Profit below -10%
    if (totalProfit < maximumProfitLoss):
        #CLOSE ALL OPEN POSITIONS FIRST
        if backtesting == False:
            close_position()
        print("Total Profit -10% so STOP the bot!")
        print("All open trades are force closed")
        #Telegram Notif
        msg = f"*Total Profit -10% so STOP the bot!\nAll open trades are force closed*"
        telegram_bot_sendtext(msg)
        forceShutdown = True
        sys.exit("BOT SHUTDOWN")
    try:
        json_message = json.loads(message)
        candle = json_message['k']
        close = candle['c']
        # is_candle_closed = candle['x']
        
        # timeOfClose = candle['T']
        # print("Original Time of Close from candle: ")
        # print(timeOfClose)
        # timestamp = dt.datetime.fromtimestamp(int(timeOfClose)/1000)
        # closingTime = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        # print("Closing Time : ")
        # print(closingTime)
        #Add close price to list only if candle is closed



            
            #CLOSE SHORT POSITION BASED ON STOCH RSI only
            if (last_stochrsi_fastk > last_stochrsi_fastd): 
                print("Fast K > Fast D")
                #Telegram Notif
                msg = f"{last_stochrsi_fastk} : {last_stochrsi_fastd} *<Fast K > Fast D>*"
                tele_live_data(msg)
                if (in_position == True and type_position == False): #opened short position, so exit short position
                    #Close all orders
                    print("Close SHORT position at : $" + close)
                    closeShort = float(close)
                    positionStatus = 'Close SHORT Pos'
                    
                    profit = (openShort - closeShort)/openShort*100
                    totalProfit += profit
                    print("Current trade profit: ", format(profit,'2f'),"%")
                    print("Total trade profit: ", format(totalProfit,'2f'),"%")
                    print("")
                    
                    #Backtesting settings
                    if (backtesting == False):
                        #buyQuantity = calculate_position_size()
                        close_position() #Buy to exit short position
                        #Telegram Notif
                        msg = f"{positionStatus} of {roundedQty} {TRADE_SYMBOL} : \nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*\n\nFutures Balance: ${get_futures_balance()}"
                        telegram_bot_sendtext(msg)
                    else:
                        in_position = False
                        #Telegram Notif
                        msg = f"{positionStatus}\nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*"
                        telegram_bot_sendtext(msg)

            #OPEN POSITION BASED ON SAR & STOCH RSI
            #UPtrend
            if (SAR < float(close)):
                print("SAR < close: UPTREND")
                #Telegram Notif
                msg = f"{SAR} : {close} *<SAR < close: UPTREND>*"
                tele_live_data(msg)
            #Long/Short Decision
                #Go Long
                
                if (last_stochrsi_fastk > last_stochrsi_fastd): #SAR says uptrend & SRSI says long, won't open trade if it conflicts 
                    print("Fast K > Fast D")
                    #Telegram Notif
                    msg = f"{last_stochrsi_fastk} : {last_stochrsi_fastd} *<Fast K > Fast D>*"
                    tele_live_data(msg)
                    if in_position == False :
                        #Place Long Order
                        
                        
                        positionStatus = 'LONG'
                        print("Open LONG position at : $" + close)
                        openLong = float(close)          
                        
                        #Backtesting Settings
                        if (backtesting == False):
                            #Place LONG Order
                            roundedQty = goLong() 
                            #Telegram Notif
                            msg = f"{positionStatus} : {preciseQuantity} of {TRADE_SYMBOL} at {roundedQty} {alt}"
                            telegram_bot_sendtext(msg)
                        else:
                            type_position = True
                            in_position = True
                            #Telegram Notif
                            msg = f"{positionStatus} : 0 of {TRADE_SYMBOL} at {close}{alt}"
                            telegram_bot_sendtext(msg)
                    
                else:
                    print("Uptrend but SRSI says short, won't open trade")
            
            #CLOSE LONG POSITION BASED ON STOCH RSI only
            if (last_stochrsi_fastk < last_stochrsi_fastd): 
                print("Fast K < Fast D")
                #Telegram Notif
                msg = f"{last_stochrsi_fastk} : {last_stochrsi_fastd} *<Fast K < Fast D>*"
                tele_live_data(msg)
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
                    
                    #Backtesting settings
                    if (backtesting == False):
                        #Close Long position
                        close_position()
                        futuresBalance = get_futures_balance()
                        #Telegram Notif
                        msg = f"{positionStatus} of {roundedQty} {TRADE_SYMBOL} : \nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*\n\nBalance: ${futuresBalance}"
                        telegram_bot_sendtext(msg)
                    else:
                        in_position = False
                        #Telegram Notif
                        msg = f"{positionStatus}\nCurrent Trade Profit: *{profit}%*\nTotal Profit: *{totalProfit}%*"
                        telegram_bot_sendtext(msg)
            #DOWNTrend
            if (SAR > float(close)):
                print("SAR > close: DOWNTREND")
                #Telegram Notif
                msg = f"{SAR} : {close} *<SAR < close: DOWNTREND>*"
                tele_live_data(msg)
                if (last_stochrsi_fastk < last_stochrsi_fastd): #SAR says downtrend & SRSI says short, won't open trade if it conflicts 
                    print("Fast K < Fast D")
                    #Telegram Notif
                    msg = f"{last_stochrsi_fastk} : {last_stochrsi_fastd} *<Fast K < Fast D>*"
                    tele_live_data(msg)
                    if in_position == False :
                        #Place SHORT order
                        
                        positionStatus = 'SHORT'
                        print("Open SHORT position at : $" + close)  
                        openShort = float(close)        
                        
                        #Backtesting Settings
                        if (backtesting == False):
                            #Place SHORT Order
                            roundedQty = goShort()
                            #Telegram Notif
                            msg = f"{positionStatus} : {preciseQuantity} of {TRADE_SYMBOL} at {roundedQty} {alt}"
                            telegram_bot_sendtext(msg)
                        else:
                            type_position = False
                            in_position = True
                            #Telegram Notif
                            msg = f"{positionStatus} : 0 of {TRADE_SYMBOL} at {close}{alt}"
                            telegram_bot_sendtext(msg)
                    
                else:
                    print("Downtrend but SRSI says long, won't open trade")
                        
        #Track profitability of open position
        if (in_position == True and type_position == True): #Long position is open
            currentPrice = float(close)
            openPositionProfit = (currentPrice - openLong)/openLong*100
            print("[LONG] Open trade profit: ", format(openPositionProfit,'2f'),"%")
            #Telegram Notif
            msg = f"<LONG> Open trade profit: *{openPositionProfit}%*"
            tele_live_data(msg)
        if (in_position == True and type_position == False): #Short position is open
            currentPrice = float(close)
            openPositionProfit = (openShort - currentPrice)/openShort*100
            print("[SHORT] Open trade profit: ", format(openPositionProfit,'2f'),"%")
            #Telegram Notif
            msg = f"<SHORT> Open trade profit: *{openPositionProfit}%*"
            tele_live_data(msg)
        logger.info("$" + str(close) + "     "
            + "$" + str(SAR) + ""
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


def PowerOn():
    global forceShutdown
    forceShutdown = False
    initialise_futures()
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()
def Shutdown():
    print("Shut down [Telegram]")
    #CLOSE ALL OPEN POSITIONS FIRST
    if backtesting == False:
        close_position()
        print("All open trades are force closed")
    #Telegram Notif
    msg = f"*You force shutdown the bot!\nAll open trades are force closed*"
    telegram_bot_sendtext(msg)
    global forceShutdown 
    global in_position
    in_position = False
    forceShutdown = True


@bot.message_handler(commands=['shutdown'])
def greet(message):
    msg = bot.reply_to(message, 'SHUTDOWN selected')
    Shutdown()


@bot.message_handler(commands=['poweron'])
def greet(message):
    msg = bot.reply_to(message, 'POWERON selected')
    PowerOn()
@bot.message_handler(commands=['balance'])
def greet(message):
    global futuresBalance
    msg = bot.reply_to(message, 'BALANCE selected')
    futuresBalance = get_futures_balance()
    #Telegram Notif
    msg = f"Futures Balance : ${futuresBalance}"
    telegram_bot_sendtext(msg)
@bot.message_handler(commands=['inposition'])
def greet(message):
    msg = bot.reply_to(message, 'IN POSITION selected')
    checkInPosition = check_in_position()
    #Telegram Notif
    msg = f"In Position : {checkInPosition}"
    telegram_bot_sendtext(msg)
@bot.message_handler(commands=['calculatepositionsize'])
def greet(message):
    msg = bot.reply_to(message, 'Calculate Position Size selected')
    positionSize = calculate_position_size()
    #Telegram Notif
    msg = f"Position Size (Qty): {positionSize}"
    telegram_bot_sendtext(msg)
@bot.message_handler(commands=['getorders'])
def greet(message):
    msg = bot.reply_to(message, 'Get Orders selected')
    openOrders = get_orders()
    #Telegram Notif
    msg = f"Open Orders: {openOrders}"
    telegram_bot_sendtext(msg)
@bot.message_handler(commands=['getpositions'])
def greet(message):
    msg = bot.reply_to(message, 'Get Positions selected')
    openPositions = get_specific_positon()
    #Telegram Notif
    msg = f"Open Positions: {openPositions}"
    telegram_bot_sendtext(msg)


#Telebot buttons UI
from telebot import types
@bot.message_handler(commands=['settings', '/'])
def send_welcome(msg):
    userChatID = str(msg.from_user.id) #Get the user's chat ID 
    print(userChatID)
    print(myTeleChatID)
    if  (userChatID == myTeleChatID): #Make sure the chat ID of the person using my bot is the same with my ID only
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=False)
        markup.add('Power ON', 'Get Balance', 'In Position?', 'Calculate Position Size', 'Get Open Orders', 'Get Open Positions', 'Shutdown', 'Total Profit') #the names of the buttons
        msg = bot.reply_to(msg, 'Settings Opened', reply_markup=markup)
        bot.register_next_step_handler(msg, process_step)
    else:
        #Telegram Notif
        msg = f"Someone tried to use your bot"
        telegram_bot_sendtext(msg)
def process_step(msg):
    if msg.text == 'Power ON':
        msg = bot.reply_to(msg, 'POWERON selected')
        PowerOn()
    elif msg.text=='Get Balance':
        global futuresBalance
        msg = bot.reply_to(msg, 'BALANCE selected')
        futuresBalance = get_futures_balance()
        #Telegram Notif
        msg = f"Futures Balance : ${futuresBalance}"
        telegram_bot_sendtext(msg)
    elif msg.text=='In Position?':
        msg = bot.reply_to(msg, 'IN POSITION selected')
        checkInPosition = check_in_position()
        #Telegram Notif
        msg = f"In Position : {checkInPosition}"
        telegram_bot_sendtext(msg)
    elif msg.text=='Calculate Position Size':
        msg = bot.reply_to(msg, 'Calculate Position Size selected')
        positionSize = calculate_position_size()
        #Telegram Notif
        msg = f"Position Size (Qty): {positionSize}"
        telegram_bot_sendtext(msg)
    elif msg.text=='Get Open Orders':
        msg = bot.reply_to(msg, 'Get Orders selected')
        openOrders = get_orders()
        #Telegram Notif
        msg = f"Open Orders: {openOrders}"
        telegram_bot_sendtext(msg)
    elif msg.text=='Get Open Positions':
        msg = bot.reply_to(msg, 'Get Positions selected')
        openPositions = get_positions()
        #Telegram Notif
        msg = f"Open Positions: {openPositions}"
        telegram_bot_sendtext(msg)
    elif msg.text=='Shutdown':
        msg = bot.reply_to(msg, 'SHUTDOWN selected')
        Shutdown()
    elif msg.text=='Total Profit':
        global totalProfit
        #Telegram Notif
        msg = f"Total Profit: {totalProfit}%"
        telegram_bot_sendtext(msg)
    return




#Telebot buttons UI
@bot.message_handler(commands=['config'])
def send_config(msg):
    userChatID = str(msg.from_user.id) #Get the user's chat ID 
    print(userChatID)
    print(myTeleChatID)
    if  (userChatID == myTeleChatID): #Make sure the chat ID of the person using my bot is the same with my ID only
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=False)
        markup.add('ALICE/USDT', 'AXT/USDT', 'COMP/USDT', 'SAND/USDT', 'MANA/USDT', 'CHRU/USDT', 'ALPHA/USDT', 'ENJU/USDT', 'TOMO/USDT') #the names of the buttons
        msg = bot.reply_to(msg, 'Settings Opened', reply_markup=markup)
        bot.register_next_step_handler(msg, show_choices)
    else:
        #Telegram Notif
        msg = f"Someone tried to use your bot"
        telegram_bot_sendtext(msg)
def show_choices(msg):
    global taapi_symbol, symbol
    if msg.text == 'ALICE/USDT':
        msg = bot.reply_to(msg, 'ALICE/USDT selected')
        taapi_symbol = 'ALICE/USDT'
        symbol = 'ALICEUSDT'
    elif msg.text=='AXT/USDT':
        msg = bot.reply_to(msg, 'AXT/USDT selected')
        taapi_symbol = 'AXT/USDT'
        symbol = 'AXTUSDT'
    elif msg.text=='COMP/USDT':
        msg = bot.reply_to(msg, 'COMP/USDT selected')
        taapi_symbol = 'COMP/USDT'
        symbol = 'COMPUSDT'
    elif msg.text=='SAND/USDT':
        msg = bot.reply_to(msg, 'SAND/USDT selected')
        taapi_symbol = 'SAND/USDT'
        symbol = 'SANDUSDT'
    elif msg.text=='MANA/USDT':
        msg = bot.reply_to(msg, 'MANA/USDT selected')
        taapi_symbol = 'MANA/USDT'
        symbol = 'MANAUSDT'
    elif msg.text=='CHRU/USDT':
        msg = bot.reply_to(msg, 'CHRU/USDT selected')
        taapi_symbol = 'CHRU/USDT'
        symbol = 'CHRUUSDT'
    elif msg.text=='ALPHA/USDT':
        msg = bot.reply_to(msg, 'ALPHA/USDT selected')
        taapi_symbol = 'ALPHA/USDT'
        symbol = 'ALPHAUSDT'
    elif msg.text=='ENJU/USDT':
        msg = bot.reply_to(msg, 'ENJU/USDT selected')
        taapi_symbol = 'ENJU/USDT'
        symbol = 'ENJUUSDT'
    elif msg.text=='TOMO/USDT':
        msg = bot.reply_to(msg, 'TOMO/USDT selected')
        taapi_symbol = 'TOMO/USDT'
        symbol = 'TOMOUSDT'
    
    return

@bot.message_handler(commands=['backtesting'])
def send_backtesting(msg):
    userChatID = str(msg.from_user.id) #Get the user's chat ID 
    print(userChatID)
    print(myTeleChatID)
    if  (userChatID == myTeleChatID): #Make sure the chat ID of the person using my bot is the same with my ID only
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=False)
        markup.add('TRUE', 'FALSE') #the names of the buttons
        msg = bot.reply_to(msg, 'Settings Opened', reply_markup=markup)
        bot.register_next_step_handler(msg, backtesting_settings)
    else:
        #Telegram Notif
        msg = f"Someone tried to use your bot"
        telegram_bot_sendtext(msg)


def backtesting_settings(msg):
    global backtesting
    if msg.text == 'TRUE':
        msg = bot.reply_to(msg, 'Backtesting: True')
        backtesting = True
    elif msg.text=='FALSE':
        msg = bot.reply_to(msg, 'Backtesting: False')
        backtesting = False
        



try:
  bot.infinity_polling()
except Exception as e:
    close_position()
    print("All positions closed")
    print(e)
    msg = f"{e}"
    telegram_bot_sendtext(msg)
