from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone



class Stock(models.Model):
    ticker = models.CharField(max_length=20, unique=True)
    symbol = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    symbol_fa = models.CharField(max_length=30)
    name_fa = models.CharField(max_length=30)
    industry_index = models.CharField(max_length=50, null=True)
    exchange = models.CharField(max_length=30)
    type_code = models.IntegerField()
    company_key = models.IntegerField(null=True)
    company_type = models.CharField(max_length=30, null=True)
    status = models.CharField(max_length=30)
    board = models.IntegerField(null=True)
    market = models.IntegerField(null=True)
    company_code = models.CharField(max_length=30, null=True)
    #indicators_list = models.CharField(max_length=30, blank=True, null=True)
    industry_tse = models.IntegerField()
    industry_bourseview = models.IntegerField()
    last_update_data = models.DateTimeField(null=True)
    indicators_lastupdate = models.DateTimeField(null=True, default=timezone.now()-timedelta(days=2*365))

    def __str__(self):
        return self.symbol_fa


class AdjustedData(models.Model):
    day = models.CharField(max_length=10)
    state = models.CharField(max_length=4)
    time = models.DateTimeField(max_length=30)
    open_adjusted = models.IntegerField(null=True)
    high_adjusted = models.IntegerField(null=True)
    low_adjusted = models.IntegerField(null=True)
    close_adjusted = models.IntegerField(null=True)
    vwap_adjusted = models.IntegerField(null=True)
    vwap_adjusted_previous = models.IntegerField(null=True)
    volume = models.BigIntegerField()
    value = models.BigIntegerField()
    num_of_trades = models.IntegerField()
    adj_coef = models.FloatField()
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    def __str__(self):
        return self.time.strftime("%Y-%m-%d %H:%M:%S") + ' ' + self.stock.symbol_fa

