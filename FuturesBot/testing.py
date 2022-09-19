
from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance.client import Client
from binance.enums import *
from binance.client import Client
import config


alt = config.alt
type = config.type

TRADE_SYMBOL = config.symbol
TRADE_SYMBOL_lowercase = TRADE_SYMBOL.lower()
SOCKET = "wss://stream.binance.com:9443/ws/{0}@kline_1m".format(TRADE_SYMBOL_lowercase)
client = Client(config.API_KEY, config.API_SECRET)
request_client = RequestClient(api_key=config.API_KEY, secret_key=config.API_SECRET, url= "https://fapi.binance.com")

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
    global futuresBalance, buyQuantity

    price = request_client.get_symbol_price_ticker(TRADE_SYMBOL)
    price = price[0].price

    futuresBalance = get_futures_balance()
    qty = (int(futuresBalance) / price) * 1
    qty = float(qty * 0.99)

    return qty
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

#Execute an order, this can open and close a trade
def execute_order(_symbol, _type, _side, _position_side, _qty):
    request_client.post_order(symbol=_symbol,
                      ordertype=_type,
                      side=_side,
                      #positionSide=_position_side,
                      quantity = str(_qty))

#Place LONG Order
global buyQuantity
buyQuantity = calculate_position_size()
print("Calculated [LONG] position size : " + str(buyQuantity))
prcision = get_market_precision()
print("Calculated precision : " + str(prcision))
rounded = round_to_precision(buyQuantity, prcision)
print("Rounded : " + str(rounded))
order = execute_order(_symbol=TRADE_SYMBOL, _type=type, _side="BUY", _position_side="LONG", _qty=rounded)