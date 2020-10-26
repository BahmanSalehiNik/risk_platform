from django.contrib import admin
from .models import Stock, AdjustedData

admin.site.register(Stock)
admin.site.register(AdjustedData)
