from SmartApi.smartConnect import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import pyotp
import pandas as pd
import json
import time
import schedule

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


correlation_id = "abc123"
action = 1
mode = 2
token_list = [
    {
        "exchangeType": 1,
        "tokens": ["99926000"]
    }
]
#retry_strategy=0 for simple retry mechanism
sws = SmartWebSocketV2(access_token, api_key, client_id ,feed_token,max_retry_attempt=2, retry_strategy=0, retry_delay=3, retry_duration=30)

position1_open= True
position2_open=True

def fetch_ltp(message):
    global position1_open,position2_open

    with open('angel_one_credentials.json', 'r') as file:
        config = json.load(file)

    nifty_entry_price = config['ltp']
    call_option = config['call_option_strike']
    put_option = config['put_option_strike']
    symbol_token1 = config['symbol_token1']
    symbol_token2 = config['symbol_token2']

    nifty_abs=message['last_traded_price']
    nifty_ltp=nifty_abs/100
    # print(nifty_ltp)
    # print(nifty_ltp >= (nifty_entry_price * 1.0095))

    """ 1.0095 and 0.9905 is for 0.95% up and down fri,mon,tue, """
    """ 1.0051 and 0.9949 is for 0.51% up and down wed,thu """

    if nifty_ltp >= (nifty_entry_price * 1.0095) and position1_open:  # --> place to change
        exit_call_option = {
            "variety": "NORMAL",
            "tradingsymbol": call_option,
            "symboltoken": symbol_token1,
            "transactiontype": "BUY",
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": "50"
        }
        orderid = smartApi.placeOrder(exit_call_option)
        print(f'order placed :{orderid}')
        print(f"Exited call option at NIFTY 50 LTP: {nifty_ltp}")
        position1_open = False

    elif nifty_ltp <= (nifty_entry_price * 0.9905) and position2_open:  # --> place to change

        # Exit put option
        exit_put_option= {
            "variety": "NORMAL",
            "tradingsymbol": put_option,
            "symboltoken": symbol_token2,
            "transactiontype": "BUY",
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": "50"
        }
        orderid = smartApi.placeOrder(exit_put_option)
        print(f'order placed :{orderid}')
        print(f"Exited put option at NIFTY 50 LTP: {nifty_ltp}")
        position2_open = False
    # else:
    #     print(f'waiting to hit stoploss : {nifty_ltp}')

def on_data(wsapp, message):
    # print(message)
    fetch_ltp(message)
    # close_connection()

def on_open(wsapp):
        sws.subscribe(correlation_id, mode, token_list)
        print('websocket started')
        # sws.unsubscribe(correlation_id, mode, token_list1)

def on_error(wsapp, error):
    print(error)

def on_close(wsapp):
    print('close')

def close_connection():
    sws.close_connection()


def trigger_stoploss():
    # Assign the callbacks.
    sws.on_open = on_open
    sws.on_data = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    sws.connect()

schedule.every().day.at("09:21").do(trigger_stoploss)

print("Scheduler started. Waiting to hit the stoploss...")

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)

# trigger_stoploss()