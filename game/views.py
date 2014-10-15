# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.utils.datastructures import MultiValueDictKeyError

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
        response_data['errmsg'] = e.args

    return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
