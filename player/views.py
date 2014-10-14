# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.utils.dateparse import parse_datetime

import json
import requests

from player.models import Player, AccessToken
from player.decorators import requires_access_token

# this can raise IntegrityError
def _create_player(user_id, name=None, email=None, auth_provider=Player.IIZS_NET):
    p = Player()
    p.user_id=user_id
    p.name=name
    p.email=email
    p.auth_provider=auth_provider
    p.save()
    return p

def _get_token_info(token, auth_provider=Player.IIZS_NET):
    payloads = { 'token': token }
    r = requests.get("https://iizs.net/auth/tokeninfo", params=payloads, verify=False)
    # TODO add validity check
    if r.status_code != 200:
        raise AccessToken.Invalid( 'AccessToken, \'' + token + '\' not found from iizs.net')
    return r.json()

@csrf_exempt
def create(request):
    response_data = {}
    response_data['request'] = request.POST.copy()

    try:
        p = _create_player( 
            user_id=request.POST.get('user_id', None),
            name=request.POST.get('name', None),
            email=request.POST.get('email', None),
            auth_provider=request.POST.get('auth_provider', Player.IIZS_NET),
        )
        response_data['success'] = True
    except IntegrityError as e:
        response_data['success'] = False
        # TODO DB 오류 메시지가 그대로 노출되므로 좋지 않다. 수정 필요
        response_data['errmsg'] = e.args

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

@requires_access_token
def get(request):
    try:
        response_data = {}

        p = Player.objects.get(user_id=request.GET['user_id'])
        response_data['success'] = True
        response_data['user_id'] = p.user_id
        response_data['name'] = p.name
        response_data['email'] = p.email
    except Player.DoesNotExist:
        response_data['success'] = False
        response_data['errmsg'] = 'Player not found: ' + request.GET['user_id']
    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

def registerToken(request):
    response_data = {}
    try:
        # get token info 
        token_param = request.GET['token']
        token_info = _get_token_info(token_param)

        user_id = token_info['user']['id']
        expires = token_info['expires']

        p = Player.objects.get(user_id=user_id)
        try:
            t = AccessToken.objects.get(player=p)
        except AccessToken.DoesNotExist:
            t = AccessToken()
            t.player = p

        t.token = token_param
        t.expires = parse_datetime(expires)

        # TODO expired token은 등록하지 말까? 
        t.save()

        response_data['success'] = True

    except AccessToken.Invalid as e:
        response_data['success'] = False
        response_data['errmsg'] = e.value
    except Player.DoesNotExist:
        response_data['success'] = False
        response_data['errmsg'] = 'Player not found: ' + request.GET['user_id']

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
