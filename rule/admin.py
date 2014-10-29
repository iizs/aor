from django.contrib import admin
from django.forms import SelectMultiple
from django.db import models

from rule.models import Edition, Commodity, Province, Water, Advance, HistoryCard, EventCard, LeaderCard, CommodityCard

class CommodityAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'short_name', 'unit_price', 'dice_roll')

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

class WaterAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 
        'area', 
        'short_name', 
        'water_type', 
        'get_all_connected', 
        'edition', 
    )

    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'10'}) },
    }

class AdvanceAdmin(admin.ModelAdmin):
    list_display = (
        'short_name', 
        'full_name', 
        'category', 
        'points', 
        'credits', 
        'get_all_prerequisites', 
        'edition', 
    )

    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'10'}) },
    }

class EventCardAdmin(admin.ModelAdmin):
    fieldsets = [
        ('None',    {'fields': [
                        'edition', 
                        'short_name', 
                        'full_name', 
                        'epoch', 
                        'recycles', 
                        'shuffle_later', 
                        'description'
                    ]}
        ),
    ]
    list_display = (
        'full_name', 
        'short_name', 
        'epoch', 
        'recycles', 
        'shuffle_later', 
        'edition', 
    )

class LeaderCardAdmin(admin.ModelAdmin):
    fieldsets = [
        ('None',    {   'fields': [
                            'edition', 
                            'short_name', 
                            'full_name', 
                            'epoch', 
                            'recycles', 
                            'shuffle_later', 
                            'discount',
                            'advances'
                        ]
                    }),
         ('None',    {   'fields': [
                            'event', 
                            'discount_on_event', 
                            'discount_after_event', 
                            'discount_during_event' 
                        ],
                        'classes': [ 'collapse' ],
                    }
        ),
    ]
    list_display = (
        'full_name', 
        'short_name', 
        'epoch', 
        'discount',
        'get_all_advances',
        'shuffle_later', 
        'recycles', 
        'edition', 
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'10'}) },
    }

class CommodityCardAdmin(admin.ModelAdmin):
    fieldsets = [
        ('None',    {'fields': [
                        'edition', 
                        'short_name', 
                        'full_name', 
                        'epoch', 
                        'recycles', 
                        'shuffle_later', 
                        'commodities'
                    ]}
        ),
    ]
    list_display = (
        'full_name', 
        'short_name', 
        'epoch', 
        'get_all_commodities',
        'shuffle_later', 
        'recycles', 
        'edition', 
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'10'}) },
    }


admin.site.register(Edition)
admin.site.register(Commodity, CommodityAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(Water, WaterAdmin)
#admin.site.register(HistoryCard)
admin.site.register(EventCard, EventCardAdmin)
admin.site.register(LeaderCard, LeaderCardAdmin)
admin.site.register(CommodityCard, CommodityCardAdmin)
admin.site.register(Advance, AdvanceAdmin)
