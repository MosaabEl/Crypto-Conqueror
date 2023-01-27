from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from binance.client import Client
from binance.enums import *
import json, pprint, config, csv
import websocket, talib, numpy
from websocket import WebSocketApp

app = Flask(__name__)
app.secret_key = b'secretKeyForFlaskApp'

Symbol = 'ethbtc'
buySymbol = ''
SOCKET = "wss://stream.binance.com:9443/ws/ethbtc@kline_15m"

client = Client(config.API_KEY, config.API_SECRET, tld='com')
closes = []
closes1 = []

in_position = False
timePERIOD = 14
OVERBOUGHT = 70
OVERSOLD = 30
assetQUANTITY = 0.4

@app.route('/', methods = ['POST', 'GET'])
def login():
    errorMsg = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            errorMsg = 'Incorrect username or password, please try again.'
        else:
            errorMsg = None
            return redirect(url_for('home'))
    return render_template('login.html', errorMsg=errorMsg)

@app.route('/home', methods=['POST', 'GET'])
def home():
    title = 'Crypto Conqueror'
    account = client.get_account()
    balanceData = account['balances']
    balances = []

    for balance in balanceData:
        if balance['free'] != '0.00000000' and balance['free'] != '0.00':
            balances.append(balance)
    
    

    exchange_info = client.get_exchange_info()
    symbols = exchange_info['symbols']

    return render_template('index.html', title = title, my_balances = balances, symbols=symbols)

@app.route('/graphSelect', methods=["GET", "POST"])
def graphSelect():
    global Symbol
    Symbol = (request.form['symbol']).upper()
    
    return redirect('/home')
    

@app.route('/activate', methods=["GET", "POST"])
def activate():
    global timePERIOD, OVERBOUGHT, OVERSOLD, assetQUANTITY, buySymbol
    error=None
    try:
        buySymbol = str.strip((request.form['buyTXT']).lower())
        timePERIOD = int(request.form['rsiLen'])
        OVERBOUGHT = int(request.form['rsiOverbought'])
        OVERSOLD = int(request.form['rsiOversold'])
        assetQUANTITY = float(request.form['quantity'])
    except:
        error = 'ERROR: Incorrect Settings input has been entered, Please try again:'
    SOCKET = "wss://stream.binance.com:9443/ws/"+ buySymbol +"@kline_1m"
    
    
    try:
        analysis = request.form['radio']
    except:
        analysis = 'error'
    if analysis == 'RSI':
        
            ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
            ws.run_forever()
            if ws == None:
                error = 'Invalid Currency pair was inputted, Please try again.'
    elif analysis == 'ROC':
       
            ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message1)
            ws.run_forever()
            if ws == None:
                error = 'Invalid Currency pair was inputted, Please try again.'
    else:
        error = 'Select technical analysis method: RSI or ROC'
    

    title = 'Crypto Conqueror'
    account = client.get_account()
    balanceData = account['balances']
    balances = []

    for balance in balanceData:
        if balance['free'] != '0.00000000' and balance['free'] != '0.00':
            balances.append(balance)
    
    

    exchange_info = client.get_exchange_info()
    symbols = exchange_info['symbols']


    return render_template('index.html', error = error, title = title, my_balances = balances, symbols=symbols)

@app.route('/order', methods=['POST', 'GET'])
def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    global buySymbol
    try:
        order = client.create_order(symbol = buySymbol, 
        side=side,
        type=order_type,
        quantity=assetQUANTITY)
        print(order)
        flash('Successful Purchase.')
    except Exception as e:
        errorMSG = 'ERROR: ' + str(e)
        flash(errorMSG)
        
        return False
    
    return True
@app.route('/history')
def history():
    global Symbol
    
    candlesticks = client.get_historical_klines(Symbol, Client.KLINE_INTERVAL_15MINUTE, "26 April, 2021")
    processed_candlesticks = []
    for data in candlesticks:
        candlestick = { 
            "time": data[0] / 1000,
            "open": data[1],
            "high": data[2],
            "low": data[3], 
            "close": data[4] }
        processed_candlesticks.append(candlestick)
          
    return jsonify(processed_candlesticks)


@app.route('/history1')
def history1():
    global Symbol
    
    volumeData = client.get_historical_klines(Symbol, Client.KLINE_INTERVAL_15MINUTE, "26 April, 2021")
    processed_volume = []
    
    for data in volumeData:
        volume = {
            'time': data[0]/1000,
            'value': data[5],
        }
        processed_volume.append(volume)
    return jsonify(processed_volume)
@app.route('/updateCandle')
def updateCandle():
    global Symbol
    newSym = Symbol.lower()
    return jsonify(newSym)
@app.route('/')
def on_open(ws):
    print('opened')
@app.route('/')
def on_close(ws):
    print('close')
@app.route('/')
def on_message(ws, message):
    global closes, in_position, timePERIOD, OVERBOUGHT, OVERSOLD, assetQUANTITY, buySymbol

   

    #print('received')
    json_message = json.loads(message)
    #print(json_mesßsage)

    candle = json_message['k']
    is_candle_closed = candle['x'] 
    close = candle['c']

    if is_candle_closed:
        print("Candle closed at: : {}".format(close))
        closes.append(float(close))
        print('Number of closing candles:')
        print(len(closes))
        print('Chosen RSI Period:')
        print(timePERIOD)

        if len(closes) > timePERIOD:
           
            np_closes = numpy.array(closes)
          
            rsi = talib.RSI(np_closes, timePERIOD)
            print("RSI's calculated so far:")
            print(rsi)
            last_rsi = rsi[-1]
            print(last_rsi)
            
            print("Latest RSI: {}".format(last_rsi))

            if last_rsi > OVERBOUGHT: 
                if in_position: #Tests RSI against oversold threshold, if in a trade then a sell order will be made
                    print('Attempted sell: Asset is overbought')
                    order_succeeded = order(SIDE_SELL, assetQUANTITY, buySymbol)
                    if order_succeeded:
                        print('Selling Asset')
                        in_position = False
                else:
                    print('Not ready to sell')
            if last_rsi < OVERSOLD:
                if in_position: #Tests RSI against oversold threshold, if NOT in a trade then a sell order will be made
                    print('Not ready to buy')
                else:
                    print('Attempted purchase: Asset is oversold')
                    order_succeeded = order(SIDE_BUY, assetQUANTITY, buySymbol)
                    if order_succeeded:
                        print('Buying Asset')
                        in_position = True

@app.route('/')
def on_message1(ws, message):
    global closes1, in_position, timePERIOD, OVERBOUGHT, OVERSOLD, assetQUANTITY, buySymbol

   
    OVERBOUGHT = OVERBOUGHT/100
    OVERSOLD = OVERSOLD/100
    #print('received')
    json_message = json.loads(message)
    #print(json_mesßsage)

    candle = json_message['k']
    is_candle_closed = candle['x'] 
    close = candle['c']

    if is_candle_closed:
        print("Candle closed at: : {}".format(close))
        closes1.append(float(close))
        print('Number of closing candles:')
        print(len(closes1))
        print('Chosen time Period:')
        print(timePERIOD)

        if len(closes1) > timePERIOD:
           
            np_closes = numpy.array(closes1)
          
            roc = talib.ROC(np_closes, timePERIOD)
            print("ROC's calculated so far:")
            print(roc)
            last_roc = roc[-1]
            print(last_roc)
            
            print("Latest ROC: {}".format(last_roc))

            if last_roc > OVERBOUGHT: 
                if in_position: #Tests RSI against oversold threshold, if in a trade then a sell order will be made
                    print('Attempted sell: Asset is overbought')
                    order_succeeded = order(SIDE_SELL, assetQUANTITY, buySymbol)
                    if order_succeeded:
                        print('Selling Asset')
                        in_position = False
                else:
                    print('Not ready to sell')
            if last_roc < OVERSOLD:
                if in_position: #Tests RSI against oversold threshold, if NOT in a trade then a sell order will be made
                    print('Not ready to buy')
                else:
                    print('Attempted purchase: Asset is oversold')
                    order_succeeded = order(SIDE_BUY, assetQUANTITY, buySymbol)
                    if order_succeeded:
                        print('Buying Asset')
                        in_position = True