class InvalidAccessToken(Exception):
    def __init__(self, value):
        self.value = value
    def __unicode__(self):
        return repr(self.value)

class AccessTokenExpired(Exception):
    def __init__(self, value):
        self.value = value
    def __unicode__(self):
        return repr(self.value)
