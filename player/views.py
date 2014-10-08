# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError

import json

from player.models import Player

@csrf_exempt
def create(request):
    response_data = {}
    response_data['request'] = request.POST.copy()

    try:
        p = Player()
        p.user_id=request.POST.get('user_id', None)
        p.name=request.POST.get('name', None)
        p.email=request.POST.get('email', None)
        p.save()
        response_data['success'] = True
    except IntegrityError as e:
        response_data['success'] = False
        # TODO DB 오류 메시지가 그대로 노출되므로 좋지 않다. 수정 필요
        response_data['errmsg'] = e.args

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
