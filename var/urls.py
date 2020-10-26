from django.urls import path
from . import views
from var.views import DailyUpdateQuotes, GetAllStocks, GetStockTrade

urlpatterns = [
    path('updater', DailyUpdateQuotes.as_view(), name='updater'),
    path('stocks', GetAllStocks.as_view(), name='stocks'),
    path('stocktrade/<str:ticker>', GetStockTrade.as_view(), name='stocktrade'),
]