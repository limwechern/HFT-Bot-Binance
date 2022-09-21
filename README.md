# HFT Bot Binance Futures
High Frequency Trading bot using 

### Python Libraries (For Technical Analysis):
- Tulipy
- TA-Lib
- Numpy

### API Used:
- Binance API
  - Websocket to obtain stream of the latest market price of the specified trading pair 
  - REST API to execute Futures trades
- Taapi API
  - To obtain additional Technical Analysis info)
- Telegram API
  - Start/Stop the bot
  - Shows all buy/sell trades and whether they are long/short positions
  - Displays profit/loss
  
### Config:
- Set Backtesting to true 
  - if you want to run the bot in simulation mode without executing actual trades, the p&l are monitored. 
  - Useful for testing different Technical Analysis Indicators
- Set Backtesting to false
  - To execute real trades using your Binance account 
