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
    stock_trades_df = pd.DataFrame(AdjustedData.objects.filter(stock__ticker=ticker, time__gte=timezone.now()-timedelta(days=365)).values())
    if len(stock_trades_df) != 0:
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


def trunc_datetime(someDate):
    return someDate.replace(hour=0, minute=0, second=0, microsecond=0)


class GetPortfolioVar(View):
    def get(self, request, portfolio_id):
        last_stock = Stock.objects.all().order_by('last_update_data').first()
        if last_stock.last_update_data is None:
            last_stock_update_date = settings.START_DATA_DATE
        else:
            last_stock_update_date = last_stock.last_update_data + timedelta(days=1)

        #today_datetime = datetime.now()
        start_date = last_stock_update_date - timedelta(days=360)
        base_df = pd.DataFrame()
        date_column = pd.date_range(start_date, last_stock_update_date)
        base_df['time'] = list(map(trunc_datetime,date_column))
        base_df = base_df.astype(
            {'time': 'datetime64[ns]'})
        url = 'http://192.168.10.23:8000/getlastcdsasset/{0}'.format(portfolio_id)
        portfolio = requests.get(url).json()
        data_df = pd.DataFrame(portfolio['data'])
        data_df = data_df[data_df['insMaxLCode']!='-']
        trade_df_dict = {}
        df_historical_portfolio = pd.DataFrame()
        for index, row in data_df.iterrows():
            temp_df = get_stock_trade(row['insMaxLCode'])
            if len(temp_df)!=0:
                temp_df['time'] = list(map(trunc_datetime, temp_df['time']))
                base_df[row['insMaxLCode']] = None
                for index_base, row_base in base_df.iterrows():
                    temp_target = temp_df[temp_df['time']==row_base['time']]
                    if len(temp_target)!= 0:
                        temp_target.reset_index(inplace=True, drop=True)
                        base_df.loc[index_base, row['insMaxLCode']] = temp_target.loc[0, 'vwap_adjusted']*row['quantity']
        base_df = base_df.dropna(subset=base_df.columns[1:], how='all')
        # Dropping columns with more than 50 Nans
        drop_list = []
        drop_weight_sum = 0 # return error if we are dropping more than 30% of the portfolio
        for c in base_df.columns[1:]:
            if base_df[c].isna().sum() >= 50:
                c_weight_df = data_df[data_df['insMaxLCode']==c]
                if len(c_weight_df) > 0:
                    c_weight_df.reset_index(inplace=True, drop=True)
                    drop_weight_sum += c_weight_df.loc[0,'percentage']
                    if drop_weight_sum >= 30:
                        return JsonResponse({'error': 'Dropping more than 30% of the portfolio, the model is not valid anymore!'}, status=500, safe=False)
                drop_list.append(c)
        if len(drop_list) > 0:
            base_df =base_df.drop(columns=drop_list)
        base_df = base_df.dropna(how='any')
        base_df['hist_value'] = 0
        for c in base_df.columns[1:]:
            base_df['hist_value'] += base_df[c]

        base_df['hist_value(-1)'] = base_df['hist_value'].shift(1)
        base_df['raw_returns'] = base_df['hist_value'] / base_df['hist_value(-1)']
        base_df['ln_returns'] = list(map(math.log, base_df['raw_returns']))
        base_df['ln_returns'].dropna(inplace=True)
        portfolio_variance = base_df['ln_returns'].var()
        sigma = math.sqrt(portfolio_variance)
        value_at_risk = base_df.tail(1)['hist_value'] * sigma * 1.645
        return JsonResponse({'value_at_risk': str(round(float(value_at_risk)))}, status=200, safe=False)