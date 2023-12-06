
import json

import requests
from flask import Flask, request, render_template, session, redirect

from DbManager import DBHelper
from BinanceManager import BinanceManager
_db = DBHelper()
_tables = _db.instance()
_users = _tables["Users"]
_tradingHistory = list(dict())
webhook_data = None
app = Flask(__name__)
import os
secret_key = os.urandom(24)
app.secret_key = secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
bots = []

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html")

@app.route('/create_bot', methods=['GET', 'POST'])
def create_bot():
    if 'username' in session:
        if request.method == 'POST':
            script = request.form.get('script')
            currencies = request.form.getlist('currencies')

            # Create a dictionary to store bot information
            bot = {
                'script': script,
                'currencies': currencies
            }

            # Add the bot to the list
            bots.append(bot)

            def create_pine_script(script):
                # TradingView API endpoint for creating a Pine script
                api_endpoint = 'https://api.tradingview.com/pine_script/full'

                # Create the payload with the Pine script
                payload = {
                    'content': script
                }

                # Make an HTTP POST request to the TradingView API endpoint
                response = requests.post(api_endpoint, json=payload)

                if response.status_code == 200:
                    print('Pine script created successfully')
                    # Retrieve the script ID from the response if needed
                    script_id = response.json().get('id')
                    print(f'Script ID: {script_id}')
                    return script_id
                else:
                    print('Failed to create Pine script')
                    print('Response:', response.text)
                    return None

            def create_alarm(script_id):
                # TradingView API endpoint for creating an alarm
                api_endpoint = 'https://api.tradingview.com/alarms'

                # Create the payload for the alarm
                payload = {
                    'condition': {
                        'script_id': script_id
                    },
                    'is_active': True
                }

                # Make an HTTP POST request to the TradingView API endpoint
                response = requests.post(api_endpoint, json=payload)

                if response.status_code == 201:
                    print('Alarm created successfully')
                    # Retrieve the alarm ID from the response if needed
                    alarm_id = response.json().get('id')
                    print(f'Alarm ID: {alarm_id}')
                else:
                    print('Failed to create alarm')
                    print('Response:', response.text)

            # Example usage
            pine_script = """
            //@version=5
            strategy("My Strategy", overlay=true)
            """

            # Create the Pine script
            script_id = create_pine_script(pine_script)

            if script_id is not None:
                # Create an alarm for the Pine script
                create_alarm(script_id)

            return render_template('create_bot.html', bot=bot)

        return render_template('create_bot.html')

    return render_template("login.html")
@app.route('/index', methods=['GET', 'POST'])
def index():
    try:
        if 'username' in session:
            print("Muhammed username in session")
            return redirect('/dashboard')

        if request.method == 'POST':
            email = request.form['username']
            password = request.form['password']

            user = _db.get_user(email, password)

            if user != None:
                session['username'] = email
                _tradingHistory = _db.get_active_trades(session["username"])

                return render_template('dashboard.html', username=email, trades=_tradingHistory)
            else:
                print("Muhammed else user")
                return render_template('login.html', message='Invalid login credentials')

        return render_template('login.html')
    except(Exception):
        print("Muhammed ex: " + Exception)

@app.route('/dashboard')
def dashboard():
    print("dashboard")
    if 'username' in session:
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return redirect('/index')


@app.route('/logout')
def logout():
    print("Logout")
    session.pop('username', None)
    return redirect('/index')

@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    #tradingviewApiKey = request.form['tradingviewApiKey']
    #tradingviewApiSecret = request.form['tradingviewApiSecret']
    binanceApiKey = request.form['binanceApiKey']
    binanceApiSecret = request.form['binanceApiSecret']

    user = {
        'Username': username,
        'Email': email,
        'Password': password,
        'BinanceApiKey': binanceApiKey,
        'BinanceApiSecret': binanceApiSecret,
    }
    result = _db.insert_user(user)
    if result == False:
        return redirect('/dashboard')

    return "Failed creating user"

@app.route('/create_user', methods=['GET'])
def create_user_page():
    return render_template("create_user.html")

@app.route("/webhook",methods=["POST"])
def webhook():
    try:
        print("Request Data = ", request.data)
        webhook_data = json.loads(request.data)
        binanceManager = BinanceManager()
        if(webhook_data != None and webhook_data.__contains__('email')):
            _tradingHistory = _db.get_active_trades(webhook_data['email'])
            symbols = [d['Symbol'] for d in _tradingHistory]
            if len(_tradingHistory) > 0:
                for trade in _tradingHistory:
                    if webhook_data["Symbol"] in symbols:
                        if (trade['UsedSafetyOrderCount'] < trade['SafetyOrderCount'] and
                                float(webhook_data["Price"]) < float(trade["LastBuyPrice"][-1])):
                            # TODO Buy First Then according to result true then add to db
                            _db.update_trade(webhook_data['email'], webhook_data["Symbol"],
                                             float(webhook_data["Price"]))
                    else:
                        #TODO Buy First Then according to result true then add to db
                        #binanceLastPrice = binanceManager.get_last_price_of_symbol(symbol=webhook_data["Symbol"])
                        _db.add_trade(email=webhook_data['email'], symbol=webhook_data["Symbol"],
                                      price=float(webhook_data["Price"]),
                                      isDealActive=True, safetyOrderCount=3, usedSafetyOrderCount =0, quantity=1, safetyOrderVolume=100)
            else:
                # TODO Buy First Then according to result true then add to db
                # binanceLastPrice = binanceManager.get_last_price_of_symbol(symbol=webhook_data["Symbol"])
                _db.add_trade(email=webhook_data['email'], symbol=webhook_data["Symbol"],
                              price=float(webhook_data["Price"]),
                              isDealActive=True, safetyOrderCount=3, usedSafetyOrderCount=0, quantity=1,
                              safetyOrderVolume=100)

    except Exception as e:
        print("Exception e = ", e.with_traceback())
        return "None"

    return webhook_data

@app.route("/webhook",methods=["GET"])
def webhookGet():
    try:
        if webhook_data != None:
            return webhook_data["ticker"]
        else:
            return "webhook_data is null"
    except Exception as e:
        print(e)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port= 80, debug=True)










'''
# Enter your API Key and Secret here. If you don't have one, you can generate it from the website.
key = "XXXX"
secret = "YYYY"

# python3
secret_bytes = bytes(secret, encoding='utf-8')
# python2
secret_bytes = bytes(secret)

# Generating a timestamp.
timeStamp = int(round(time.time() * 1000))

body = {
  "side": "buy",    #Toggle between 'buy' or 'sell'.
  "order_type": "limit_order", #Toggle between a 'market_order' or 'limit_order'.
  "market": "SNTBTC", #Replace 'SNTBTC' with your desired market pair.
  "price_per_unit": 0.03244, #This parameter is only required for a 'limit_order'
  "total_quantity": 400, #Replace this with the quantity you want
  "timestamp": timeStamp
}

json_body = json.dumps(body, separators = (',', ':'))

signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

url = "https://api.coindcx.com/exchange/v1/orders/create"

headers = {
    'Content-Type': 'application/json',
    'X-AUTH-APIKEY': key,
    'X-AUTH-SIGNATURE': signature
}

response = requests.post(url, data = json_body, headers = headers)
data = response.json()
print(data)
'''