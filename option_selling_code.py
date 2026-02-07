from SmartApi.smartConnect import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import pyotp
import pandas as pd
import requests
import json
import time
import schedule
import sys


with open('angel_one_credentials.json','r') as file:
    config=json.load(file)

api_key = config['api_key']
client_id = config['client_id']
pin = config['pin']
smartApi = SmartConnect(api_key)

qr_token = config['qr_token']
totp = pyotp.TOTP(qr_token).now()
data = smartApi.generateSession(client_id, pin, totp)

access_token = data['data']['jwtToken']
refresh_token = data['data']['refreshToken']
feed_token = data['data']['feedToken']

config['access_token']= access_token
config['feed_token']= feed_token
config['refresh_token'] = refresh_token

with open('angel_one_credentials.json', 'w') as file:
    json.dump(config, file, indent=4)


def fetch_ltp_and_sell_straddle():

    nifty50_ltp=smartApi.ltpData("NSE", "NIFTY 50", "99926000")
    ltp = nifty50_ltp['data']['ltp']
    atm_strike = round(ltp / 50) * 50
    print('ltp is :',ltp)

    expiry_date='19DEC24'

    call_option=f"NIFTY{expiry_date}{atm_strike}CE"
    put_option=f"NIFTY{expiry_date}{atm_strike}PE"

    """symbol token generation"""

    df=pd.read_csv('angel_broking_instruments.csv')
    # print(df)

    symbol_token1=df.loc[df['symbol'] == call_option, 'token'].values[0]
    symbol_token1 = str(symbol_token1)
    # print(symbol_token1)
    symbol_token2=df.loc[df['symbol'] == put_option, 'token'].values[0]
    symbol_token2 = str(symbol_token2)
    # print(symbol_token2)

    config['ltp']=ltp
    config['call_option_strike']=call_option
    config['put_option_strike']=put_option
    config['symbol_token1'] =symbol_token1
    config['symbol_token2'] =symbol_token2

    with open('angel_one_credentials.json', 'w') as file:
        json.dump(config, file, indent=4)

    """placing orders"""

    call_option_sell = {
                "variety": "NORMAL",
                "tradingsymbol": call_option,
                "symboltoken": symbol_token1,
                "transactiontype": "SELL",
                "exchange": "NFO",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "quantity": "50"
                }
    orderid = smartApi.placeOrder(call_option_sell)
    print(f'order placed :{orderid}')

    put_option_sell = {
                "variety": "NORMAL",
                "tradingsymbol": put_option,
                "symboltoken": symbol_token2,
                "transactiontype": "SELL",
                "exchange": "NFO",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "quantity": "50"
                }
    orderid = smartApi.placeOrder(put_option_sell)
    print(f'order placed :{orderid}')
    sys.exit()

schedule.every().day.at("09:20").do(fetch_ltp_and_sell_straddle)

print("Scheduler started. Waiting to sell straddle at 9:20 AM...")

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)

# fetch_ltp_and_sell_straddle()