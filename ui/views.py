from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext

def showMap(request):
    return render(request, 'ui/map.html', context_instance=RequestContext(request))
