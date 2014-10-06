from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers

from rule.models import Edition, Commodity, Province, Water

import json

def getMap(request):
    param_edition = request.GET.get('edition', 'none')

    edition = Edition.objects.filter(name__exact=param_edition)
    provinces = Province.objects.filter(edition__exact=edition)#.filter(area__exact='1')
    waters = Water.objects.filter(edition__exact=edition)#.filter(area__exact='1')

    response_data = {}
    response_data['edition'] = json.loads(serializers.serialize("json", edition))
    response_data['provinces'] = json.loads(serializers.serialize("json", provinces))
    response_data['waters'] = json.loads(serializers.serialize("json", waters))
    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

