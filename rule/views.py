from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers

import json
from rule.models import Edition, Commodity, Province, Water

def getMap(request):
    param_edition = request.GET.get('edition', 'none')

    edition = Edition.objects.filter(name__exact=param_edition)
    provinces = Province.objects.filter(edition__exact=edition)
    waters = Water.objects.filter(edition__exact=edition)

    response_data = {}
    response_data['edition'] = json.loads(serializers.serialize("json", edition))
    response_data['provinces'] = json.loads(serializers.serialize("json", provinces))
    response_data['waters'] = json.loads(serializers.serialize("json", waters))
    return HttpResponse(json.dumps(response_data, indent=None), content_type="application/json")

