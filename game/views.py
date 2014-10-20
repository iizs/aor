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
import datetime

from game.models import Game, GameLog, GameInfo, HouseInfo, HouseTurnLog, HouseBiddingLog, GameInfoEncoder, GameInfoDecoder, Action
from rule.models import Edition
from player.models import Player
from player.decorators import requires_access_token
from game.tasks import process_action

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
        response_data['errmsg'] = type(e).__name__ + ": " + e.message

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
        response_data['errmsg'] = type(e).__name__ + ": " + e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

def _get_user_id_from_post(request):
    return request.POST.get('user_id', None)

def _get_user_id_from_get(request):
    return request.GET.get('user_id', None)

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
        response_data['errmsg'] = type(e).__name__ + ": " + e.message

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
        response_data['errmsg'] = type(e).__name__ + ": " + e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

@csrf_exempt
@requires_access_token(func_get_user_id=_get_user_id_from_post)
def start(request):
    response_data = {}

    try:
        with transaction.atomic():
            g = Game.objects.get(hashkey=request.POST['game_id'])
            p = Player.objects.get(user_id=request.POST['user_id'])

            if ( ( g.status == Game.WAITING ) 
                and g.players.filter(user_id=request.POST['user_id']).exists() 
                and len(g.players.all()) == g.num_players ):
                g.status = Game.IN_PROGRESS
                g.date_started = datetime.datetime.now()
                info = GameInfo(g)
                g.initial_info = json.dumps(info, cls=GameInfoEncoder)
                g.current_info = g.initial_info
                g.last_lsn += 1
                a = GameLog(
                        game=g,
                        player=None,
                        lsn=g.last_lsn,
                    )
                a.set_log(log_dict={ 'action': Action.DEAL_CARDS })
                g.save()
                a.save()
                process_action.delay(g.hashkey, a.lsn)
                response_data['success'] = True
            else :
                raise Game.UnableToStart('unable to start game')

    except (MultiValueDictKeyError, Game.DoesNotExist, Player.DoesNotExist, Game.UnableToStart) as e:
        response_data['success'] = False
        response_data['errmsg'] = type(e).__name__ + ": " + e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

@requires_access_token(func_get_user_id=_get_user_id_from_get)
def get_info(request):
    response_data = {}

    try:
        with transaction.atomic():
            g = Game.objects.get(hashkey=request.GET['game_id'])
            response_data['info'] = json.loads(g.current_info, cls=GameInfoDecoder)
            response_data['last_lsn'] = g.last_lsn

    except (MultiValueDictKeyError, Game.DoesNotExist) as e:
        response_data['success'] = False
        response_data['errmsg'] = type(e).__name__ + ": " + e.message
    return HttpResponse(json.dumps(response_data, cls=GameInfoEncoder, indent=2), content_type="application/json")
        

# can raise (KeyError, ValueError):
def _get_user_id_from_action(request):
    body = json.loads(request.body)
    return body['user_id'] if 'user_id' in body else None

@csrf_exempt
@requires_access_token(func_get_user_id=_get_user_id_from_action)
def action(request):
    response_data = {}

    try:
        body = json.loads(request.body)

        with transaction.atomic():
            g = Game.objects.get(hashkey=body['game_id'])
            p = Player.objects.get(user_id=body['user_id'])
            action = body['action']
            if ( ( g.status == Game.IN_PROGRESS ) 
                and g.players.filter(user_id=body['user_id']).exists() ):
                g.last_lsn += 1
                a = GameLog(
                        game=g,
                        player=p,
                        lsn=g.last_lsn,
                        log=action,
                    )
                g.save()
                a.save()
                process_action.delay(g.hashkey, a.lsn)
                response_data['success'] = True
                response_data['lsn'] = a.lsn
            else :
                raise GameLog.WriteFailed('unable to write action log')

    except (KeyError, ValueError, Game.DoesNotExist, Player.DoesNotExist, GameLog.WriteFailed) as e:
        response_data['success'] = False
        response_data['errmsg'] = type(e).__name__ + ": " + e.message

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
