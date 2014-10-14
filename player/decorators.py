from django.http import HttpResponse

import json

from player.models import Player, AccessToken

def requires_access_token(func):
    def inner(request, *args, **kwargs):
        http_authorization = request.META.get('HTTP_AUTHORIZATION', None)
        if http_authorization == None :
            response_data = {}
            response_data['success'] = False
            response_data['errmsg'] = 'Not authorized API access: access token not found'
            return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
        token_str = http_authorization.split()[1] # [0] must be Bearer

        try:
            t = AccessToken.objects.get(token=token_str)
            if t.is_expired() :
                raise AccessToken.Expired(t.expires)
        except AccessToken.DoesNotExist:
            response_data = {}
            response_data['success'] = False
            response_data['errmsg'] = 'Not authorized API access: access token not registered'
            return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
        except AccessToken.Expired:
            response_data = {}
            response_data['success'] = False
            response_data['errmsg'] = 'Not authorized API access: access token expired'
            return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")

        return func(request, *args, **kwargs)
    
    return inner

