import config
import requests, pprint, json




shern_secret = config.shern_secret
exchange = config.exchange
taapi_symbol = config.taapi_symbol
interval = config.interval
optInAcceleration = config.optInAcceleration

# Define indicator
SAR_url = "sar"
  
# Define endpoint 
endpoint = f"https://api.taapi.io/{SAR_url}"
  
# Define a parameters dict for the parameters to be sent to the API 
parameters = {
    'secret': shern_secret,
    'exchange': exchange,
    'symbol': taapi_symbol,
    'interval': interval,
    'optInAcceleration' : optInAcceleration
    } 


def getSAR():
    # Send get request and save the response as response object 
    response = requests.get(url = endpoint, params = parameters)
    
    # Extract data in json format 
    SAR_JSON = response.json() 
    SAR = SAR_JSON.get('value')


    # Print result
    return SAR



