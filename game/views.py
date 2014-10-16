# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.datastructures import MultiValueDictKeyError
from django.core import serializers

import random
import string
import json

from game.models import Game, GameLog
from rule.models import Edition
from player.models import Player
from player.decorators import requires_access_token

def _generate_hashkey(size=15):
    c = string.letters + string.digits
    return ''.join(random.sample(c, size))

@csrf_exempt
@requires_access_token()
def create(request):
    response_data = {}

    try:
        hashkey = _generate_hashkey()
        with transaction.atomic():
            while ( Game.objects.get_or_none(hashkey=hashkey) != None ) :
                hashkey = _generate_hashkey()
            g = Game(
                    num_players=request.POST['num_players'],
                    edition=Edition.objects.get(name=request.POST['edition']),
                    hashkey=hashkey,
                )
            g.save()
        response_data['success'] = True
        response_data['game_id'] = g.hashkey
    except (MultiValueDictKeyError, IntegrityError) as e:
        response_data['success'] = False
        response_data['errmsg'] = e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

@requires_access_token()
def list(request):
    response_data = {}
    games = Game.objects.all().filter(
        Q(status__exact=Game.WAITING) | Q(status__exact=Game.IN_PROGRESS))
    response_data['games'] = []
    for g in games:
        response_data['games'].append(g.to_dict())
    response_data['success'] = True
    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")


@csrf_exempt
@requires_access_token()
def delete(request):
    response_data = {}

    try:
        with transaction.atomic():
            g = Game.objects.get(hashkey=request.POST['game_id'])

            if ( g.status == Game.WAITING and g.players.count() == 0 ) :
                g.delete()
                response_data['success'] = True
            else :
                raise Game.UnableToDelete('unable to delete game')

    except (MultiValueDictKeyError, Game.DoesNotExist, Game.UnableToDelete) as e:
        response_data['success'] = False
        response_data['errmsg'] = e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

def _get_user_id_from_post(request):
    return request.POST['user_id']

@csrf_exempt
@requires_access_token(func_get_user_id=_get_user_id_from_post)
def join(request):
    response_data = {}

    try:
        with transaction.atomic():
            g = Game.objects.get(hashkey=request.POST['game_id'])
            p = Player.objects.get(user_id=request.POST['user_id'])

            if ( g.status == Game.WAITING and g.players.count() < g.num_players ) :
                g.players.add(p)
                response_data['success'] = True
            else :
                raise Game.UnableToJoin('unable to join game')

    except (MultiValueDictKeyError, Game.DoesNotExist, Game.UnableToJoin, Player.DoesNotExist) as e:
        response_data['success'] = False
        response_data['errmsg'] = e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

@csrf_exempt
@requires_access_token(func_get_user_id=_get_user_id_from_post)
def quit(request):
    response_data = {}

    try:
        with transaction.atomic():
            g = Game.objects.get(hashkey=request.POST['game_id'])
            p = Player.objects.get(user_id=request.POST['user_id'])

            if ( g.status == Game.WAITING  ) :
                g.players.remove(p)
                response_data['success'] = True
            else :
                raise Game.UnableToQuit('unable to quit game')

    except (MultiValueDictKeyError, Game.DoesNotExist, Game.UnableToQuit, Player.DoesNotExist) as e:
        response_data['success'] = False
        response_data['errmsg'] = e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
