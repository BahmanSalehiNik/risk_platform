from django.shortcuts import render
from django.views import View
from django.conf import settings
from .pouya_services import *
from .models import Stock, AdjustedData
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import json
import pandas as pd
import numpy as np
import math

class DailyUpdateQuotes(View):
    def post(self, request):

        last_stock = Stock.objects.all().order_by('last_update_data').first()
        if last_stock.last_update_data is None:
            last_stock_update_date = settings.START_DATA_DATE
        else:
            last_stock_update_date = last_stock.last_update_data + timedelta(days=1)

        today_datetime = datetime.now()
        data = quotes(start_date=last_stock_update_date.strftime('%Y%m%d')
                                     ,end_date=today_datetime.strftime('%Y%m%d'))

        for item in data:
            current_stock = Stock.objects.get(ticker=item['ticker'])
            days = item['items'][0]['days']
            last_current_stock_data = AdjustedData.objects.filter(stock=current_stock).order_by('-time')
            if last_current_stock_data.exists():
                stock_start_date = last_current_stock_data[0].time
            else:
                stock_start_date = settings.START_DATA_DATE

            for day_data in days:
                fields = day_data['items'][0]['values']
                day_time = datetime.strptime(day_data['time'], '%Y-%m-%d %H:%M:%S')
                if day_time.date() > stock_start_date.date():
                    try:
                        AdjustedData.objects.create(day=str(day_data['day']), state=day_data['state'],
                                                              time=day_time,
                                                              open_adjusted=fields['openAdjusted'], high_adjusted=fields['highAdjusted'],
                                                              low_adjusted=fields['lowAdjusted'], close_adjusted=fields['closeAdjusted'],
                                                              vwap_adjusted=fields['vwapAdjusted'], vwap_adjusted_previous=fields['vwapAdjustedPrevious'],
                                                              volume=fields['volume'], value=fields['value'], num_of_trades=fields['numOfTrades'],
                                                              adj_coef=fields["adjCoef"], stock=current_stock)
                        Stock.objects.filter(ticker=item['ticker']).update(last_update_data=datetime.now())
                    except:
                        print("Error in Create Model")

        return JsonResponse(data={}, safe=True)


class GetAllStocks(View):
    def post(self, request):
        stocks = get_all_stocks()
        for item in stocks:
            if item['company'] is None:
                item['company'] = {'type': None, 'key': None}
            try:
                Stock.objects.create(ticker=item['ticker'], symbol=item['symbol'],name=item['name'],
                                        symbol_fa=item['symbolFA'], name_fa=item['nameFA'],
                                        industry_index=item['industryIndex'], exchange=item['exchange'],
                                        type_code=item['type']['code'], company_key=item['company']['key'],
                                        company_type=item['company']['type'], status=item['status'], board=item['board'],
                                        market=item['market'], company_code=item['companyCode'],
                                        industry_tse=item['industry']['tse'],
                                        industry_bourseview=item['industry']['bourseview'])
            except:
                print("Problem in Save Data")

        return JsonResponse(data={}, safe=True)

def nan_binary_func(x):
    if math.isnan(x):
        return 1
    else:
        return 0

def get_stock_trade(ticker):
    stock_trades_df = pd.DataFrame(AdjustedData.objects.filter(stock__ticker=ticker).values())
    stock_trades_df = stock_trades_df.astype(
        {'time': 'datetime64[ns]'})
    stock_trades_df['nan_binary'] = None
    stock_trades_df['nan_ahead'] = 0
    stock_trades_df['nan_binary'] = list(map(nan_binary_func, stock_trades_df['close_adjusted']))
    stock_trades_df.sort_values(by=['time'], ascending=True, inplace=True)
    stock_trades_df.reset_index(drop=True, inplace=True)
    for index, row in stock_trades_df.iterrows():
        if index == 0:
            stock_trades_df.loc[index, 'nan_ahead'] = row['nan_binary']
        else:
            stock_trades_df.loc[index, 'nan_ahead'] = (stock_trades_df.loc[index - 1, 'nan_ahead'] + row[
                'nan_binary']) * row['nan_binary']

    stock_trades_df.sort_values(by=['time'], ascending=False, inplace=True)
    stock_trades_df.reset_index(drop=True, inplace=True)

    for index, row in stock_trades_df.iterrows():
        if row['nan_ahead']!=0 and index != 0:
            stock_trades_df.loc[index,'vwap_adjusted'] = stock_trades_df.loc[index-1,'vwap_adjusted'] + (stock_trades_df.loc[(int(index) + int(row['nan_ahead'])), 'vwap_adjusted'] - stock_trades_df.loc[index-1,'vwap_adjusted']) / row['nan_ahead']
    return stock_trades_df


class GetStockTrade(View):
    def get(self, request, ticker):
        df_ticker_trades = get_stock_trade(ticker)
        return JsonResponse({'test':'ok'}, status=200, safe=False)