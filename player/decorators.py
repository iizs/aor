from django.http import HttpResponse

import json

def requires_access_token(func):
    def inner(request, *args, **kwargs):
        http_authorization = request.META.get('HTTP_AUTHORIZATION', None)
        if http_authorization == None :
            response_data = {}
            response_data['success'] = False
            response_data['errmsg'] = 'Not authorized API access'
            return HttpResponse(json.dumps(response_data, indent=2), content_type="application/json")
        return func(request, *args, **kwargs)
    
    return inner

