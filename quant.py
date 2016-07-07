
from krakenex.connection import Connection
from krakenex.api import API
import datetime
import time 
import csv
import numpy
import sys, os
sys.path.append(os.path.join(os.getcwd(), "site-packages"))
import numpy as np

currency = 'XETHZUSD'
k = API('jzJfKeoARa/Vo5x3tgvOvl1WXYMhemsn6Nyzq5/resmCOyBhwU3ag514', '6Mr/qy2anpTZHwgx/C+vK+jhFJkG4PgZFC1Y95awMhb15y2EQAj+tjiV/WKhEpZsVNmV8z3VrU1ujQsTLkQ9Gg==')
#possible intervals:  1, 5, 15, 30, 60, 240, 1440, 10080, 21600
history = k.query_public('OHLC', {'pair': currency,'interval': 60})

data2 = []

with open('eggs.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=',')
	spamwriter.writerow(['Date Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'])
	for time in history['result'][currency]:
		if datetime.datetime.fromtimestamp(time[0]).strftime('%Y-%m-%d %H:%M:%S') == '2016-02-29 01:00:00' and float(time[2]) == 7.6:
			continue
		data2.append([datetime.datetime.fromtimestamp(time[0]).strftime('%Y-%m-%d %H:%M:%S'), float(time[1]), float(time[4])])
		spamwriter.writerow([data2[-1][0], float(time[1]), float(time[2]), float(time[3]), float(time[4]), float(time[6]), float(time[4])])

import pyalgotrade
from pyalgotrade import strategy
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi
from pyalgotrade.technical import macd
from pyalgotrade.technical import stoch

from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import returns
import matplotlib.pyplot as plt

class Currency(strategy.BacktestingStrategy):

    def __init__(self, feed, instrument, smaPeriod, rsi_thr, j = 2, k = 3):
        strategy.BacktestingStrategy.__init__(self, feed, 10000)
        self.__position = None
        self.__instrument = instrument
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        
       	self.__ema = ma.EMA(feed[instrument].getPriceDataSeries(), smaPeriod)
       	self.__stoch = stoch.StochasticOscillator(feed.getDataSeries(), smaPeriod)
       	self.__sma = ma.SMA(feed[instrument].getPriceDataSeries(), smaPeriod)
        #self.__sma = ma.WMA(feed[instrument].getPriceDataSeries(), smaPeriod)
        #self.__sma = ma.VWAP(feed[instrument].getPriceDataSeries(), smaPeriod)
        self.__rsi = rsi.RSI(self.__sma, smaPeriod)
        self.__macd = macd.MACD(feed[instrument].getPriceDataSeries(), j, k, smaPeriod)
 		
        self.__rsith = rsi_thr
        self.__higher = False

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        #self.info("BUY at $%.2f" % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        #self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate a SMA.
        if self.__sma[-1] is None:
            return
        bar = bars[self.__instrument]
        # If a position was not opened, check if we should enter a long position.
        self.__rsi_e = self.__rsi
        self.__sma_e = self.__rsi
        if self.__position is None:
        	# for MACD(t-1)<Signal(t-1)} und MACD(t)>Signal(t)
        	# for sma and rsi -> 8 Dollars per eth 
            if self.__rsi[-1] > self.__rsi[-2]:
            #if self.__rsi[-1] > self.__rsi[-2]:
                self.__position = self.enterLong(self.__instrument, 1, True)
        # Check if we have to exit the position.
        #self.__sma[-1]< bar.getClose()
        elif self.__rsi[-1] < self.__rsi[-2] and not self.__position.exitActive():
        	self.__position.exitMarket()

    def getSMA(self):
    	return self.__sma

    def getRSI(self):
    	return self.__rsi

    def getMACD(self):
    	return self.__macd

    def getstoch(self):
    	return self.__stoch

def run_strategy(smaPeriod, rsi_thr, j = 24, k = 48):
    # Load the yahoo feed from the CSV file	
    feed = csvfeed.GenericBarFeed(pyalgotrade.bar.Frequency.HOUR)
    feed.addBarsFromCSV("eggs", "eggs.csv")
    # Evaluate the strategy with the feed.
    myStrategy = Currency(feed, "eggs", smaPeriod, rsi_thr, j, k)
    # Attach a returns analyzers to the strategy.
    
    returnsAnalyzer = returns.Returns()
    myStrategy.attachAnalyzer(returnsAnalyzer)
    plt = plotter.StrategyPlotter(myStrategy)
    #plt.getInstrumentSubplot("eggs").addDataSeries("EMA", myStrategy.getEMA())
    #plt.getInstrumentSubplot("eggs").addDataSeries("SMA", myStrategy.getSMA())
    #plt.getInstrumentSubplot("eggs").addDataSeries("Macd", myStrategy.getMACD())

    plt.getOrCreateSubplot("RSI").addDataSeries("RSI", myStrategy.getRSI())
    plt.getOrCreateSubplot("MACD").addDataSeries("Macd", myStrategy.getMACD())
    plt.getOrCreateSubplot("Stoch").addDataSeries("Stoch", myStrategy.getSMA())
    myStrategy.run()
    myStrategy.info("Final portfolio value: $%.2f" % myStrategy.getResult())
    plt.plot()
    #print myStrategy.getSMA()[:]
    print len(myStrategy.getRSI()[:])
    print myStrategy.getRSI()[-10:]
    return myStrategy.getResult()

results = []
run_strategy(22, [])
"""
for i in range(5, 60):
	results.append(run_strategy(i, []) - 10000)

plt.plot(range(5, 60), results)
plt.ylabel('results')
plt.show()"""

