# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.db.models import Q
from django.utils.datastructures import MultiValueDictKeyError
from django.core import serializers

import random
import string
import json

from game.models import Game, GameLog
from rule.models import Edition

def _generate_hashkey(size=15):
    c = string.letters + string.digits
    return ''.join(random.sample(c, size))

@csrf_exempt
def create(request):
    response_data = {}

    try:
        hashkey = _generate_hashkey()
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

def list_games(request):
    response_data = {}
    games = Game.objects.all().filter(
        Q(status__exact=Game.WAITING) | Q(status__exact=Game.IN_PROGRESS))
    response_data['games'] = json.loads(serializers.serialize('json', games))
    response_data['success'] = True
    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")


