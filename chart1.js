
/*The assetPair variable below will determine the live data for the asset entered on the app, MUST be lower case and synced with the asset that was submitted and chosen on the app. */

//var assetPair = 'ethusdt';

//var formElements=document.getElementById("myForm").elements;    
//var postData={};
//for (var i=0; i<formElements.length; i++)
//	if (formElements[i].type!="submit")//we dont want to include the submit-buttom
//		postData[formElements[i].name]=formElements[i].value;
//var assetPair = String(postData.symbol.toLowerCase());


var chart = LightweightCharts.createChart(document.getElementById('chart'), {
	width: 1058,
  height: 450,

  
	layout: {
		backgroundColor: '#253248',
		textColor: 'white',
	
	},
	grid: {
		vertLines: {
			color: '#A8A8A8',
		},
		horzLines: {
			color: '#A8A8A8',
		},
	},
	crosshair: {
		mode: LightweightCharts.CrosshairMode.Normal,
		vertLine: {
			color: '#30D5C8'
		},
		horzLine: {
			color: '#30D5C8'
		}
	},
	
	rightPriceScale: {
		borderColor:'#A8A8A8'
	},
	timeScale: {
		borderColor:'#A8A8A8'
	},
});

var candleSeries = chart.addCandlestickSeries({
  upColor: 'green',
  downColor: 'red',
  borderDownColor: '#A8A8A8',
  borderUpColor: '#A8A8A8',
  wickDownColor: '#A8A8A8',
  wickUpColor: '#A8A8A8',
});
var volumeSeries = chart.addHistogramSeries({
    color: '#182233',
    lineWidth: 1,
    priceFormat: {
        type: 'volume',
    },
    overlay: true,
  scaleMargins: {
      top: 0.92,
    bottom: 0, },
}); 

	//The fetch code below would enable live charts for the asset chosen in bot.py
	fetch('http://localhost:5000/history') 
	.then((r) => r.json())
	.then((response) => {
		console.log(response)
		candleSeries.setData(response);
	
	}) 
	fetch('http://localhost:5000/history1') 
	.then((r) => r.json())
	.then((response) => {
		console.log(response)
		volumeSeries.setData(response);
	}) 
	
	fetch('http://localhost:5000/updateCandle') 
	.then((r) => r.json())
	.then((response) => {
		console.log(response)
		assetPair = response;

		binanceSocket = new WebSocket('wss://stream.binance.com:9443/ws/'+assetPair+'@kline_15m');
		console.log("wss://stream.binance.com:9443/ws/"+assetPair+"@kline_15m")
		binanceSocket.onmessage = function (event) 
	{ 	

		var message = JSON.parse(event.data);
		var candlestick = message.k;
		candleSeries.update({
			time: candlestick.t + 1,
			open: candlestick.o + 1,
			high: candlestick.j + 1,
			low: candlestick.l + 1,		
			close: candlestick.c + 1
		})
		volumeSeries.update({
			time: candlestick.t + 1,
			volume: candlestick.v + 1})

	}})
	 
	

	



    
