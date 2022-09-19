from binance.client import Client
from os import getenv


API_KEY = '<yourKEY>'
API_SECRET = '<yourSECRET>'

#Telegram bot
telegram_token = getenv('TELEGRAM_TOKEN', '<yourToken>')

live_data_telegram_token = getenv('TELEGRAM_TOKEN', '<yourToken>')
telegram_chatid = getenv('TELEGRAM_CHATID', '<yourChatID>')




#Make sure to update both
taapi_symbol = 'ALICE/USDT'

symbol = "ALICEUSDT"


sell_quantity = 10
buy_quantity = 10


alt = 'USDT'


#WARNING
backtesting = True
leverage = 1
marginType = "CROSSED"
type = "MARKET"

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30




#Taapi 
chern_secret = '<yourSecret>'
shern_secret = '<yourSecret>'

exchange = 'binance'
interval = '1m'

#SAR
optInAcceleration = 0.028
#optInMaximum = 0.2

