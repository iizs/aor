from django.contrib import admin
from django.forms import SelectMultiple
from django.db import models

from rule.models import Edition, Commodity, Province, Water

class CommodityAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'short_name', 'unit_price')

class ProvinceAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 
        'area', 
        'short_name', 
        'province_type', 
        'market_size', 
        'get_all_commodities', 
        'get_all_connected', 
        'get_all_supports', 
        'edition', 
    )

    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'10'}) },
    }

admin.site.register(Edition)
admin.site.register(Commodity, CommodityAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(Water)
