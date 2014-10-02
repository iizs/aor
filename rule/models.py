from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

class Edition(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name

class Commodity(models.Model):
    short_name = models.CharField(max_length=2)
    full_name = models.CharField(max_length=10)
    unit_price = models.SmallIntegerField()

    def __unicode__(self):
        return self.full_name

class Province(models.Model):
    CAPITAL     = 'C'
    PROVINCE    = 'P'
    SATELLITE   = 'S'
    PROVINCE_TYPE = (
        (CAPITAL, 'Capital'),
        (PROVINCE, 'Province'),
        (SATELLITE, 'Satellite'),
    )

    AREA_I          = '1'
    AREA_II         = '2'
    AREA_III        = '3'
    AREA_IV         = '4'
    AREA_V          = '5'
    AREA_VI         = '6'
    AREA_VII        = '7'
    AREA_VIII       = '8'
    AREA_FAR_EAST   = 'F'
    AREA_NEW_WROLD  = 'N'
    AREA_ND         = 'X'
    AREA = (
        (AREA_I, 'I'),
        (AREA_II, 'II'),
        (AREA_III, 'III'),
        (AREA_IV, 'IV'),
        (AREA_V, 'V'),
        (AREA_VI, 'VI'),
        (AREA_VII, 'VII'),
        (AREA_VIII, 'VIII'),
        (AREA_FAR_EAST, 'Far East'),
        (AREA_NEW_WROLD, 'New World'),
        (AREA_ND, 'Not Defined'),
    )

    edition = models.ForeignKey('Edition')
    area = models.CharField(max_length=1, choices=AREA)
    full_name = models.CharField(max_length=20)
    short_name = models.CharField(max_length=10)
    province_type = models.CharField(max_length=1, choices=PROVINCE_TYPE, verbose_name = 'Type')
    market_size = models.SmallIntegerField()
    commodities = models.ManyToManyField('Commodity', null=True, blank=True)
    supports = models.ManyToManyField('self', null=True, blank=True)
    connected = models.ManyToManyField('self', null=True, blank=True)

    def __unicode__(self):
        return self.full_name

    # for list_display() in admin page
    def get_all_commodities(self):
        return ', '.join([c.full_name for c in self.commodities.all()])
    get_all_commodities.short_description = 'Commodities'

    # for list_display() in admin page
    def get_all_supports(self):
        return ', '.join([p.full_name for p in self.supports.all()])
    get_all_supports.short_description = 'Supports'

    # for list_display() in admin page
    def get_all_connected(self):
        return ', '.join([p.full_name for p in self.connected.all()])
    get_all_connected.short_description = 'Connected'

    # for validation in admin page
    def clean(self):
        if self.market_size <= 0 :
            raise ValidationError( _('Market size must be a positive integer.') )

        if self.province_type == Province.SATELLITE and self.market_size != 1 :
            raise ValidationError( 
                _('Market size of \'%(p_type)s\' must be 1.'), 
                params = { 'p_type' : self.get_province_type_display() } 
            )

        if self.province_type != Province.SATELLITE and self.market_size == 1 :
            raise ValidationError( 
                _('Market size of \'%(p_type)s\' must be larger than 1'), 
                params = { 'p_type' : self.get_province_type_display() } 
            )

    class Meta:
        unique_together = (
            ("edition", "full_name"),
            ("edition", "short_name"),
        )

class Water(models.Model):
    COAST = 'C'
    SEA   = 'S'
    WATER_TYPE = (
        (COAST, 'Coast'),
        (SEA, 'Sea'),
    )

    edition = models.ForeignKey('Edition')
    full_name = models.CharField(max_length=20)
    short_name = models.CharField(max_length=10)
    water_type =  models.CharField(max_length=1, choices=WATER_TYPE)
    coast_of = models.ForeignKey('Province', null=True)
    connected = models.ManyToManyField('self', null=True)
    
