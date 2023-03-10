from django.shortcuts import render
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def home(request):
    if request.method == 'POST':
        # Get form data
        crypto = request.POST.get('crypto')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Fetch data from Yahoo Finance
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        stock_data = yf.download(crypto, start=start_date, end=end_date)


        # Compute RSI
        period = 7
        delta = stock_data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        average_gain = gain.rolling(window=period).mean()
        average_loss = loss.rolling(window=period).mean()
        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))

        # Add RSI to stock_data DataFrame
        stock_data['rsi'] = rsi

        # Define a function to calculate the accuracy of RSI for trading
        def rsi_accuracy(df, rsi_column):
            # Calculate daily returns
            df['return'] = np.log(df['Close'] / df['Close'].shift(1))
            # Create a new column to hold the signal
            df['signal'] = np.nan
            # Create a threshold for the RSI
            upper_threshold = 70
            lower_threshold = 30
            # Generate the signal
            df.loc[df[rsi_column] > upper_threshold, 'signal'] = -1 # overbought, sell signal
            df.loc[df[rsi_column] < lower_threshold, 'signal'] = 1 # oversold, buy signal
            # Forward fill the signal column to simulate holding the position
            df['signal'].fillna(method='ffill', inplace=True)
            # Compute daily returns when the signal is active
            df['strategy_return'] = df['return'] * df['signal']
            # Compute accuracy
            accuracy = len(df[df['strategy_return'] > 0]) / len(df[df['signal'] != 0])
            return accuracy

        # Compute the accuracy of RSI
        accuracy = rsi_accuracy(stock_data, 'rsi')
       # print('Accuracy of RSI for trading: {:.2f}%'.format(accuracy*100))
        return render(request, 'rsi.html', {
            'crypto': crypto,
            'start_date': start_date,
            'end_date': end_date,
            'accuracy': accuracy,
        })
    return render(request, 'rsi.html')

