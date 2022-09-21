# HFT Bot Binance Futures
High Frequency Trading bot using 

### Python Libraries (For Technical Analysis):
- Tulipy
- TA-Lib
- Numpy

<br>

### API Used:
<ul>
<li> Binance API</li>
  <ul>
  <li> Websocket to obtain stream of the latest market price of the specified trading pair </li>
  <li> REST API to execute Futures trades</li>
  </ul>
<li> Taapi API</li>
  <ul>
  <li> To obtain additional Technical Analysis info</li>
  </ul>
<li> Telegram API</li>
  <ul>
  <li> Start/Stop the bot</li>
  <li> Displays all buy/sell trades and whether they are long/short positions</li>
  <li> Displays profit/loss</li>
  </ul>
 </ul>
<br> 
  
### Config:
- Set Backtesting to true 
  - if you want to run the bot in simulation mode without executing actual trades, the p&l are monitored. 
  - Useful for testing different Technical Analysis Indicators
- Set Backtesting to false
  - To execute real trades using your Binance account 
