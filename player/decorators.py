# -*- coding: utf-8 -*-
from django.http import HttpResponse

from functools import wraps

import json

from player.models import Player, AccessToken

# func_get_user_id 는 request 를 parameter로 받는 함수
# None이면 user_id check를 수행하지 않음
def requires_access_token(func_get_user_id=None):
    def _wrapper(func_view):
        def _decorator(request, *args, **kwargs):
            return func_view(request, *args, **kwargs)
            try:
                http_authorization = request.META.get('HTTP_AUTHORIZATION', None)
                if http_authorization == None :
                    raise AccessToken.NotFound('')

                token_str = http_authorization.split()[1] # [0] must be Bearer
                t = AccessToken.objects.get(token=token_str)

                if ( func_get_user_id != None ):
                    req_user_id = func_get_user_id(request)
                    if ( req_user_id != t.player.user_id ) :
                        raise AccessToken.Invalid('user_id does not match')

                if t.is_expired() :
                    raise AccessToken.Expired(t.expires)

            except (AccessToken.DoesNotExist, AccessToken.NotFound, AccessToken.Expired, AccessToken.Invalid) as e:
                response_data = {}
                response_data['success'] = False
                response_data['errmsg'] = type(e).__name__ + ": " + e.message
                return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
            return func_view(request, *args, **kwargs)
        return _decorator
    return _wrapper

