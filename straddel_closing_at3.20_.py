from SmartApi.smartConnect import SmartConnect
import json
import schedule
import time
import sys
import pyotp

with open('angel_one_credentials.json','r') as file:
    config=json.load(file)

api_key = config['api_key']
client_id = config['client_id']
pin = config['pin']
smartApi = SmartConnect(api_key)

qr_token = config['qr_token']
totp = pyotp.TOTP(qr_token).now()
data = smartApi.generateSession(client_id, pin, totp)

"""closing the orders"""

def exit_the_straddle():
    net_qty = smartApi.position()
    for position in net_qty['data']:
        if position['netqty'] != '0':
            val = abs(int(position['netqty']))
            quantity = str(val)

            exit_option = {
                "variety": "NORMAL",
                "tradingsymbol": position['tradingsymbol'],
                "symboltoken": position['symboltoken'],
                "transactiontype": "BUY",
                "exchange": "NFO",
                "ordertype": "MARKET",
                "producttype": "INTRADAY",
                "duration": "DAY",
                "quantity": quantity
            }
            orderid = smartApi.placeOrder(exit_option)
            print(f'order placed :{orderid}')
    sys.exit()

schedule.every().day.at("15:15").do(exit_the_straddle)
print("Scheduler started. Waiting to exit positions at 3:15 PM...")

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)

